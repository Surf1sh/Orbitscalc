"""
Orbitscalc
Copyright 2021 Hannes Diener
Licensed under the Apache License, Version 2.0
"""

from orbitscalc.general_utility import data_with_unit, average_time, format_time, merge_sort
from orbitscalc.models import Link
from orbitscalc.errors import ContactRetrieveTimeError, AddContactChronologicalError
from enum import Enum
from skyfield.api import utc
from orbitscalc.general_utility import vector_length, max_data_rate_calculation


SIMPLE_TIME_FORMAT = "%H:%M"


class OverlappingContactsDesignations(Enum):
    IndexOfNextContact = "next index"
    OverlappingContacts = "overlapping contacts"


class RelativePosition:
    """
    RelativePosition repräsentiert alle Lagemerkmale des Satelliten relativ zur Antenne zu einem Zeitpunkt
    """
    def __init__(self, time_skyfield, antenna):
        satellite_skyfield = antenna.retrieve_analysis().get_satellite().get_skyfield()
        # geozentrische Position
        self.__satellite_position_skyfield = satellite_skyfield.at(time_skyfield)
        self.__relative_position_skyfield = (satellite_skyfield - antenna.get_skyfield()).at(time_skyfield)
        self.__time_skyfield = time_skyfield
        self.__data_rate = None
        self.__antenna = antenna

    def calculate_data_rate(self, satellite, link):
        """
        gibt maximal erreichbare Datenrate der relativen Position zurück
        :param satellite: analysis.Satellite
        :param link: models.Link
        :return: float
        """
        minimum_frequency = max(link.frequency_min, satellite.get_minimum_downlink_frequency())
        maximum_frequency = min(link.frequency_max, satellite.get_maximum_downlink_frequency())
        base_bandwidth = maximum_frequency - minimum_frequency
        if base_bandwidth > 0:
            self.__data_rate = max_data_rate_calculation(
                satellite.get_effective_isotropic_radiated_power(),
                self.__antenna.retrieve_gain_to_noise_temperature(),
                self.retrieve_distance(), base_bandwidth, maximum_frequency
            )
        else:
            self.__data_rate = 0

    def retrieve_time(self):
        """
        gibt Zeitpunkt als datetime Objekt mit Zeitzone UTC zurück
        :return: datetime
        """
        return self.__time_skyfield.astimezone(utc)

    def retrieve_distance(self):
        """
        gibt Abstand zwischen Satellit und Antenne in Metern zurück
        :return: float
        """
        return vector_length(self.__relative_position_skyfield.position.m)

    def retrieve_latitude(self):
        """
        gibt geografische Breite des Satelliten in Grad zurück
        :return: float
        """
        return self.__satellite_position_skyfield.subpoint().latitude.radians

    def retrieve_longitude(self):
        """
        gibt geografische Länge des Satelliten in Grad zurück
        :return: float
        """
        return self.__satellite_position_skyfield.subpoint().longitude.radians

    def get_height_above_sea_level(self):
        """
        gibt Höhe des Satelliten über dem Meeresspiegel in Metern zurück
        :return: float
        """
        return self.__satellite_position_skyfield.subpoint().elevation.m

    def get_data_rate(self):
        return self.__data_rate

    def get_time_skyfield(self):
        return self.__time_skyfield

    # setter
    def set_data_rate(self, data_rate):
        self.__data_rate = data_rate


