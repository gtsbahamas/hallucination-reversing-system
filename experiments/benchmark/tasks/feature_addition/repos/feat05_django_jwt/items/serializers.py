"""Item serializer."""

from rest_framework import serializers
from .models import Item


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "name", "description", "price", "created_at"]
        read_only_fields = ["id", "created_at"]
