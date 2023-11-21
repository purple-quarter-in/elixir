from django.db import models
from django.utils import timezone

from apps.client.models import Organisation
from apps.pipedrive.helper import upload_path_rdcapsule, upload_path_service_contract
from apps.user.models import User

# Create your models here.


class RoleDetail(models.Model):
    """Model definition for RoleDetail."""

    # TODO: Define fields here
    role_type = models.CharField(max_length=100)
    budget_range = models.CharField(max_length=100)
    fixed_budget = models.CharField(max_length=50, blank=True, null=True)
    fixed_budget_ul = models.CharField(max_length=50, blank=True, null=True)
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

    def get_lead_id(self):
        return Lead.objects.get(role_id=self.id).id


class Lead(models.Model):
    """Model definition for Lead."""

    # TODO: Define fields here
    organisation = models.ForeignKey(
        Organisation, on_delete=models.DO_NOTHING, related_name="lead_organisation"
    )
    title = models.CharField(max_length=150, blank=True, null=True, db_index=True)
    role = models.ForeignKey(RoleDetail, on_delete=models.DO_NOTHING)
    currency = models.CharField(max_length=3, blank=True, null=True)  # discuss with abhinav
    service_fee = models.CharField(max_length=50, blank=True, null=True)
    service_fee_range = models.CharField(max_length=100, blank=True, null=True)
    flat_fee = models.CharField(max_length=100, blank=True, null=True, default=None)
    equity_fee = models.CharField(max_length=100, blank=True, null=True, default=None)
    retainer_advance = models.BooleanField(blank=True, null=True)
    exclusivity = models.BooleanField(blank=True, null=True)
    source = models.CharField(max_length=100)
    status = models.CharField(default="Unverified", max_length=50, db_index=True)
    reason = models.CharField(max_length=150, blank=True, null=True)
    is_converted_to_prospect = models.BooleanField(default=0, db_index=True)
    archived = models.BooleanField(default=0)
    created_at = models.DateTimeField(editable=False, db_index=True)
    updated_at = models.DateTimeField()
    owner = models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        related_name="lead_owner_user",
    )
    fullfilled_by = models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        related_name="lead_fullfilled_by_user",
    )
    closed_by = models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        related_name="lead_closed_by_user",
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
    verification_time = models.DateTimeField(default=None, blank=True, null=True)
    closure_time = models.DateTimeField(default=None, blank=True, null=True)

    class Meta:
        """Meta definition for Lead."""

        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        permissions = [("access_lead", "Can access Lead")]

    def __str__(self):
        return self.organisation.name

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created_at = timezone.now()
            ROLETYPE = {
                "CTO": "CTO",
                "CPTO": "CPTO",
                "Head of Engineering": "HOE",
                "VP of Engineering": "VPOE",
                "Director of Engineering": "DOE",
                "Site Lead": "SL",
                "Head of Data Science": "HODS",
                "CISO": "ciso",
                "Principal Architect": "PA",
                "Principal Engineer": "PE",
                "VP of Data Science": "VPODS",
                "Director of Data Science": "DODS",
                "Board Member": "BM",
            }

            REGION = {"India": "IND", "USA": "USA", "APAC": "APAC", "MENA": "MENA", "Europe": "EU"}

            count = Lead.objects.filter(
                organisation=self.organisation,
                role__region=self.role.region,
                role__role_type=self.role.role_type,
            ).count()
            self.title = f"{self.organisation.name} - {REGION[self.role.region]} - {ROLETYPE[self.role.role_type]} - {count+1}"
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
    status = models.CharField(default="Qualified", max_length=50, db_index=True)
    reason = models.CharField(max_length=150, blank=True, null=True)
    lead = models.ForeignKey(Lead, on_delete=models.DO_NOTHING)
    is_converted_to_deal = models.BooleanField(default=0, db_index=True)
    archived = models.BooleanField(default=0)
    created_at = models.DateTimeField(editable=False, db_index=True)
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
        return self.lead.title

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(Prospect, self).save(*args, **kwargs)


class Deal(models.Model):
    """Model definition for Deal."""

    # TODO: Define fields here
    # organization = models.ForeignKey(Organisation, on_delete=models.DO_NOTHING)
    # role = models.CharField(max_length=100, blank=True, null=True)
    # budget = models.CharField(max_length=100, blank=True, null=True)
    # location = models.CharField(max_length=100, blank=True, null=True)
    # source = models.CharField(max_length=100)
    deal_value = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(default="In Progress", max_length=50)
    reason = models.CharField(max_length=150, blank=True, null=True)
    prospect = models.ForeignKey(Prospect, on_delete=models.DO_NOTHING)
    lead = models.ForeignKey(Lead, on_delete=models.DO_NOTHING)
    archived = models.BooleanField(default=0)
    created_at = models.DateTimeField(editable=False, db_index=True)
    updated_at = models.DateTimeField()
    owner = models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        related_name="deal_owner_user",
    )
    created_by = models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        related_name="deal_lead_created_by_user",
    )
    updated_by = models.ForeignKey(
        "user.User",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
        related_name="deal_updated_by_user",
    )

    class Meta:
        """Meta definition for Deal."""

        verbose_name = "Deal"
        verbose_name_plural = "Deals"
        permissions = [("access_deal", "Can access deal")]

    def __str__(self):
        return self.lead.title

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        return super(Deal, self).save(*args, **kwargs)