class Contact:
    """
    ununterbrochene Sichtverbindung zwischen Antenne und Satellit
    enthält mehrere relative Positionen
    """
    def __init__(self, antenna):
        self.__antenna = antenna
        self.__relative_positions = []
        self.__is_optimal = False
        self.__data_calculated = False
        self.__data = None
        self.__best_link = None

    # Darstellung beim Ausgeben in Konsole
    def __repr__(self):
        return '%s bis %s: %s' % (
            self.retrieve_start_time().strftime(SIMPLE_TIME_FORMAT),
            self.retrieve_end_time().strftime(SIMPLE_TIME_FORMAT),
            data_with_unit(self.get_data())
        )

    # zum Zeitpunkt Position berechnen und zum Kontakt hinzufuegen
    def add_relative_position_by_skyfield_time(self, skyfield_time):
        self.__relative_positions.append(RelativePosition(skyfield_time, self.__antenna))

    def determine_max_data(self):
        """
        Datenmenge berechnen, welche in diesem Kontakt übertragen werden kann
        :return: int
        """
        satellite = self.__antenna.retrieve_analysis().get_satellite()
        links = Link.objects.filter(aperture_id=self.__antenna.retrieve_id())
        best_link = None
        max_data = 0
        # fuer jeden Link Datenmenge ermitteln
        for link in links:
            if link.is_downlink:
                # pruefen, ob Datenübertragung mit Frequenzbereichen möglich
                if link.frequency_min < satellite.get_maximum_downlink_frequency() and \
                        link.frequency_max > satellite.get_minimum_downlink_frequency():
                    self.determine_data_for_link(link)
                    if self.__data > max_data:
                        best_link = link
                        max_data = self.__data
        if best_link:
            self.__best_link = best_link
        self.__data = max_data
        self.__data_calculated = True

    def determine_data_rates_for_link(self, link):
        """
        ermittelt für jede relative Position die Datenübertragungsraten und gibt sie in chronologischer Liste zurück
        :param link: Link model object
        :return: list
        """
        data_rates = list()
        for relative_position in self.__relative_positions:
            relative_position.calculate_data_rate(self.__antenna.retrieve_analysis().get_satellite(), link)
            data_rates.append(relative_position.get_data_rate())
        return data_rates

    def determine_data_for_link(self, link):
        """
        ermittelt bei Kontakt mit übergebenem Link mögliche Datenübertragungsmenge
        und speichert diese im Attribut __data
        :param link: Link model object
        :return: None
        """
        self.__data = 0
        # für jede Relative Position Datenübertragungsraten ermitteln
        data_rates = self.determine_data_rates_for_link(link)
        # Für jeden Zeitpunkt mit Datenübertragungsrate übertragbare Datenmenge berechnen
        for i, (data_rate, relative_position) in enumerate(zip(data_rates, self.__relative_positions)):
            time_of_this_relative_position = relative_position.retrieve_time()
            # Prüfen, ob nicht erster Zeitpunkt
            if i != 0:
                time_of_previous = self.__relative_positions[i - 1].retrieve_time()
                # Mittelpunkt zwischen jetzigem und vorherigem Kontakt als Start von Intervall
                start_time = average_time(time_of_this_relative_position, time_of_previous)
            else:
                # als Startzeitpunkt festlegen, wenn erste relative Position in Kontakt
                start_time = time_of_this_relative_position
            # Prüfen, ob nicht letzter Zeitpunkt
            if i != len(data_rates) - 1:
                time_of_next = self.__relative_positions[i + 1].retrieve_time()
                # Mittelpunkt zwischen jetzigem und nachfolgendem Kontakt als Ende von Intervall
                end_time = average_time(time_of_this_relative_position, time_of_next)
            else:
                # als Endzeitpunkt festlegen, wenn letzte Relative Position von Kontakt
                end_time = time_of_this_relative_position
            # Datenmenge als Produkt von Dauer des Intervalls und Datenrate ermitteln
            duration = (end_time - start_time).total_seconds()
            self.__data += data_rate * duration
        self.__data_calculated = True

    # getter
    def get_link(self):
        return self.__best_link

    def get_data(self):
        return self.__data

    def retrieve_data_with_unit(self):
        if self.__data or self.__data == 0:
            return data_with_unit(self.__data)
        else:
            return None

    def get_time_of_relative_position(self, index):
        try:
            return self.__relative_positions[index].retrieve_time()
        except ContactRetrieveTimeError:
            pass

    def retrieve_start_time(self):
        return self.get_time_of_relative_position(0)

    def retrieve_end_time(self):
        return self.get_time_of_relative_position(-1)

    def get_optimal(self):
        return self.__is_optimal

    def set_optimal(self):
        self.__is_optimal = True

    def generate_output_string(self):
        """
        gibt String mit wichtigen Informationen über Kontakt zurück
        :return: string
        """
        start = format_time(self.retrieve_start_time())
        end = format_time(self.retrieve_end_time())
        data = self.retrieve_data_with_unit()
        if not data:
            data = "keine Datenmenge berechnet"
        antenna = self.__antenna.get_name()
        return "Kontakt vom %s bis %s mit Antenne %s:  %s" % (start, end, antenna, data)

    # Ausgabe mit Name der Bodenstation
    def generate_output_string_with_ground_station_name(self):
        """
        gibt String mit wichtigen Informationen inkl. Bodenstationsname über Kontakt zurück
        :return: string
        """
        start = format_time(self.retrieve_start_time())
        end = format_time(self.retrieve_end_time())
        data = self.retrieve_data_with_unit()
        if not data:
            data = "keine Datenmenge berechnet"
        antenna_name = self.__antenna.get_name()
        ground_station_name = self.__antenna.get_ground_station().get_name()
        return "Kontakt vom %s bis %s mit %s von %s:  %s" % (start, end, antenna_name, ground_station_name, data)


