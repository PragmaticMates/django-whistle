from rest_framework import serializers, viewsets

from pragmatic.serializers import ContentTypeSerializer
from whistle.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    description = serializers.CharField()
    short_description = serializers.CharField()
    object_content_type = ContentTypeSerializer(read_only=True)
    target_content_type = ContentTypeSerializer(read_only=True)

    class Meta:
        model = Notification
        exclude = []


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return super().get_queryset()\
            .for_recipient(self.request.user) \
            .select_related(
                'object_content_type',
                'target_content_type',
                'recipient',
                'actor'
            )
