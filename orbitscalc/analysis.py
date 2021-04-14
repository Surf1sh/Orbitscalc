"""
Orbitscalc
Copyright 2021 Hannes Diener
Licensed under the Apache License, Version 2.0
"""

from skyfield.api import EarthSatellite, load
from datetime import timedelta
from copy import copy
from orbitscalc.general_utility import data_with_unit, CustomEnum, to_percent_max100
from orbitscalc.ground_station import GroundStation
from orbitscalc.contact_utility import ContactSequence, determine_sorted_contact_groups,\
    best_contact_sequence_from_sorted_group
from orbitscalc.regex_tle import LINE_OF_ORBITS_PER_DAY_IN_TLE, START_OF_ORBITS_PER_DAY_IN_TLE, \
    END_OF_ORBITS_PER_DAY_IN_TLE, LINE_OF_NAME_IN_TLE, LINE_ONE_IN_TLE, LINE_TWO_IN_TLE


SI_DAY_IN_SECONDS = 86400
STEPS_PER_ORBIT = 100


class AnalysisModes(CustomEnum):
    GroundStations = "Bodenstationen einzeln"
    Antennas = "Antennen einzeln"
    Operators = "Betreiber einzeln"
    All = "allen Antennen zusammen"
    JustOrbit = "nur Kontakte darstellen"


def set_contacts_of_sequence_optimal(contact_sequence):
    for contact in contact_sequence.get_contacts():
        if contact.get_data() > 0:
            contact.set_optimal()


def analyse_mode_antennas(ground_stations, target_data):
    """
    analysiert jede Antenne bezüglich der maximal übertragabren Datenmenge
    :param ground_stations: list
    :param target_data: int
    :return: dict
    """
    results = list()
    for ground_station in ground_stations:
        for antenna in ground_station.get_antennas():
            contact_sequence = antenna.get_contact_sequence()
            for contact in contact_sequence.get_contacts():
                contact.determine_max_data()
                if contact.get_data() > 0:
                    contact.set_optimal()
            antenna.set_share(antenna.retrieve_data() / target_data)
        results.append(ground_station)
    return results


def analyse_mode_all(ground_stations, target_data):
    """
    analysiert jede Antenne bezüglich der maximal übertragbaren Datenmenge
    :param ground_stations: list
    :param target_data: int
    :return: dict
    """
    contacts = list()
    for ground_station in ground_stations:
        for contact in ground_station.retrieve_contact_set().get_contacts():
            contact.determine_max_data()
            contacts.append(contact)
    best_contact_sequence = determine_best_contact_sequence(contacts)
    set_contacts_of_sequence_optimal(best_contact_sequence)
    share = best_contact_sequence.retrieve_data() / target_data
    return {
        "best_contact_sequence": best_contact_sequence,
        "data_with_unit": data_with_unit(best_contact_sequence.retrieve_data()),
        "share_percentage": to_percent_max100(share),
        "sufficient": share >= 1,
    }


def analyse_mode_operators(operators_database, target_data, ground_stations_dict):
    """
    analysiert jeden übergebenen Betreiber auf maximal übertragbare Datenmenge
    :param operators_database: list
    :param target_data: int
    :param ground_stations_dict: dict
    :return: dict
    """
    results = list()
    for operator_database in operators_database:
        contacts = list()
        ground_stations_of_operator = list()
        for ground_station_data_base in operator_database.groundstation_set.all():
            if ground_station_data_base.id in ground_stations_dict:
                ground_station = ground_stations_dict[ground_station_data_base.id]
                ground_stations_of_operator.append(ground_station)
                for contact in ground_station.retrieve_contact_set().get_contacts():
                    contact.determine_max_data()
                    contacts.append(contact)
        best_contact_sequence = determine_best_contact_sequence(contacts)
        set_contacts_of_sequence_optimal(best_contact_sequence)
        share = best_contact_sequence.retrieve_data() / target_data
        results.append({
            "share_percentage": to_percent_max100(share),
            "sufficient": share >= 1,
            "data_with_unit": data_with_unit(best_contact_sequence.retrieve_data()),
            "name": operator_database.name,
            "best_contact_sequence": best_contact_sequence,
            "id": operator_database.id,
            "selected_ground_stations": ground_stations_of_operator,
        })
    return results


