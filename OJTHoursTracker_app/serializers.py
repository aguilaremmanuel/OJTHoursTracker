from rest_framework import serializers
from .models import TimeEntry

class TimeEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeEntry
        fields = ['no', 'date', 'morning_in', 'morning_out', 'afternoon_in', 'afternoon_out', 'evening_in', 'evening_out', 'total_hours']
        read_only_fields = ['no', 'time_created', 'user', 'total_hours']
