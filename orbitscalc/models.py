"""
Orbitscalc
Copyright 2021 Hannes Diener
Licensed under the Apache License, Version 2.0
"""

from django.db import models


MEGA_PREFIX_SIZE = 1e6


class Operator(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    @property
    def usable_ground_stations(self):
        all_ground_stations = self.groundstation_set.all()
        usable = list()
        for ground_station in all_ground_stations:
            if ground_station.usable_antennas:
                usable.append(ground_station)
        return usable


class GroundStation(models.Model):
    name = models.CharField(max_length=200)
    operator = models.ManyToManyField(Operator)

    def __str__(self):
        return self.name

    @property
    def usable_antennas(self):
        all_antennas = Aperture.objects.filter(groundstation_id=self.id).order_by("name")
        usable_antennas = []
        for antenna in all_antennas:
            if antenna.is_usable:
                usable_antennas.append(antenna)
        return usable_antennas

    # Zum Darstellen der Bodenstation auf Karte, Mittelwert der Koordinaten aller Antennen übermitteln
    @property
    def coordinates_for_display(self):
        average_latitude = 0
        average_longitude = 0
        average_altitude = 0
        for antenne in self.usable_antennas:
            average_latitude += antenne.latitude / len(self.usable_antennas)
            average_longitude += antenne.longitude / len(self.usable_antennas)
            average_altitude += antenne.altitude / len(self.usable_antennas)
        return {'lat': average_latitude, 'lon': average_longitude, 'alt': average_altitude}
        

class Aperture(models.Model):
    name = models.CharField(max_length=200, null=True)
    groundstation = models.ForeignKey(GroundStation, on_delete=models.SET_NULL, null=True)
    latitude = models.DecimalField(max_digits=15, decimal_places=12, null=True)
    longitude = models.DecimalField(max_digits=15, decimal_places=12, null=True)
    altitude = models.DecimalField(max_digits=7, decimal_places=3, null=True)
    eirp_dbw = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    gt_dbw_k = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    diameter = models.DecimalField(max_digits=6, decimal_places=3, null=True)
    is_operational = models.BooleanField(null=True)
    polarisation = models.CharField(max_length=200, null=True)

    def __str__(self):
        if self.name:
            return "aperture %s of %s" % (self.name, self.groundstation.name)
        else:
            return "unnamed aperture %i of %s " % (self.id, str(self.groundstation.name))

    @property
    def usable_links(self):
        links = Link.objects.filter(aperture_id=self.id)
        usable = []
        for link in links:
            if link.is_usable:
                usable.append(link)
        return usable

    # prueft, ob fuer alle relevanten Parameter Werte angegeben sind und die Antenne betriebsfaehig ist
    @property
    def is_usable(self):
        if self.name and self.latitude and self.longitude and \
                self.altitude and self.gt_dbw_k and self.is_operational is not False and self.usable_links:
            return True
        else:
            return False


class Link(models.Model):
    aperture = models.ForeignKey(Aperture, on_delete=models.CASCADE, null=True)
    frequency_min_MHz = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    frequency_max_MHz = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    is_downlink = models.BooleanField(null=True)

    def __str__(self):
        return "link %i of aperture %s" % (self.id, self.aperture)

    # prueft, ob fuer alle relevanten Parameter Werte angegeben sind
    @property
    def is_usable(self):
        if self.frequency_max_MHz and self.frequency_min_MHz and self.is_downlink is not None:
            return True

    @property
    def frequency_min(self):
        return float(self.frequency_min_MHz) * MEGA_PREFIX_SIZE

    @property
    def frequency_max(self):
        return float(self.frequency_max_MHz) * MEGA_PREFIX_SIZE