class ContactSet:
    """
    repräsentiert beliebige Menge von Kontakten
    """
    def __init__(self):
        self.__start_time = 12345
        self.__end_time = None
        self.__contacts = set()

    def __repr__(self):
        return repr(self.__contacts)

    def add_contact_and_adjust_times(self, contact):
        contact_start_time = contact.retrieve_start_time()
        contact_end_time = contact.retrieve_end_time()
        # falls noch keine Kontakte Vorhanden, Start- und Endzeitpunkt dieses Kontaktes übernehmen
        if not self.__contacts:
            self.__start_time = contact_start_time
            self.__end_time = contact_end_time
            self.__contacts.add(contact)
        else:
            self.__contacts.add(contact)
            # Pruefen, ob dieser Kontakt eher beginnt als erster Kontakt
            if contact.retrieve_start_time() < self.__start_time:
                self.__start_time = contact_start_time
            # Pruefen, ob dieser Kontakt spaeter endet als letzter Kontakt
            elif contact_end_time > self.__end_time:
                self.__end_time = contact_end_time

    def get_contacts(self):
        return self.__contacts

    def get_start_time(self):
        return self.__start_time

    def get_end_time(self):
        return self.__end_time


class ContactInterval:
    """
    repräsentiert eine Zeitspanne mit der Information, ob optimale Kontakte stattfinden oder nicht
    """
    def __init__(self, start_time, end_time, is_optimal):
        self.__start_time = start_time
        self.__end_time = end_time
        self.__is_optimal = is_optimal

    def get_start_time(self):
        return self.__start_time

    def get_end_time(self):
        return self.__end_time

    def get_optimal(self):
        return self.__is_optimal

    def set_end_time(self, end_time):
        self.__end_time = end_time

    def set_start_time(self, start_time):
        self.__start_time = start_time

    def __repr__(self):
        return "%s bis %s: %r" % (
            self.__start_time.strftime(SIMPLE_TIME_FORMAT),
            self.__end_time.strftime(SIMPLE_TIME_FORMAT),
            self.__is_optimal
        )


