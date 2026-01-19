from django.urls import path, include

urlpatterns = [
    path('notifications/', include('whistle.urls', namespace='notifications')),
]