class Activity(models.Model):
    """Model definition for Activity."""

    # Logic to link activity to entity
    title = models.CharField(max_length=100, blank=True, default="")
    lead = models.ForeignKey(
        Lead, related_name="activity_lead", on_delete=models.DO_NOTHING, null=True, default=None
    )
    organisation = models.ForeignKey(
        Organisation,
        related_name="activity_organisation",
        on_delete=models.DO_NOTHING,
        null=True,
        default=None,
    )
    type = models.CharField(max_length=50)
    contact = models.ManyToManyField("client.Contact", related_name="activity_contact")
    mode = models.CharField(max_length=50)
    status = models.CharField(max_length=50, default="In Progress", blank=True, null=True)
    due_date = models.DateTimeField(blank=True, null=True)
    reminder = models.IntegerField(blank=True, null=True)
    rescheduled = models.IntegerField(default=0)
    created_by = models.ForeignKey(
        User, related_name="activity_created_by", on_delete=models.DO_NOTHING
    )
    assigned_to = models.ForeignKey(
        User,
        related_name="activity_assigned_to",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        default=None,
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False, db_index=True)
    closed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        """Meta definition for Activity."""

        verbose_name = "Activity"
        verbose_name_plural = "Activitys"

    def __str__(self):
        """Unicode representation of Activity."""
        return self.type + "_" + self.mode + "_" + self.created_by.get_full_name()


class Note(models.Model):
    """Model definition for Note."""

    activity = models.ForeignKey(
        Activity,
        related_name="notes_activity",
        on_delete=models.DO_NOTHING,
        default=None,
        null=True,
    )
    role_status = models.CharField(max_length=50, blank=True, null=True)
    role_urgency = models.CharField(max_length=50, blank=True, null=True)
    is_retainer_model = models.CharField(max_length=50, blank=True, null=True)
    is_min_flat_Service = models.CharField(max_length=50, blank=True, null=True)
    is_collateral_shared = models.BooleanField(blank=True, null=True)
    is_response_shared = models.BooleanField(blank=True, null=True)
    is_open_engange = models.CharField(max_length=50, blank=True, null=True)
    is_role_clear = models.BooleanField(blank=True, null=True)
    is_willing_pay_ra = models.CharField(max_length=50, blank=True, null=True)
    exp_service_fee = models.CharField(max_length=50, blank=True, null=True)
    is_proposal_shared = models.BooleanField(blank=True, null=True)
    related_to = models.CharField(max_length=50, blank=True, null=True)
    prospect_status = models.CharField(max_length=50, blank=True, null=True)
    deal_status = models.CharField(max_length=50, blank=True, null=True)
    negotiation_broker = models.CharField(max_length=50, blank=True, null=True)
    is_contract_draft_shared = models.BooleanField(blank=True, null=True)
    next_step = models.CharField(max_length=50, blank=True, null=True)
    remarks = models.CharField(max_length=500, blank=True, null=True, default="")
    created_by = models.ForeignKey(
        User, related_name="note_created_by", on_delete=models.DO_NOTHING
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False, db_index=True)

    class Meta:
        """Meta definition for Note."""

        verbose_name = "Note"
        verbose_name_plural = "Notes"

    def __str__(self):
        """Unicode representation of Note."""
        return self.activity_type + "_" + self.mode + "_" + self.created_by.get_full_name()


class changelog(models.Model):
    """Model definition for changelog."""

    type = models.CharField(max_length=50)
    field_name = models.CharField(max_length=50, blank=True, null=True)
    changed_from = models.CharField(max_length=150, blank=True, null=True)
    changed_to = models.CharField(max_length=150, blank=True, null=True)
    description = models.CharField(max_length=150, blank=True, null=True)
    changed_by = models.ForeignKey(
        User, related_name="changed_by", on_delete=models.DO_NOTHING, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False, db_index=True)
    model_name = models.CharField(max_length=50, blank=True, null=True)
    obj_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        """Meta definition for changelog."""

        verbose_name = "changelog"
        verbose_name_plural = "changelogs"

    def __str__(self):
        return self.type + " : " + (self.description or "")


class ServiceContract(models.Model):
    """Model definition for ServiceContract."""

    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE)
    file = models.FileField(upload_to=upload_path_service_contract)
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )
    sent_on = models.DateTimeField(default=None, blank=True, null=True)
    uploaded_by = models.ForeignKey(
        User, related_name="contract_uploaded_by", on_delete=models.DO_NOTHING
    )

    class Meta:
        """Meta definition for ServiceContract."""

        verbose_name = "ServiceContract"
        verbose_name_plural = "ServiceContracts"

    def __str__(self):
        """Unicode representation of ServiceContract."""
        return self.file.url


class RDCapsule(models.Model):
    """Model definition for RDCapsule."""

    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, default=None)
    file = models.FileField(upload_to=upload_path_rdcapsule)
    uploaded_at = models.DateTimeField(auto_now_add=True, editable=False)
    sent_on = models.DateTimeField(default=None, blank=True, null=True)
    uploaded_by = models.ForeignKey(
        User, related_name="rdcapsule_uploaded_by", on_delete=models.DO_NOTHING
    )

    class Meta:
        """Meta definition for RDCapsule."""

        verbose_name = "RDCapsule"
        verbose_name_plural = "RDCapsules"

    def __str__(self):
        """Unicode representation of RDCapsule."""
        return self.file.url
