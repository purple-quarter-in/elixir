from django.db import models
from django.utils import timezone

from apps.client.models import Organisation

# Create your models here.


class RoleDetail(models.Model):
    """Model definition for RoleDetail."""

    # TODO: Define fields here
    role_type = models.CharField(max_length=100)
    budget_range = models.CharField(max_length=100)
    fixed_budget = models.FloatField(blank=True, null=True)
    fixed_budget_ul = models.FloatField(blank=True, null=True)
    esop_rsu = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True, null=True)
    time_To_fill = models.CharField(max_length=100, blank=True, null=True)
    archived = models.BooleanField(default=0)
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField()

    class Meta:
        """Meta definition for RoleDetail."""

        verbose_name = "RoleDetail"
        verbose_name_plural = "RoleDetails"

    def __str__(self):
        return self.role_type

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(RoleDetail, self).save(*args, **kwargs)


class Lead(models.Model):
    """Model definition for RoleDetail."""

    # TODO: Define fields here
    organisation = models.ForeignKey(Organisation, on_delete=models.DO_NOTHING)
    title = models.CharField(max_length=50, blank=True, null=True)
    role = models.ForeignKey(RoleDetail, on_delete=models.DO_NOTHING)
    currency = models.CharField(max_length=3, blank=True, null=True)  # discuss with abhinav
    service_fee = models.FloatField(blank=True, null=True)
    service_fee_range = models.CharField(max_length=100, blank=True, null=True)
    retainer_advance = models.BooleanField(blank=True, null=True)
    exclusivity = models.BooleanField(blank=True, null=True)
    source = models.CharField(max_length=100)
    status = models.CharField(default="Unverified", max_length=50)
    is_converted_to_prospect = models.BooleanField(default=0)
    archived = models.BooleanField(default=0)
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField()
    owner = models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        related_name="lead_owner_user",
    )
    created_by = models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        related_name="lead_created_by_user",
    )
    updated_by = models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        related_name="lead_updated_by_user",
    )

    class Meta:
        """Meta definition for ContactLead."""

        verbose_name = "ContactLead"
        verbose_name_plural = "ContactLeads"
        permissions = [("access_lead", "Can access Lead")]

    def __str__(self):
        return self.organization

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(Lead, self).save(*args, **kwargs)


class Prospect(models.Model):
    """Model definition for Prospect."""

    # TODO: Define fields here
    # organization = models.ForeignKey(Organisation, on_delete=models.DO_NOTHING)
    # role = models.CharField(max_length=100, blank=True, null=True)
    # budget = models.CharField(max_length=100, blank=True, null=True)
    # location = models.CharField(max_length=100, blank=True, null=True)
    # source = models.CharField(max_length=100)
    status = models.CharField(default="Qualified", max_length=50)
    lead = models.ForeignKey(Lead, on_delete=models.DO_NOTHING)
    is_converted_to_deal = models.BooleanField(default=0)
    archived = models.BooleanField(default=0)
    created_at = models.DateTimeField(editable=False)
    updated_at = models.DateTimeField()
    owner = models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        related_name="prospect_owner_user",
    )
    created_by = models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        related_name="prospect_lead_created_by_user",
    )
    updated_by = models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        related_name="prospect_updated_by_user",
    )

    class Meta:
        """Meta definition for Prospect."""

        verbose_name = "Prospect"
        verbose_name_plural = "Prospects"
        permissions = [("access_prospect", "Can access prospect")]

    def __str__(self):
        return self.organization

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(Prospect, self).save(*args, **kwargs)
