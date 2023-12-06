import requests
from django.conf import settings

mapping = {"elixir-stage-alerts": settings.SLACK_HOOK_URL_ELIXIR_STAGE_ALERTS}


def slack_send_message(channel, message):
    if mapping[channel] != "":
        requests.post(
            mapping[channel],
            json={"text": "\n".join(message)},
            timeout=3,
        )
