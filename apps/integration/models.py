from django.db import models
from django.utils import timezone


class Integration(models.Model):
    """Model definition for Integration."""

    service_name = models.CharField(max_length=100)
    auth_type = models.CharField(max_length=50)
    user_email = models.EmailField(blank=True, null=True)
    access_token = models.TextField()
    refresh_token = models.TextField()
    expiry = models.DateTimeField()
    userinfo = models.JSONField(null=True, blank=False)
    token_type = models.CharField(max_length=50)
    archived = models.BooleanField(default=0)
    created_at = models.DateTimeField(editable=False, db_index=True)
    updated_at = models.DateTimeField()

    class Meta:
        """Meta definition for Integration."""

        verbose_name = "Integration"
        verbose_name_plural = "Integrations"

    def __str__(self):
        """Unicode representation of Integration."""
        pass

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(Integration, self).save(*args, **kwargs)
