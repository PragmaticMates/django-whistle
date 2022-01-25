from django.utils.translation import ngettext

from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from pragmatic.serializers import ContentTypeNaturalField
from whistle.models import Notification


class PushSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = []

    def to_internal_value(self, data):
        return {
            'body': 'test',
            'title': 'skuska',
            # 'image': ''
        }

    def to_representation(self, instance):
        # return '.'.join(instance.natural_key())
        pass


class NotificationSerializer(serializers.ModelSerializer):
    description = serializers.CharField()
    short_description = serializers.CharField()
    object_content_type = ContentTypeNaturalField()
    target_content_type = ContentTypeNaturalField()
    push_config = serializers.JSONField(read_only=True)

    class Meta:
        model = Notification
        exclude = []


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
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


class MarkNotificationsAsReadAPIView(APIView):
    permission_classes = [IsAuthenticated]
    operations = ['apply', 'ignore']

    def patch(self, request, *args, **kwargs):
        notification_id = request.GET.get('notification_id', None)
        unread_notifications = request.user.notifications.unread()

        if notification_id:
            unread_notifications = unread_notifications.filter(id=notification_id)

        num_notifications = unread_notifications.count()
        unread_notifications.mark_as_read()
        request.user.clear_unread_notifications_cache()

        return Response(status=200, data=ngettext(
            '%(count)d notification marked as read',
            '%(count)d notifications marked as read',
            num_notifications,
        ) % {'count': num_notifications})
