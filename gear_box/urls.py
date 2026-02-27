from django.contrib import admin
from django.urls import path
from gearapp.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path("gear_value_view/", gear_dashboard_view, name="gear_value_view"),
    path("filter_gear_value/", filter_gear_value, name="filter_gear_value"),
    path("download_gear_value/", download_gear_value, name="download_gear_value"),
    path("filter_gear_ratio/", filter_gear_ratio, name="filter_gear_ratio"),
    path("download_gear_ratio/", download_gear_ratio, name="download_gear_ratio"),
    path("filter_gear_ratio1/", filter_gear_ratio1, name="filter_gear_ratio1"),

]
 
