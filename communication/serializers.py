from rest_framework import serializers
from .models import CallSession, Participant


class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = ('id', 'user_id', 'uid', 'joined_at', 'left_at')


class CallSessionSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)
    class Meta:
        model = CallSession
        fields = ('id', 'channel_name', 'host_id', 'started_at', 'ended_at', 'metadata', 'participants')