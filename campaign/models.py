from django.utils import timezone
from django.db import models


# Create your models here.
class ContactLead(models.Model):
    """Model definition for ContactLead."""

    # TODO: Define fields here
    name = models.CharField(max_length=100)
    company_email = models.EmailField(max_length=100)
    std_code = models.CharField(max_length=5)
    phone = models.CharField(max_length=15)
    organization = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    budget = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    source = models.CharField(max_length=100)
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField()

    class Meta:
        """Meta definition for ContactLead."""

        verbose_name = "ContactLead"
        verbose_name_plural = "ContactLeads"

    def __str__(self):
        return self.organization

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(ContactLead, self).save(*args, **kwargs)
