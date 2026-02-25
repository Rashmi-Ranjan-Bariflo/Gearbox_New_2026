from django.contrib import admin
from .models import GearValue, HourlyGearValueStats, DailyGearValueStats, DataCycle, GearRatio
@admin.register(GearValue)
class gear_valueAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "channel", "rpm"]
    ordering = ["-timestamp"]
    readonly_fields = ["timestamp"]
@admin.register(HourlyGearValueStats)
class HourlyGearValueStatsAdmin(admin.ModelAdmin):
    list_display = ('hour_start', 'max_rpm', 'min_rpm')
    ordering = ('-hour_start',)

@admin.register(DailyGearValueStats)
class DailyGearValueStatsAdmin(admin.ModelAdmin):
    list_display = ('date', 'max_rpm', 'min_rpm')
    ordering = ('-date',)

@admin.register(DataCycle)
class DataCycleAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'active')

@admin.register(GearRatio)
class GearRatioAdmin(admin.ModelAdmin):
    list_display = ('input_rpm', 'timestamp', 'output1_rpm', 'output2_rpm','output3_rpm', 'output4_rpm', 'ratio1', 'ratio2', 'ratio3', 'ratio4')