from django.db import models
from django.utils import timezone


# Create your models here.
class Organisation(models.Model):
    """Model definition for Organisation."""

    name = models.CharField(max_length=100)
    registered_name = models.CharField(max_length=100, blank=True, null=True)
    govt_id = models.CharField(max_length=100, blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)
    industry = models.CharField(max_length=50, blank=True, null=True)
    domain = models.CharField(max_length=50, blank=True, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    last_funding_stage = models.CharField(max_length=50, blank=True, null=True)
    last_funding_amount = models.IntegerField(blank=True, null=True)
    funding_currency = models.CharField(max_length=3, blank=True, null=True)
    archived = models.BooleanField(default=0)
    segment = models.CharField(max_length=50, blank=True, null=True)
    created_by = models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        related_name="organisation_created_by_user",
    )
    updated_by = models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        related_name="organisation_updated_by_user",
    )
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta definition for Organisation."""

        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"
        permissions = [("access_organisation", "Can access organisation")]

    def __str__(self):
        """Unicode representation of Organisation."""
        return self.name
        pass

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(Organisation, self).save(*args, **kwargs)

    def get_absolute_url(self):
        """Return absolute url for Organisation."""
        return ""


class Contact(models.Model):
    """Model definition for Contact."""

    organisation = models.ForeignKey(Organisation, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    std_code = models.CharField(max_length=5)
    phone = models.CharField(max_length=15)
    designation = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta definition for Contact."""

        verbose_name = "Contact"
        verbose_name_plural = "Contacts"

    def __str__(self):
        """Unicode representation of Contact."""
        return self.name
        pass

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(Contact, self).save(*args, **kwargs)

    def get_absolute_url(self):
        """Return absolute url for Contact."""
        return ""
