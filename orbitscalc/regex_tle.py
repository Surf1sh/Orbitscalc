"""
Orbitscalc
Copyright 2021 Hannes Diener
Licensed under the Apache License, Version 2.0
"""

# Regex Ausdruck laut NASA - geprüft mit NORAD Elementen von Celestrak
REGEX_TLE = str()
# Satellitenname
REGEX_TLE += ".{0,24} {0,45}\r{0,1}\n"
# erste Zeile
REGEX_TLE += "1 "  # Zeilennummer
REGEX_TLE += "[0-9]{5}"  # Katalognummer
REGEX_TLE += "[USC] "  # Klassifizierung
REGEX_TLE += "[0-9]{2}"  # international designator - die letzten beiden Stellen vom Startjahr
REGEX_TLE += "[0-9]{3}"  # international designator - nummer des Starts
REGEX_TLE += "[ A-Z]{3} "  # international designator - Teil der Fracht
REGEX_TLE += "[0-9]{2}"  # die letzten beiden Stellen vom Epoch-Jahr
REGEX_TLE += "[0-9]{3}[.][0-9]{8} "  # Epoch - nummer des Tages
REGEX_TLE += "[ -][.][0-9]{8} "  # Ballistischer Koeffizient
REGEX_TLE += "[ 0-9]{5}[0-9]-[0-9] "  # Second Derivate of Mean Motion
REGEX_TLE += "[ -][0-9]{5}-[0-9] "  # Reibungsterm
REGEX_TLE += ". "  # Ephemeridentyp
REGEX_TLE += "[ 0-9]{3}[0-9]"  # TLE-Nummer
REGEX_TLE += "[0-9]\r{0,1}\n"  # Pruefsumme Zeile 1
# zweite Zeile
REGEX_TLE += "2 "  # Zeilennummer
REGEX_TLE += "[0-9]{5} "  # Katalognummer
REGEX_TLE += "[ 0-9]{3}[.][0-9]{4} "  # Inclination
REGEX_TLE += "[ 0-9]{3}[.][0-9]{4} "  # Right Ascension of the Ascending Node
REGEX_TLE += "[0-9]{7} "  # Exzentrizitaet
REGEX_TLE += "[ 0-9]{3}[.][0-9]{4} "  # Argument of Perigee
REGEX_TLE += "[ 0-9]{3}[.][0-9]{4} "  # Mean Anomaly
REGEX_TLE += "[ 0-9]{2}[.][0-9]{8}"  # Mean Motion
REGEX_TLE += "[ 0-9]{5}"  # Revolution number at epoch
REGEX_TLE += "[0-9]"  # Prüfsumme Zeile 2

NUMBER_OF_ROWS_TLE = 2
NUMBER_OF_COLUMNS_TLE = 69
MAX_LENGTH_TLE = 24 + NUMBER_OF_COLUMNS_TLE * NUMBER_OF_ROWS_TLE + 4
LINE_OF_ORBITS_PER_DAY_IN_TLE = 2
START_OF_ORBITS_PER_DAY_IN_TLE = 52
END_OF_ORBITS_PER_DAY_IN_TLE = 63
LINE_OF_NAME_IN_TLE = 0
LINE_ONE_IN_TLE = 1
LINE_TWO_IN_TLE = 2
