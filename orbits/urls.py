"""
Orbitscalc
Copyright 2021 Hannes Diener
Licensed under the Apache License, Version 2.0
"""

from django.contrib import admin
from django.urls import include, path, re_path

urlpatterns = [
    path('', include('orbitscalc.urls')),
    re_path(r'^admin/', admin.site.urls, name='admin'),
]
