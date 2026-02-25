from django.db import models
from django.utils import timezone

# ===============================
# Main RPM Data Table
# ===============================
class GearValue(models.Model):
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    channel = models.CharField(max_length=50, db_index=True)
    rpm = models.FloatField()

    def __str__(self):
        return f"{self.channel} | {self.rpm} RPM @ {self.timestamp}"

# ===============================
# Hourly Statistics
# ===============================
class HourlyGearValueStats(models.Model):
    hour_start = models.DateTimeField(db_index=True)
    max_rpm = models.FloatField()
    min_rpm = models.FloatField()

    def __str__(self):
        return f"{self.hour_start} | Max: {self.max_rpm} | Min: {self.min_rpm}" 


# ===============================
# Daily Statistics
# ===============================
class DailyGearValueStats(models.Model):
    date = models.DateField(unique=True)
    max_rpm = models.FloatField()
    min_rpm = models.FloatField()

    def __str__(self):
        return f"{self.date} | Max: {self.max_rpm} | Min: {self.min_rpm}"


# ===============================
# Data Cycle Control
# ===============================
class DataCycle(models.Model):
    start_time = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=False)

    def __str__(self):
        status = "Active" if self.active else "Inactive"
        return f"Cycle: {status} | Started: {self.start_time}"
    
# ===============================
# Gear Ratio
# ===============================
class GearRatio(models.Model):

    timestamp = models.DateTimeField(db_index=True)

    input_rpm = models.FloatField()

    output1_rpm = models.FloatField(null=True, blank=True)
    output2_rpm = models.FloatField(null=True, blank=True)
    output3_rpm = models.FloatField(null=True, blank=True)
    output4_rpm = models.FloatField(null=True, blank=True)
    ratio1 = models.FloatField(null=True, blank=True)
    ratio2 = models.FloatField(null=True, blank=True)
    ratio3 = models.FloatField(null=True, blank=True)
    ratio4 = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (f"{self.timestamp} | Input: {self.input_rpm} | "
                f"Outputs: [{self.output1_rpm}, {self.output2_rpm}, {self.output3_rpm}, {self.output4_rpm}] | "
                f"Ratios: [{self.ratio1}, {self.ratio2}, {self.ratio3}, {self.ratio4}]")