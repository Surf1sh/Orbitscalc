"""
Orbitscalc
Copyright 2021 Hannes Diener
Licensed under the Apache License, Version 2.0
"""

from orbitscalc.antenna import Antenna
from orbitscalc.contact_utility import ContactSet, ContactGroup
from orbitscalc.general_utility import merge_sort, to_percent_max100


class GroundStation:
    def __init__(self, analyse, ground_station_data_base, antennas_data_base):
        self.__analyse = analyse
        self.__antennas = []
        self.__ground_station_data_base = ground_station_data_base
        for antenna_data_base in antennas_data_base:
            self.add_antenna(antenna_data_base)
        self.__share = None
        self.__best_contact_sequence = None

    def __repr__(self):
        return "Bodenstation %s" % self.get_name()

    def add_antenna(self, antenna_data_base):
        self.__antennas.append(Antenna(self, antenna_data_base))

    def determine_contacts(self):
        """
        lässt alle Antennen ihre Kontakte ermitteln
        :return: None
        """
        for antenne in self.__antennas:
            antenne.determine_contacts()

    def determine_data(self):
        """
        lässt alle Antennen ihre Datenmengen ermitteln
        :return: None
        """
        for antenna in self.__antennas:
            antenna.determine_data()

    def retrieve_contact_set(self):
        contact_set = ContactSet()
        for antenna in self.__antennas:
            for contact in antenna.get_contact_sequence().get_contacts():
                contact_set.add_contact_and_adjust_times(contact)
        return contact_set

    def get_antennas(self):
        return self.__antennas

    def get_name(self):
        return self.__ground_station_data_base.name

    def get_coordinates(self):
        return self.__ground_station_data_base.coordinates_for_display

    def retrieve_id(self):
        return self.__ground_station_data_base.id

    def get_analysis(self):
        return self.__analyse

    def retrieve_sufficient(self):
        return self.__share >= 1

    def get_share(self):
        return self.__share

    def get_best_contact_sequence(self):
        return self.__best_contact_sequence

    def get_data(self):
        return self.__best_contact_sequence.get_data()

    def retrieve_data_with_unit(self):
        return self.__best_contact_sequence.retrieve_data_with_unit()

    # Prozentwert maximal 100
    def retrieve_share_percentage(self):
        return to_percent_max100(self.__share)

    def set_share(self, anteil):
        self.__share = anteil

    def set_best_contact_sequence(self, contact_sequence):
        self.__best_contact_sequence = contact_sequence

    def get_contact_groups(self):
        """
        gibt Kontaktsets zur Darstellung in Cesium zurück,
        welche ein Intervall mit ununterbrochen Kontakte mit dem Satelliten repräsentieren
        :return: list
        """
        contacts = self.retrieve_contact_set().get_contacts()
        groups_of_contiguous_contacts = list()
        # Pruefen, ob es Kontakte gibt
        if contacts:
            # Kontakte nach Startzeit sortieren
            sorted_contacts = merge_sort(list(contacts), True)
            # Gruppen ueberlappender Kontakte ermitteln
            highest_end_time = sorted_contacts[0].retrieve_end_time()
            contiguous_contacts = ContactGroup()
            contiguous_contacts.add_contact_and_adjust_times(sorted_contacts[0])
            for contact in sorted_contacts[1:]:
                # pruefen, ob Kontakt nach Ende des letzten Kontaktes erst anfaengt
                if contact.retrieve_start_time() > highest_end_time:
                    # aktuelle Gruppe zusammenhaengender Kontakte abschliessen
                    groups_of_contiguous_contacts.append(
                        contiguous_contacts)
                    # mit aktuellem Kontakt neue Gruppe beginnen
                    contiguous_contacts = ContactGroup()
                contiguous_contacts.add_contact_and_adjust_times(contact)
                if contact.retrieve_end_time() > highest_end_time:
                    highest_end_time = contact.retrieve_end_time()
            # letzte Gruppe zusammenhaenger Kontakte abschliessen
            groups_of_contiguous_contacts.append(
                contiguous_contacts)
        return groups_of_contiguous_contacts
