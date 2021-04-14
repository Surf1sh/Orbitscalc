"""
Orbitscalc
Copyright 2021 Hannes Diener
Licensed under the Apache License, Version 2.0
"""

from django.shortcuts import render
from .models import GroundStation, Operator, Aperture
from datetime import timezone
from .analysis import Analysis, Satellite
from .forms import InputForm, TimeInputStyles
from django.views import View
import math
from orbitscalc.analysis import AnalysisModes


ANALYSIS_TEMPLATE = 'orbitscalc/analysis.html'
ANTENNA_PREFIX = "_antenna_"
OPERATOR_PREFIX = "_operator_"
GROUND_STATION_PREFIX = "_ground_station_"


def create_display_information():
    ground_stations_dict = dict()
    ground_station_to_operator_dict = dict()
    for ground_station in GroundStation.objects.order_by("name"):
        antennas = ground_station.usable_antennas
        if antennas:
            # Betreiber dieser Bodenstation
            operators_of_this_ground_station = ground_station.operator.all()
            operators_list = list()
            for operator in operators_of_this_ground_station:
                operators_list.append(operator.id)
            ground_station_to_operator_dict.update({ground_station.id: operators_list})
            # Liste aller Antennen erstellen
            antennas_dict = dict()
            for antenna in antennas:
                antennas_dict.update({antenna.id: {
                    "id": antenna.id,
                    "name": antenna.name,
                    "selected": False,
                    "lat": antenna.latitude,
                    "lon": antenna.longitude,
                    "alt": antenna.altitude
                }})
            # Koordinaten zum Darstellen in Cesium
            koords = ground_station.coordinates_for_display
            lat = koords["lat"]
            lon = koords["lon"]
            alt = koords["alt"]
            ground_stations_dict.update({ground_station.id: {
                "id": ground_station.id,
                "name": ground_station.name,
                "antennas": antennas_dict,
                "selected": False,
                "lat": lat,
                "lon": lon,
                "alt": alt
            }})
    # Betreiber (-> Bodenstationen)
    operators_dict = dict()
    operator_to_ground_station_dict = dict()
    # Betreiber in Ausgabe nach Namen alphabetisch sortiert
    for operator in Operator.objects.order_by("name"):
        ground_stations_of_this_operator = operator.usable_ground_stations
        # pruefen, ob es verwendbare Bodenstationen gibt
        if ground_stations_of_this_operator:
            operators_dict.update(
                {operator.id: {
                    "id": operator.id,
                    "name": operator.name,
                    "selected": False,
                    "ground_stations": operator.usable_ground_stations
                }})
            # Liste mit Bodenstationen dieses Betreibers erstellen
            ground_stations_list = list()
            for bod in ground_stations_of_this_operator:
                ground_stations_list.append(bod.id)
            operator_to_ground_station_dict.update({operator.id: ground_stations_list})
    return {
        "operators": operators_dict,
        "ground_stations": ground_stations_dict,
        "operators_to_ground_stations": operator_to_ground_station_dict,
        "ground_stations_to_operators": ground_station_to_operator_dict
    }


