"""
Orbitscalc
Copyright 2021 Hannes Diener
Licensed under the Apache License, Version 2.0
"""

from django.forms import DecimalField, SplitDateTimeField, SplitDateTimeWidget, Form, NumberInput, \
    ChoiceField, IntegerField, Select, Textarea, RegexField
from orbitscalc.analysis import AnalysisModes
from orbitscalc.regex_tle import REGEX_TLE, MAX_LENGTH_TLE, NUMBER_OF_COLUMNS_TLE, NUMBER_OF_ROWS_TLE
from orbitscalc.general_utility import CustomEnum


DATA_UNITS = [
    (1, "bit"),
    (8, "Byte"),
    (8e3, "kB"),
    (8e6, "MB"),
    (8e9, "GB"),
    (2 ** 10, "KiB"),
    (2 ** 20, "MiB"),
    (2 ** 30, "GiB")
]


FREQUENCY_UNITS = [
    (0, "Hz"),
    (3, "KHz"),
    (6, "MHz"),
    (9, "GHz"),
]


EIRP_UNITS = [
    ('dBW', "dBW"),
    ("W", "W")
]


class TimeInputStyles(CustomEnum):
    Whole = "gesamter Analysezeitraum"
    PerOrbit = "Orbit"
    Custom = "benutzerdefiniert"


class InputForm(Form):
    tle = RegexField(regex=REGEX_TLE, widget=Textarea(attrs={
        # Maximalanzahl Zeichen + 2 Zeichen für Zeilenumbruch und 2 Zeichen für eventuellen Wagenrücklauf
        "maxlength": MAX_LENGTH_TLE,
        "rows": NUMBER_OF_ROWS_TLE,
        "cols": NUMBER_OF_COLUMNS_TLE,
        # manuelles Ändern von Größe Verhindern
        "style": "resize:none"
    }))
    start_time = SplitDateTimeField(widget=SplitDateTimeWidget(
        date_attrs={'type': 'date'},
        time_attrs={'type': 'time'},
    ))
    end_time = SplitDateTimeField(widget=SplitDateTimeWidget(
        date_attrs={'type': 'date'},
        time_attrs={'type': 'time'},
    ))
    time_input_style = ChoiceField(
        choices=TimeInputStyles.retrieve_list_of_tuples(TimeInputStyles),
        widget=Select(attrs={'onchange': "changeTimeInputStyle();"})
    )
    data_unit = ChoiceField(choices=DATA_UNITS, widget=Select())
    data = DecimalField(widget=NumberInput(attrs={'step': "any", 'min': 0}))

    time_days = IntegerField(widget=NumberInput(attrs={'min': 0, "value": 1}))
    time_hours = IntegerField(widget=NumberInput(attrs={'min': 0, "value": 0}))
    time_minutes = DecimalField(widget=NumberInput(attrs={'step': "any", 'min': 0, "value": 0}))

    eirp_unit = ChoiceField(choices=EIRP_UNITS, widget=Select())
    eirp = DecimalField(widget=NumberInput(attrs={'step': "any"}))

    minimum_frequency = DecimalField(widget=NumberInput(attrs={'step': "any", 'min': 0}))
    maximum_frequency = DecimalField(widget=NumberInput(attrs={'step': "any", 'min': 0}))
    minimum_frequency_unit = ChoiceField(choices=FREQUENCY_UNITS, widget=Select())
    maximum_frequency_unit = ChoiceField(choices=FREQUENCY_UNITS, widget=Select())

    mode = ChoiceField(choices=AnalysisModes.retrieve_list_of_tuples(AnalysisModes), widget=Select())

    def clean(self):
        cleaned_data = super().clean()
        # Zeitraum Daten > 0 pruefen
        time_days = cleaned_data.get("time_days")
        time_hours = cleaned_data.get("time_hours")
        time_minutes = cleaned_data.get("time_minutes")
        time_input_style = cleaned_data.get("time_input_style")
        if time_days == 0 and time_hours == 0 and time_minutes == 0.0 and time_input_style == TimeInputStyles.Custom:
            error_message = "Der Zeitraum darf nicht 0 sein."
            self.add_error('time_minutes', error_message)
        
        # min <= max Frequenz pruefen
        minimum_frequency = float(cleaned_data.get("minimum_frequency"))
        maximum_frequency = float(cleaned_data.get("maximum_frequency"))
        minimum_frequency_unit = float(cleaned_data.get("minimum_frequency_unit"))
        maximum_frequency_unit = float(cleaned_data.get("maximum_frequency_unit"))
        if minimum_frequency * pow(10, minimum_frequency_unit) > maximum_frequency * pow(10, maximum_frequency_unit):
            error_message = "Minimalwert größer als Maximalwert"
            self.add_error('maximum_frequency', error_message)

        # Startzeit < Endzeit pruefen
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        if not start_time < end_time:
            error_message = "Startzeit nach Endzeit"
            self.add_error('end_time', error_message)

        # angestrebte Datenmenge = 0
        if cleaned_data.get("mode") is not AnalysisModes.JustOrbit:
            if cleaned_data.get("data") <= 0:
                error_message = "Die angestrebte Datenmenge muss größer aus 0 sein."
                self.add_error('data', error_message)
