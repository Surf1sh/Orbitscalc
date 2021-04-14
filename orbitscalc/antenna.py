from skyfield.api import Topos, load
from orbitscalc.contact_utility import Contact, ContactSequence
from orbitscalc.general_utility import data_with_unit, to_percent_max100
from enum import IntEnum


MINIMUM_ALTITUDE_OVER_HORIZON_FOR_CONTACT_DEGREES = 5.0


class SkyfieldEventTypes(IntEnum):
    Rise = 0
    Culminate = 1
    Set = 2


def determine_first_contact_incomplete(start_time_skyfield, events, times, antenna):
    """
    gibt ersten Kontakt vervollständigt und Anzahl der an events in unvollständiger Folge zurück
    :param start_time_skyfield: skyfield time
    :param events: array of int
    :param times: array of skyfield times
    :param antenna: Antenna object
    :return: Contact object, int
    """
    incomplete_event_sequence_beginning = list()
    # ersten Kontakt bei Anfang des Analysezeitraumes beginnen lassen
    incomplete_event_sequence_beginning.append(start_time_skyfield)
    # falls erstes Event Höchststand, dieses zu anfang hinzufügen
    if events[0] == int(SkyfieldEventTypes.Culminate):
        incomplete_event_sequence_beginning.append(times[0])
    # falls erstes Event in Liste jetzt Untergehen, dieses zu Anfang hinzufügen
    if len(events) >= 2:
        if events[len(incomplete_event_sequence_beginning)] == int(SkyfieldEventTypes.Set):
            incomplete_event_sequence_beginning.append(times[len(incomplete_event_sequence_beginning)])
    # falls erster Kontakt unvollständig, diesen erstellen
    incomplete_contact_beginning = Contact(antenna)
    for time_skyfield in incomplete_event_sequence_beginning:
        incomplete_contact_beginning.add_relative_position_by_skyfield_time(time_skyfield)
    return incomplete_contact_beginning, len(incomplete_event_sequence_beginning)


def determine_last_contact_incomplete(end_time_skyfield, events, times, antenna):
    """
    gibt letzten Kontakt vervollständigt und Anzahl der an events in unvollständiger Folge zurück
    :param end_time_skyfield: skyfield time
    :param events: array of int
    :param times: array of skyfield times
    :param antenna: Antenna object
    :return: Contact object, int
    """
    incomplete_event_sequence_end = list()
    # letztes Kontakt bei Ende des Analysezeitraums enden lassen
    incomplete_event_sequence_end.append(end_time_skyfield)
    # falls letztes Event Höchststand, dieses zu ende hinzufügen
    if events[-1] == int(SkyfieldEventTypes.Culminate):
        incomplete_event_sequence_end.append(times[-1])
    # falls letztes Event in Liste Aufgehen, dieses zu Ende hinzufügen
    if events[-1 - len(incomplete_event_sequence_end)] == int(SkyfieldEventTypes.Rise):
        incomplete_event_sequence_end.append(times[-1 - len(incomplete_event_sequence_end)])
    # Invertieren der Liste für chronologisch korrekte Reihenfolge
    incomplete_event_sequence_end.reverse()
    incomplete_contact_end = Contact(antenna)
    for time in incomplete_event_sequence_end:
        incomplete_contact_end.add_relative_position_by_skyfield_time(time)
    return incomplete_contact_end, len(incomplete_event_sequence_end)


# AnalyseAntenne repraensentiert eine Antenne und alle ihre Kontakte mit dem Satelliten
class Antenna:
    """
    repräsentiert Antenne mit ihren Kontakten
    """
    def __init__(self, ground_station, antenna):
        self.__ground_station = ground_station
        self.__name = antenna.name
        # Antenne als topozentrische Position auf der Erde von Skyfield
        self.__antenna_skyfield = Topos(
            latitude_degrees=float(antenna.latitude),
            longitude_degrees=float(antenna.longitude),
            elevation_m=float(antenna.altitude)
        )
        self.__antenna_data_base = antenna
        self.__contact_sequence = None
        # Verhältnis der übertragbaren zur insgesamt angestrebten Datenmenge bei Modus Antennen
        self.__share = None
        self.__sufficient = None

    def determine_contacts(self):
        # nicht wundern, Skyfield möchte das so
        timescale = load.timescale()
        start_time_skyfield = timescale.from_datetime(self.retrieve_analysis().get_start_time())
        end_time_skyfield = timescale.from_datetime(self.retrieve_analysis().get_end_time())
        # alle Kontakte mit Satelliten im Analysezeitraum ermitteln
        times, events = self.retrieve_analysis().get_satellite().get_skyfield().find_events(
            self.__antenna_skyfield,
            start_time_skyfield,
            end_time_skyfield,
            # Mindesthöhe über Horizont bei Kontakt
            altitude_degrees=MINIMUM_ALTITUDE_OVER_HORIZON_FOR_CONTACT_DEGREES
        )

        self.__contact_sequence = ContactSequence()
        # Falls erster Kontakt unvollständig ist
        number_of_events_beginning = 0
        if len(events) >= 1 and events[0] != int(SkyfieldEventTypes.Rise):
            first_contact, number_of_events_beginning = \
                determine_first_contact_incomplete(start_time_skyfield, events, times, self)
            self.__contact_sequence.add_contact(first_contact)
        # Falls letzter Kontakt unvollständig ist
        last_contact = False
        number_of_events_end = 0
        if len(events) > 1 and events[-1] != int(SkyfieldEventTypes.Set):
            last_contact, number_of_events_end = \
                determine_last_contact_incomplete(end_time_skyfield, events, times, self)
        # vollständige Kontakte erstellen
        number_of_complete_contacts = \
            len(events) - (number_of_events_beginning + number_of_events_end)
        for number_of_complete_contact in range(number_of_complete_contacts // len(SkyfieldEventTypes)):
            contact = Contact(self)
            for number_of_event in range(len(SkyfieldEventTypes)):
                contact.add_relative_position_by_skyfield_time(
                    times[number_of_events_beginning
                          + len(SkyfieldEventTypes) * number_of_complete_contact + number_of_event])
            self.__contact_sequence.add_contact(contact)
        # falls erster Kontakt unvollständig, diesen erstellen
        if last_contact:
            self.__contact_sequence.add_contact(last_contact)

    def determine_data(self):
        self.__contact_sequence.determine_data()

    def get_contact_sequence(self):
        return self.__contact_sequence

    def retrieve_gain_to_noise_temperature(self):
        return float(self.__antenna_data_base.gt_dbw_k)

    def retrieve_id(self):
        return self.__antenna_data_base.id

    def get_skyfield(self):
        return self.__antenna_skyfield

    def get_ground_station(self):
        return self.__ground_station

    def get_name(self):
        return self.__name

    def retrieve_analysis(self):
        return self.__ground_station.get_analysis()

    def retrieve_data(self):
        return self.__contact_sequence.retrieve_data()

    def retrieve_data_with_unit(self):
        return data_with_unit(self.retrieve_data())

    def determine_sufficient(self):
        return self.__share >= 1

    def get_share(self):
        return self.__share

    # Prozentwert maximal 100
    def retrieve_share_percentage(self):
        return to_percent_max100(self.__share)

    def set_share(self, share):
        self.__share = share