def analyse_mode_ground_stations(ground_stations, target_data):
    """
    analysiert jede übergebene Bodenstation auf maximal übertragbare Datenmenge
    :param ground_stations: list
    :param target_data: int
    :return: dict
    """
    results = list()
    for ground_station in ground_stations:
        # Datenmengen aller Kontakte berechnen
        contacts = ground_station.retrieve_contact_set().get_contacts()
        for contact in contacts:
            contact.determine_max_data()
        best_contact_sequence = determine_best_contact_sequence(contacts)
        set_contacts_of_sequence_optimal(best_contact_sequence)
        ground_station.set_best_contact_sequence(best_contact_sequence)
        ground_station.set_share(best_contact_sequence.retrieve_data() / target_data)
        results.append(ground_station)
    return results


def determine_best_contact_sequence(contacts):
    """
    ermittelt aus Liste von Kontakten die Kontaktfolge, mit der der die meisten Daten übertragen werden können
    :param contacts: list
    :return: contact_utility.ContactSequence
    """
    best_sequence = ContactSequence()
    if contacts:
        contact_groups = determine_sorted_contact_groups(contacts)
        for group in contact_groups:
            best_sequence.add_sequence(best_contact_sequence_from_sorted_group(group))
    return best_sequence


class Satellite:
    def __init__(self, tle, equivalent_isotropic_radiated_power, min_downlink_frequency, max_downlink_frequency):
        """
        erstellt Object mit Informationen über Satellit und Skyfield Objekt
        :param tle: Two Line Element Set as String
        :param equivalent_isotropic_radiated_power: eqivalent isotropic radiated power of Antenna in W as String
        :param min_downlink_frequency: in Hz as float
        :param max_downlink_frequency: in Hz as float
        """
        # Skyfield Objekt erstellen
        self.__skyfield = \
            EarthSatellite(tle[LINE_ONE_IN_TLE], tle[LINE_TWO_IN_TLE], tle[LINE_OF_NAME_IN_TLE], load.timescale())
        # Anzahl Satelliten Orbits pro Tag aus fester Position in der zweiten Zeile des TLE ermitteln
        self.__orbits_per_day = \
            float(tle[LINE_OF_ORBITS_PER_DAY_IN_TLE][START_OF_ORBITS_PER_DAY_IN_TLE:END_OF_ORBITS_PER_DAY_IN_TLE])
        self.__name = tle[0]
        self.__equivalent_isotropic_radiated_power = equivalent_isotropic_radiated_power
        self.__max_downlink_frequency = max_downlink_frequency
        self.__min_downlink_frequency = min_downlink_frequency

    def get_maximum_downlink_frequency(self):
        return self.__max_downlink_frequency

    def get_minimum_downlink_frequency(self):
        return self.__min_downlink_frequency

    def get_effective_isotropic_radiated_power(self):
        """
        EIRP in dBW
        :return: float
        """
        return self.__equivalent_isotropic_radiated_power

    def get_skyfield(self):
        return self.__skyfield

    def get_orbit_duration(self):
        """
        Dauer eines Orbits des Satelliten in Sekunden
        :return: float
        """
        orbit_duration = SI_DAY_IN_SECONDS / self.__orbits_per_day
        return orbit_duration

    def get_name(self):
        return self.__name


