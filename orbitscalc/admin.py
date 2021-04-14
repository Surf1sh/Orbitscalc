"""
Orbitscalc
Copyright 2021 Hannes Diener
Licensed under the Apache License, Version 2.0
"""

from django.contrib import admin
from .models import GroundStation, Operator, Aperture, Link

admin.site.register(Operator)
admin.site.register(GroundStation)
admin.site.register(Aperture)
admin.site.register(Link)
