from datetime import datetime, timedelta

from apps.integration.slack import slack_send_message
from apps.pipedrive.models import Lead
from elixir.wsgi import Apschedular


def schedule_slack_lead_ownership_assign(instance):
    lead = Lead.objects.get(id=instance)
    if not lead.owner:
        region = lead.role.region
        slack_send_message(
            "elixir-stage-alerts",
            [
                f"** 🚨 Elixir Alert Triggered **",
                f"*Related to*: Pending Lead Ownership Assignment",
                f"*For*: {'<@kiran.satya>' if region in ['India','MENA'] else '<@ved.prakash>'}",
                f"*Entity*: {lead.title}",
                f"*Required Action*: Assign Lead Owner ",
            ],
        )
        Apschedular.scheduler.add_job(
            schedule_slack_lead_ownership_assign,
            trigger="date",
            run_date=datetime.now() + timedelta(minutes=60),
            id=f"schedule_slack_lead_ownership_assign-{lead.id}",  # The `id` assigned to each job MUST be unique
            max_instances=1,
            kwargs={"instance": lead.id},
            replace_existing=True,
        )
    pass


def schedule_slack_lead_verification(instance):
    lead = Lead.objects.get(id=instance)
    if lead.status == "Unverified":
        target_owner_user_id = (lead.owner.email).split("@")[0]
        slack_send_message(
            "elixir-stage-alerts",
            [
                f"** 🚨 Elixir Alert Triggered **",
                f"*Related to*: Pending Lead Verification",
                f"*For*: <@{target_owner_user_id}>",
                f"*Entity*: {lead.title}",
                f"*Required Action*: Lead Verification and State Change",
            ],
        )


def schedule_slack_lead_to_prospect(instance):
    lead = Lead.objects.get(id=instance)
    if lead.status == "Verified" and lead.is_converted_to_prospect == False:
        target_owner_user_id = (lead.owner.email).split("@")[0]
        slack_send_message(
            "elixir-stage-alerts",
            [
                f"** 🚨 Elixir Alert Triggered **",
                f"*Related to*: Pending Lead to Prospect Conversion",
                f"*For*: <@{target_owner_user_id}>",
                f"*Entity*: {lead.title}",
                f"*Required Action*: Either Promote Lead or Change Lead State",
            ],
        )
