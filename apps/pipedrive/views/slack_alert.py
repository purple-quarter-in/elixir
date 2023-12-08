from datetime import datetime, timedelta

from apps.integration.slack import slack_send_message
from apps.pipedrive.models import Lead
from elixir.wsgi import Apschedular


def schedule_slack_lead_ownership_assign(instance):
    print(instance)
    lead = Lead.objects.get(id=instance)
    if not lead.owner:
        region = lead.role.region
        slack_send_message(
            "elixir-stage-alerts",
            [
                f"** 🚨 Elixir Alert Triggered **",
                f"*Related to*: Lead Ownership Assignment",
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
