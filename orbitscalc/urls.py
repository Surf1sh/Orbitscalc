"""
Orbitscalc
Copyright 2021 Hannes Diener
Licensed under the Apache License, Version 2.0
"""


from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import RedirectView
from . import views
from django.contrib import admin

faviconView = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [
    path('analyse', views.AnalysisView.as_view(), name="analyse"),
    path('', views.AnalysisView.as_view()),
    re_path(r'^favicon\.ico$', faviconView),
]