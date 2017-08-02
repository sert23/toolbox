from rest_framework import serializers
from progress.models import JobStatus, Status

class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ['status_progress']

class JobStatusSerializer(serializers.ModelSerializer):
    status = StatusSerializer(many=True)
    class Meta:
        model = JobStatus
        fields = '__all__'