class ContactGroup(ContactSet):
    """
    repräsentiert Menge von Zusammenhängenden Kontakten (ohne Lücken)
    """
    def __init__(self):
        super().__init__()
        self.__optimal_intervals = list()

    def add_contact_and_adjust_times(self, contact):
        super().add_contact_and_adjust_times(contact)
        start_time_contact = contact.retrieve_start_time()
        end_time_contact = contact.retrieve_end_time()
        if contact.get_optimal():
            # fuer jedes Intervall prüfen, ob Kontakt mit Intervall überlappt
            overlap = False
            for interval in self.__optimal_intervals:
                start_time_interval = interval.get_start_time()
                end_time_interval = interval.get_end_time()
                contact_starts_before_interval_ends = start_time_contact < end_time_interval
                contact_starts_after_interval_starts = start_time_contact > start_time_interval
                contact_ends_after_interval_ends = end_time_contact > end_time_interval
                contact_ends_before_interval_ends = end_time_contact < end_time_interval
                contact_ends_after_interval_starts = end_time_contact > start_time_interval
                contact_starts_before_interval_starts = start_time_contact < start_time_interval
                if contact_starts_before_interval_ends and contact_starts_after_interval_starts \
                        and contact_ends_after_interval_ends:
                    interval.set_end_time(end_time_contact)
                    overlap = True
                elif contact_ends_before_interval_ends and contact_ends_after_interval_starts \
                        and contact_starts_before_interval_starts:
                    interval.set_start_time(start_time_contact)
                    overlap = True
            if not overlap:
                interval = ContactInterval(start_time_contact, end_time_contact, True)
                # pruefen ob bereits Intervalle in Liste
                if not self.__optimal_intervals:
                    self.__optimal_intervals.append(interval)
                # neues Intervall an entsprechender Stelle in Liste einfügen
                for i in range(len(self.__optimal_intervals)):
                    if self.__optimal_intervals[i].get_end_time() < start_time_contact:
                        self.__optimal_intervals.insert(i + 1, interval)
                        break

    def determine_intervals(self):
        """
        gibt chronologische Liste von Intervallen mit Information, ob optimale Kontakt stattfindet, zurück
        :return: list
        """
        all_intervals = list()
        last_time = super().get_start_time()
        if not self.__optimal_intervals:
            all_intervals.append(ContactInterval(super().get_start_time(), super().get_end_time(), False))
        # intervalle zwischen den Intervallen mit optimalem Kontakt erstellen
        else:
            for optimal_interval in self.__optimal_intervals:
                if optimal_interval.get_start_time() > last_time:
                    all_intervals.append(ContactInterval(last_time, optimal_interval.get_start_time(), False))
                all_intervals.append(optimal_interval)
                last_time = all_intervals[-1].get_end_time()
            if self.__optimal_intervals:
                if last_time is not super().get_end_time():
                    last_interval = ContactInterval(last_time, super().get_end_time(), False)
                    all_intervals.append(last_interval)
        return all_intervals


class ContactSequence:
    """
    repräsentiert chronologische Abfolge von Kontakten
    """
    def __init__(self):
        self.__contacts = list()

    # Kontakt ans chronologische Ende anhaengen
    def add_contact(self, contact):
        if not self.__contacts:
            self.__contacts = [contact]
        # pruefen, ob Kontakt chronologisch später
        elif contact.retrieve_start_time() > self.__contacts[-1].retrieve_end_time():
            self.__contacts.append(contact)
        else:
            raise AddContactChronologicalError

    def add_sequence(self, contact_sequence):
        if contact_sequence:
            if not self.__contacts:
                self.__contacts = contact_sequence.get_contacts()
            elif self.retrieve_end_time() < contact_sequence.retrieve_start_time():
                self.__contacts += contact_sequence.get_contacts()
            else:
                raise AddContactChronologicalError

    def determine_data(self):
        # für jeden Kontakt besten link ermitteln
        for contact in self.__contacts:
            contact.determine_max_data()

    def retrieve_data(self):
        data = 0
        for contact in self.__contacts:
            data_contact = contact.get_data()
            if data_contact:
                data += data_contact
        return data

    def retrieve_data_with_unit(self):
        return data_with_unit(self.retrieve_data())

    def get_contacts(self):
        return self.__contacts

    def retrieve_start_time(self):
        try:
            return self.__contacts[0].retrieve_start_time()
        except ContactRetrieveTimeError:
            pass

    def retrieve_end_time(self):
        try:
            return self.__contacts[-1].retrieve_end_time()
        except ContactRetrieveTimeError:
            pass


