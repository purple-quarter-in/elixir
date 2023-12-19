from django.db import models

from apps.user.models import User


# Create your models here.
class Notification(models.Model):
    """Model definition for Notification."""

    type = models.CharField(max_length=50)
    is_viewed = models.BooleanField(default=False)
    archived = models.BooleanField(default=False, db_index=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    user = models.ForeignKey(User, related_name="notification_user", on_delete=models.CASCADE)
    model_name = models.CharField(max_length=50, blank=True, null=True)
    object_id = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    data_json = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        """Meta definition for Notification."""

        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        """Unicode representation of Notification."""
        pass