class AnalysisView(View):
    def __init__(self):
        super().__init__()
        # verwendetes Template
        self.template = ANALYSIS_TEMPLATE
        self.display_information = create_display_information()

    def get(self, request):
        form = InputForm()
        return render(request, self.template, {'form': form, "display_information": self.display_information})

    def post(self, request):
        form = InputForm(request.POST)
        # zum Darstellen im Template: keys von type=betreiber/bodenstation/antenne: _typ_id
        data = request.POST
        ground_stations = list()
        antennas = list()
        operators = list()
        # GroundStation.objects.get(pk=nummer)
        for k in data.keys():
            # Bodenstationen aus Anfrage ermitteln
            if k[:len(GROUND_STATION_PREFIX)] == GROUND_STATION_PREFIX:
                ground_station_id = int(k[len(GROUND_STATION_PREFIX):])
                ground_stations.append(ground_station_id)
            # Antennen aus Anfrage ermitteln
            elif k[:len(ANTENNA_PREFIX)] == ANTENNA_PREFIX:
                antenna_id = int(k[len(ANTENNA_PREFIX):])
                antennas.append(antenna_id)
            # Betreiber aus Anfrage ermitteln
            elif k[:len(OPERATOR_PREFIX)] == OPERATOR_PREFIX:
                operator_id = int(k[len(OPERATOR_PREFIX):])
                operators.append(operator_id)
                self.display_information["operators"][operator_id]["selected"] = True
        # Liste zum Darstellen akutalisieren                
        for ground_station_id in ground_stations:
            ground_station = self.display_information["ground_stations"][ground_station_id]
            ground_station["selected"] = True
            for antenna_id in ground_station["antennas"].values():
                if antenna_id["id"] in antennas:
                    antenna_id["selected"] = True
        # Pruefen, ob restliche Eingaben geultig
        if form.is_valid():
            # TLE
            tle = form.cleaned_data['tle'].splitlines()
            name = tle[0]
            tle1 = tle[1]
            tle2 = tle[2]
            # Start- und Endzeit in UTC umwandeln
            start_time = form.cleaned_data['start_time'].replace(tzinfo=timezone.utc)
            end_time = form.cleaned_data['end_time'].replace(tzinfo=timezone.utc)
            # Datenzeitraum mit Eingabemethode
            time_input_style = form.cleaned_data['time_input_style']
            data_period = None
            if time_input_style == TimeInputStyles.PerOrbit.name:
                data_period = False
            elif time_input_style == TimeInputStyles.Custom.name:
                days = float(form.cleaned_data["time_days"])
                hours = float(form.cleaned_data["time_hours"])
                minutes = float(form.cleaned_data["time_minutes"])
                # Zeitraum der Datenmenge in SI-Einheit
                data_period = (days * 24 * 60 + hours * 60 + minutes) * 60
            elif time_input_style == TimeInputStyles.Whole.name:
                data_period = (end_time - start_time).total_seconds()
            # Datenmenge in bit
            data_unit = float(form.cleaned_data["data_unit"])
            data = float(form.cleaned_data["data"])
            data *= data_unit
            # EIRP in W
            eirp_unit = form.cleaned_data["eirp_unit"]
            eirp = float(form.cleaned_data["eirp"])
            if eirp_unit == "W":
                # eirp von W in dBW umwandeln
                eirp = 10 * math.log(eirp, 10)
            # Frequenzbereich
            minimum_frequency = float(form.cleaned_data["minimum_frequency"])
            maximum_frequency = float(form.cleaned_data["maximum_frequency"])
            minimum_frequency_unit = float(form.cleaned_data["minimum_frequency_unit"])
            maximum_frequency_unit = float(form.cleaned_data["maximum_frequency_unit"])
            minimum_frequency = minimum_frequency * pow(10, minimum_frequency_unit)
            maximum_frequency = maximum_frequency * pow(10, maximum_frequency_unit)
            # Analysemodus
            analysis_mode = AnalysisModes[form.cleaned_data["mode"]]
            # AnalyseObjekt mit Daten zu Satelliten erstellen
            tle = (name, tle1, tle2)
            satellite = Satellite(tle, eirp, minimum_frequency, maximum_frequency)
            analysis = Analysis(start_time, end_time, data_period, data, satellite)
            operators_database = list()
            antennas_data_base = list()
            for antenna_id in antennas:
                antennas_data_base.append(Aperture.objects.get(pk=antenna_id))
            for operator_id in operators:
                operators_database.append(Operator.objects.get(pk=operator_id))
            # Falls nichts ausgewählt nur darstellen
            if not antennas_data_base:
                analysis_mode = AnalysisModes.JustOrbit
                display_mode = "no_antennas_selected"
            else:
                display_mode = "result"
            analysis.analyse(operators_database, antennas_data_base, analysis_mode)
            context = {
                'form': form,
                "display_information": self.display_information,
                "analysis": analysis,
                "display_mode": display_mode
            }
            for mode in AnalysisModes:
                context[mode.name] = mode.name
            return render(request, self.template, context)
        return render(request, self.template, {'form': form, "display_information": self.display_information})
