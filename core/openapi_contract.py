"""Reusable OpenAPI response envelopes for documented API operations."""

from rest_framework import serializers


class APIErrorDetailSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.JSONField(allow_null=True)


class APIErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=False)
    status = serializers.CharField(default="error")
    error_code = serializers.CharField()
    message = serializers.CharField()
    error = APIErrorDetailSerializer()
