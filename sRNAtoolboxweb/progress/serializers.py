from rest_framework import serializers
from models import JobStatus


class JobStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobStatus
        fields = '__all__'

    # def create(self, validated_data):
    #     # status = validated_data.pop('status')
    #     js = JobStatus.objects.create(**validated_data)
    #     return js