def determine_overlapping_contacts(start_index, sorted_contacts):
    """
    Gibt ein Dictionary mit einer chronologischen Liste
    der mit dem Kontakt mit dem Startindex überlappenden Kontakte zurück.
    :param start_index: int
    :param sorted_contacts: list of contacts sorted by start time
    :return: dict
    """
    end_time = sorted_contacts[start_index].retrieve_end_time()
    start_time = sorted_contacts[start_index]
    overlapping_contacts = [start_time]
    i = 1
    if start_index + i < len(sorted_contacts):
        at_the_end_of_sorted_contacts = False
        # alle Kontakte ermitteln, welche mit dem aktuellen Kontakt ueberlappen und mit oder nach ihm starten
        possibly_overlapping_contact = sorted_contacts[start_index + i]
        while possibly_overlapping_contact.retrieve_start_time() <= end_time and not at_the_end_of_sorted_contacts:
            overlapping_contacts.append(
                sorted_contacts[start_index + i])
            i += 1
            if start_index + i >= len(sorted_contacts):
                at_the_end_of_sorted_contacts = True
            else:
                possibly_overlapping_contact = sorted_contacts[start_index + i]
    return {
        OverlappingContactsDesignations.OverlappingContacts: overlapping_contacts,
        OverlappingContactsDesignations.IndexOfNextContact: start_index + i
    }


def smallest_overlapping_contact_group(index_of_start_contact, sorted_contacts):
    """
    gibt mit Kontakt überlappende Kontakte zurück, welcher mit Startkontakt überlappt und als erster endet
    :param index_of_start_contact: int
    :param sorted_contacts: list of contacts sorted by start time
    :return: list of contacts sorted by start time
    """
    # mit startKontakt ueberlappende Kontakte ermitteln
    overlapping_contacts = determine_overlapping_contacts(
        index_of_start_contact, sorted_contacts)[OverlappingContactsDesignations.OverlappingContacts]
    # ueberlappende Kontakte nach Endzeit sortieren
    overlapping_contacts_sorted_by_end_time = merge_sort(overlapping_contacts, False)
    # Kontakt mit geringster Endzeit als neuen Startkontakt ermitteln
    index_of_first_ending_contact = sorted_contacts.index(overlapping_contacts_sorted_by_end_time[0])
    # ueberlappende Kontakte neu ermitteln
    result = determine_overlapping_contacts(
        index_of_first_ending_contact, sorted_contacts)
    overlapping_contacts = result[OverlappingContactsDesignations.OverlappingContacts]
    # Kontakte vor Kontakt mit geringster Endzeit wieder zu überlappenden Kontakten hinzufügen
    for i in range(index_of_first_ending_contact - index_of_start_contact):
        overlapping_contacts.insert(i, sorted_contacts[index_of_start_contact + i])
    return result


def determine_next_contact(current_contact, contact_group):
    """
    gibt den dem aktuellen Kontakt nachfolgenden Kontakt aus der nach Startzeit sortierten Kontaktgruppe zurück
    :param current_contact: Contact
    :param contact_group: list
    :return: Contact
    """
    for contact in contact_group[contact_group.index(current_contact):]:
        if contact.retrieve_start_time() > contact.retrieve_end_time():
            return contact


