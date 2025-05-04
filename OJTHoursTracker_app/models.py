from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from datetime import datetime, timedelta

class User(AbstractUser):
    email = models.EmailField(unique=True)  # This is crucial
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    profile_picture = models.URLField(max_length=500, blank=True, null=True)
    required_hours = models.FloatField(null=True, blank=True, default=0)
    rendered_hours = models.FloatField(null=True, blank=True, default=0)
    
    class Meta:
        db_table = 'tbl_user'

    def __str__(self):
        return self.email
    

class TimeEntry(models.Model):

    no = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='id')
    date = models.DateField()
    
    morning_in = models.TimeField(null=True, blank=True)
    morning_out = models.TimeField(null=True, blank=True)
    afternoon_in = models.TimeField(null=True, blank=True)
    afternoon_out = models.TimeField(null=True, blank=True)
    evening_in = models.TimeField(null=True, blank=True)
    evening_out = models.TimeField(null=True, blank=True)

    time_created = models.DateTimeField(auto_now_add=True)
    total_hours = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'tbl_time_entry'

    def save(self, *args, **kwargs):
        total = timedelta()
        pairs = [
            (self.morning_in, self.morning_out),
            (self.afternoon_in, self.afternoon_out),
            (self.evening_in, self.evening_out),
        ]

        for start, end in pairs:
            if start and end:
                start_dt = datetime.combine(self.date, start)
                end_dt = datetime.combine(self.date, end)
                total += (end_dt - start_dt)

        total_hours = round(total.total_seconds() / 3600, 2)

        # If total_hours is negative, fix it to zero
        if total_hours < 0:
            total_hours = 0

        self.total_hours = total_hours

        super().save(*args, **kwargs)

        # After saving the time entry, update the user's rendered_hours
        if self.user:
            self.user.rendered_hours = (self.user.rendered_hours or 0) + self.total_hours
            self.user.save()