class Analysis:
    """
    repräsentiert einen Analyseprozess
    """
    def __init__(self, start_time, end_time, data_period, data_in_period, satellite):
        """
        :param start_time: datetime.datetime
        :param end_time: datetime.datetime
        :param data_period: float
        :param data_in_period: int
        :param satellite: analysis.Satellite
        """
        self.__satellite = satellite
        # startZeit und endZeit mit Datum
        self.__start_time = start_time
        self.__end_time = end_time
        # Wenn kein Zeitraum in s gegeben, ist die Dauer eines Orbits der Zeitraum
        if not data_period:
            data_period = satellite.get_orbit_duration()
        # zielDatenmenge berechnen
        self.__target_data = \
            (self.__end_time - self.__start_time).total_seconds() / data_period * data_in_period
        self.__mode = None
        self.__ground_stations = None
        self.__results = None

    def analyse(self, operators_database, antennas_data_base, mode):
        """
        führt Analyse mit gegebenen Antennen nach gegebenem Modus durch
        :param operators_database: Operator model object
        :param antennas_data_base: Aperture model object
        :param mode: AnalysisMode
        :return: None
        """
        self.__mode = mode
        # analyseBodenstationen nur mit ausgewählten Antennen erstellen
        self.__ground_stations = dict()
        for antenna_data_base in antennas_data_base:
            ground_station_data_base = antenna_data_base.groundstation
            ground_station_id = ground_station_data_base.id
            if ground_station_id in self.__ground_stations.keys():
                # Antenne zu bestehendem Objekt hinzufuegen
                self.__ground_stations[ground_station_id].add_antenna(
                    antenna_data_base)
            else:
                # analyseBodenstation Objekt erzeugen
                self.__ground_stations.update(
                    {ground_station_id: GroundStation(self, ground_station_data_base, [antenna_data_base])})
        # Analyse nach Modi
        self.__results = list()
        # zum Dartstellen in Cesium alle Kontakte ermitteln
        for ground_station in self.__ground_stations.values():
            ground_station.determine_contacts()
        if self.__mode == AnalysisModes.Antennas:
            self.__results = analyse_mode_antennas(self.__ground_stations.values(), self.__target_data)
        elif self.__mode == AnalysisModes.All:
            self.__results = analyse_mode_all(self.__ground_stations.values(), self.__target_data)
        # jeder betreiber
        elif self.__mode == AnalysisModes.Operators:
            self.__results = analyse_mode_operators(operators_database, self.__target_data, self.__ground_stations)
        # jede Bodenstation
        elif self.__mode == AnalysisModes.GroundStations:
            self.__results = analyse_mode_ground_stations(self.__ground_stations.values(), self.__target_data)
        
    def get_start_time(self):
        return self.__start_time

    def get_end_time(self):
        return self.__end_time

    def get_results(self):
        return self.__results

    def get_ground_stations(self):
        return self.__ground_stations

    def get_target_data_volume(self):
        return self.__target_data

    def retrieve_target_data_with_unit(self):
        return data_with_unit(self.__target_data)

    def get_satellite(self):
        return self.__satellite

    def calculate_satellite_positions(self):
        """
        Berechnung der Positionen des Satelliten und zugehörigen Zeitpunkten über den gesamten Analysezeitraum
        Keine Ausgabe der Positionen aus Laufzeitgründen, wenn Analysezeitraum 100 Tage übersteigt
        :return: dict
        """
        formatted_positions = list()
        # Prüfen, ob Analysezeitraum 100 Tage nicht übersteigt.
        if self.__end_time - self.__start_time <= timedelta(days=90):
            satellite = self.__satellite.get_skyfield()
            time = (self.__end_time - self.__start_time).total_seconds()
            orbit_duration = self.__satellite.get_orbit_duration()
            time_step = orbit_duration / STEPS_PER_ORBIT
            time_scale = load.timescale()
            time_and_positions = list()
            seconds_passed = 0
            ti = self.__start_time
            for i in range(STEPS_PER_ORBIT):
                skyfield_time = time_scale.from_datetime(ti)
                position = satellite.at(skyfield_time)
                time_and_positions.append((ti, position))
                ti += timedelta(seconds=time_step)
            number_of_further_positions = int(time / time_step) - STEPS_PER_ORBIT
            if number_of_further_positions < 0:
                for i in range(-number_of_further_positions):
                    del time_and_positions[-1]
            else:
                for i in range(number_of_further_positions):
                    number_of_passed_orbits = int(i / STEPS_PER_ORBIT) + 1
                    currently_in_first_orbit = time_and_positions[i % STEPS_PER_ORBIT]
                    seconds_passed = orbit_duration * number_of_passed_orbits
                    new_time = currently_in_first_orbit[0] + timedelta(seconds=seconds_passed)
                    new_position = copy(currently_in_first_orbit[1])
                    new_position.t = time_scale.from_datetime(new_time)
                    time_and_positions.append((new_time, new_position))

            for p in time_and_positions:
                position_degrees = p[1].subpoint()
                formatted_positions.append({
                    "time": p[0].isoformat(),
                    "lat": position_degrees.latitude.degrees,
                    "lon": position_degrees.longitude.degrees,
                    "alt": position_degrees.elevation.m
                })
                seconds_passed += time_step
        return formatted_positions

    def get_mode(self):
        return self.__mode
