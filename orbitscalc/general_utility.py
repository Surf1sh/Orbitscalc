"""
Orbitscalc
Copyright 2021 Hannes Diener
Licensed under the Apache License, Version 2.0
"""

import math
from enum import Enum


# Abkürzungen für Einheiten
SUFFIXES = {
    18: 'EB',
    15: 'PB',
    12: 'TB',
    9: 'GB',
    6: 'MB',
    3: 'KB',
    0: 'Byte'
}
# Grenze, welche entscheidet, ob ein Wert als Bit oder Byte angezeigt wird
BIT_BYTE_BOUNDARY = 800
BYTE_SIZE = 8
# Unterschied in den Zehnerpotenzen der Einheiten
UNIT_STEP = 3
ROUNDING_DIGITS = 3
VACUUM_LIGHT_SPEED = 299792458
BOLTZMANN_CONSTANT = 1.380640e-23
# Eb/N0 und Margin können auch je nach gewünschter Error Bit Rate angepasst werden
ENERGY_PER_BIT_TO_NOISE_POWER_SPECTRAL_DENSITY_RATIO_REQUIRED = 2.5
MARGIN_REQUIRED = 3
TIME_FORMAT_STRING = "%d. %b %Y %H:%M:%S"


def free_space_loss_calculation(distance, frequency):
    return (4 * math.pi * distance * frequency / VACUUM_LIGHT_SPEED) ** 2


def bandwidth_calculation(sender_eirp, reciever_gain_to_antenna_noise_temperature, path_loss):
    return (from_dB(ENERGY_PER_BIT_TO_NOISE_POWER_SPECTRAL_DENSITY_RATIO_REQUIRED + MARGIN_REQUIRED +
                    sender_eirp + reciever_gain_to_antenna_noise_temperature) / BOLTZMANN_CONSTANT / path_loss)


def max_data_rate_calculation(sender_eirp, reciever_gain_to_antenna_noise_temperature, distance, base_bandwidth,
                              max_frequency):
    """
    gibt mit übergebenen Parametern maximal erreichbare Datenrate zurück
    :param sender_eirp: float
    :param reciever_gain_to_antenna_noise_temperature: float
    :param distance: float
    :param base_bandwidth: float
    :param max_frequency: float
    :return: float
    """
    free_space_loss = free_space_loss_calculation(distance, max_frequency)
    # kann bei genauerer Berechnung anders sein
    path_loss = free_space_loss
    bandwidth = bandwidth_calculation(sender_eirp, reciever_gain_to_antenna_noise_temperature, path_loss)
    return int(min(base_bandwidth, bandwidth) ** (1/2))


# auf signifikaten Stellen runden
def round_significant(value, number_of_significant_digits = 0):
    """
    rundet zahl entsprechend Anzahl signifikanter Stellen
    :param value: float / int
    :param number_of_significant_digits: int
    :return: float / int
    """
    return round(value, number_of_significant_digits - 1 - int((math.log10(value))))


# Rückgabe von Datenmenge in und mit passender Einheit
def data_with_unit(data_bit):
    """
    gibt Datenmenge mit Einheit entsprechend gerundet zurück
    :param data_bit: int
    :return: str
    """
    data_bit = int(data_bit)
    if data_bit < BIT_BYTE_BOUNDARY:
        return str(data_bit) + ' Bit'
    data_byte = data_bit / BYTE_SIZE
    power_of_ten_closest_to_unit = int((math.log10(data_byte) // UNIT_STEP) * UNIT_STEP)
    suffix = SUFFIXES[power_of_ten_closest_to_unit]
    data_rounded_to_unit = round_significant(data_byte / (10 ** power_of_ten_closest_to_unit), 3)
    # zu String casten um Nullen am Ende zu umgehen
    return "%s %s" % (str(data_rounded_to_unit), suffix)


def merge(left_part, right_part, sort_by_start):
    """
    Mergen der unsortierten Hälften
    :param left_part: list
    :param right_part: list
    :param sort_by_start: Boolean
    :return: list
    """
    result = list()
    while len(left_part) > 0 and len(right_part) > 0:
        if sort_by_start:
            left_value = left_part[0].retrieve_start_time()
            right_value = right_part[0].retrieve_start_time()
        else:
            left_value = left_part[0].retrieve_end_time()
            right_value = right_part[0].retrieve_end_time()
        if left_value < right_value:
            result.append(left_part[0])
            del left_part[0]
        else:
            result.append(right_part[0])
            del right_part[0]
    if len(left_part) == 0:
        result += right_part
    else:
        result += left_part
    return result


def merge_sort(unordered_list, sort_by_start):
    """
    sortiert liste nach Zeit von Index 0 bis -1 steigend
    :param unordered_list: list
    :param sort_by_start: Boolean
    :return: list
    """
    if len(unordered_list) <= 1:
        return unordered_list
    # Mittelpunkt finden und Liste an Mittelpunkt aufteilen
    middle = math.floor(len(unordered_list) / 2)
    right_list = unordered_list[middle:]
    left_list = unordered_list[:middle]
    right_list = merge_sort(right_list, sort_by_start)
    left_list = merge_sort(left_list, sort_by_start)

    return list(merge(left_list, right_list, sort_by_start))


def to_dB(value):
    """
    Wert in logarithmische Form umrechnen
    :param value: float
    :return: float
    """
    return 10 * math.log(value, 10)


def from_dB(value):
    """
    Wert aus logarithmischer Form umrechnen
    :param value: float
    :return: float
    """
    return math.pow(10, value / 10.0)


def to_percent_max100(value):
    """
    gibt Anteil in Prozent zurück; max 100
    :param value: float
    :return: float
    """
    return min(value * 100, 100)


def vector_length(vector_as_list):
    """
    gibt Betrag eines Vektors zurück
    :param vector_as_list: list
    :return: float
    """
    length = 0
    for i in vector_as_list:
        length += i ** 2
    length **= 1 / 2
    return length


def average_time(time1, time2):
    """
    gibt Zeitpunkt zurück, der zwischen übergebenen Zeitpunkten liegt
    :param time1: datetime.datetime
    :param time2: datetime.datetime
    :return: datetime.datetime
    """
    time_difference = time1 - time2
    return time2 + time_difference / 2


def format_time(time):
    """
    gibt Zeitpunkt formatiert als String zurück
    :param time: datetime.datetime
    :return: string
    """
    return time.strftime(TIME_FORMAT_STRING)


def enum_to_list_of_tuples(enum):
    """
    gibt liste mit Attributen von Enum als Tupel zurück
    :param enum: enum.Enum
    :return: list()
    """
    return [(attribute.name, attribute.value) for attribute in enum]


class CustomEnum(Enum):
    """
    Basisklasse für individualisierte Enumerations
    """
    def retrieve_list_of_tuples(self):
        return enum_to_list_of_tuples(self)
