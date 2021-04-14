"""
Orbitscalc
Copyright 2021 Hannes Diener
Licensed under the Apache License, Version 2.0
"""

class ContactRetrieveTimeError(Exception):
    """
    Zugriff auf Zeitpunkt von relativer Position eines Kontaktes
    """
    def __init__(self):
        super().__init__("This contact has no relative positions.")


class AddContactChronologicalError(Exception):
    """
    anzuhängender Kontakt zeitlich vor letztem Kontakt
    """
    def __init__(self):
        super().__init__("Contact to be attached starts before last contact ends.")


class ContactNoDataError(Exception):
    """
    Kontakt wurde nicht berechnet, weshalb keine Datenmenge vorliegt
    """
    def __init__(self):
        super().__init__("Data of Contact was not calculated.")