def determine_contacts_sorted_by_following_contact(contacts, contact_group):
    """
    gibt die Kontakte nach nachfolgendem Kontakt gruppiert zurück
    :param contacts: list
    :param contact_group: list
    :return: list
    """
    contacts_sorted_by_following_contact = list()
    current_contacts_with_same_next_contact = list()
    following_contact_of_previous = None
    for contact in merge_sort(contacts, True):
        following_contact = determine_next_contact(contact, contact_group)
        if following_contact is following_contact_of_previous:
            current_contacts_with_same_next_contact.append(contact)
        else:
            contacts_sorted_by_following_contact.append(
                (current_contacts_with_same_next_contact, following_contact_of_previous)
            )
            current_contacts_with_same_next_contact = [contact]
        following_contact_of_previous = following_contact
    contacts_sorted_by_following_contact.append({
        "contacts": current_contacts_with_same_next_contact,
        "following_contact": following_contact_of_previous
    })
    return contacts_sorted_by_following_contact


def best_contact_sequence_from_sorted_group(contact_group):
    """
    ermittelt Kontaktfolge mit höchster Übertragener Datenmenge aus einer Kontaktgruppe
    :param contact_group: list
    :return: ContactSequence
    """
    smallest_group_of_mutually_exclusive_contacts =\
        smallest_overlapping_contact_group(0, contact_group)[OverlappingContactsDesignations.OverlappingContacts]
    contacts_sorted_by_following_contact = \
        determine_contacts_sorted_by_following_contact(smallest_group_of_mutually_exclusive_contacts, contact_group)
    sequences = list()
    for contacts_with_following in contacts_sorted_by_following_contact:
        current_best_sequence = ContactSequence()
        best_contact = determine_best_contact(contacts_with_following["contacts"])
        if best_contact:
            current_best_sequence.add_contact(best_contact)
        following_contact = contacts_with_following["following_contact"]
        if following_contact:
            contacts_from_following_contact = \
                contact_group[contact_group.index(following_contact):]
            best_following_sequence = best_contact_sequence_from_sorted_group(contacts_from_following_contact)
            current_best_sequence.add_sequence(best_following_sequence)
        sequences.append(current_best_sequence)
    return determine_best_contact_sequence(sequences)


def determine_best_contact_sequence(contact_sequences):
    """
    ermittelt aus einer Menge von Kontaktfolgen die Kontaktfolge mit den meisten übertragenen Daten
    :param contact_sequences: list
    :return: ContactSequence
    """
    best_sequence = None
    best_data = 0
    for sequence in contact_sequences:
        if sequence.retrieve_data() > best_data:
            best_sequence = sequence
            best_data = sequence.retrieve_data()
    return best_sequence


def determine_best_contact(contacts):
    """
    gibt Kontakt mit höchster übertragener Datenmenge aus übergebener Menge zurück
    :param contacts: list / set / ...
    :return: Contact
    """
    current_best_data = 0
    best_contact = None
    for contact in contacts:
        current_data = contact.get_data()
        if current_data > current_best_data:
            current_best_data = current_data
            best_contact = contact
    return best_contact


def determine_sorted_contact_groups(all_contacts):
    """
    gibt eine chronologische Liste von Gruppen von Kontakten zurück, zwischen denen keine weiteren Kontakte stattfinden
    :param all_contacts: list
    :return: list
    """
    contact_groups = list()
    if all_contacts:
        sorted_contacts = merge_sort(list(all_contacts), True)
        current_last_end_time = sorted_contacts[0].retrieve_end_time()
        current_contact_group = list()
        for contact in sorted_contacts:
            # Kontakt außerhalb aktueller Kontaktgruppe
            if contact.retrieve_start_time() > current_last_end_time:
                contact_groups.append(current_contact_group)
                current_contact_group = [contact]
                current_last_end_time = contact.retrieve_end_time()
            # Kontakt noch innerhalb aktueller Kontaktgruppe
            else:
                current_contact_group.append(contact)
                # Falls Kontakt in Gruppe als letztes endet, aktuell spätesten Endzeitpunkt anpassen
                if contact.retrieve_end_time() > current_last_end_time:
                    current_last_end_time = contact.retrieve_end_time()
        contact_groups.append(current_contact_group)
    return contact_groups
