import logging
from datetime import datetime
from urllib import request

import requests
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.job import Job
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from django.db import connection
from sqlalchemy import Connection

from apps.notification.models import Notification
from elixir.settings.base import DATABASES

logging.basicConfig()
logging.getLogger("apscheduler").setLevel(logging.INFO)

db_settings = DATABASES["default"]
db_url = f"mysql://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
mongo_db_url = "mongodb://localhost:27017/elixir"
mongo = f"mongodb:///?Server=localhost&Port=27017&Database=elixir"
request_domain = settings.API_URL


class Schedular:
    scheduler = None

    def my_listener(self, event):
        print("in listnrer")
        self.scheduler.print_jobs("default")
        print(self.scheduler._executors)
        if event.exception:
            print(f"The job {event.job_id} crashed with execption:- {event.exception}:(")
        else:
            print(f"The job {event.job_id} worked :)")
        if connection.connection:
            # Check the connection's status
            if connection.is_usable():
                print("The database connection is fresh.")
                connection.close()
            else:
                connection.close()
                connection.connect()

    def __init__(self):
        executors = {"default": ThreadPoolExecutor(20), "processpool": ProcessPoolExecutor(5)}
        job_defaults = {
            "coalesce": False,
            "misfire_grace_time": 60 * 60,
        }
        self.scheduler = BackgroundScheduler(
            timezone=settings.TIME_ZONE, job_defaults=job_defaults, executors=executors
        )
        self.scheduler.add_listener(self.my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.scheduler.add_jobstore(
            SQLAlchemyJobStore(
                db_url,
                engine_options={
                    "pool_pre_ping": True,
                    "pool_recycle": 3600,
                    "echo": True,
                    "echo_pool": True,
                },
            ),
            "default",
        )
        # self.scheduler.add_job(
        #     my_job,
        #     trigger=CronTrigger(second="*/4"),  # Every 10 seconds
        #     id="my_job",  # The `id` assigned to each job MUST be unique
        #     max_instances=1,
        #     replace_existing=True,
        # )
        self.scheduler.start()


def schedule_create_notification(instance, type, description, user, model_name):
    response = requests.post(
        f"{request_domain}/v1/api/notification/schedule_create_notification/",
        json={
            "type": type,
            "description": description,
            "user": user.id,
            "model_name": model_name,
            "object_id": instance.id if instance else None,
        },
    )
    print(response.json())


def schedule_refresh_docusign_token(instance):
    response = requests.post(
        f"{request_domain}/docusign_refresh_token",
        json={"instance": instance},
    )
    print(response.json())


# scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
# scheduler.add_jobstore(DjangoJobStore(), "default")

# scheduler.add_job(
#     my_job,
#     trigger=CronTrigger(second="*/10"),  # Every 10 seconds
#     id="my_job",  # The `id` assigned to each job MUST be unique
#     max_instances=1,
#     replace_existing=True,
# )
# logger.info("Starting scheduler...")
# scheduler.start()


# The `close_old_connections` decorator ensures that database connections, that have become
# unusable or are obsolete, are closed before and after your job has run. You should use it
# to wrap any jobs that you schedule that access the Django database in any way.
# @util.close_old_connections
# def delete_old_job_executions(max_age=604_800):
#     """
#     This job deletes APScheduler job execution entries older than `max_age` from the database.
#     It helps to prevent the database from filling up with old historical records that are no
#     longer useful.

#     :param max_age: The maximum length of time to retain historical job execution records.
#                     Defaults to 7 days.
#     """
#     DjangoJobExecution.objects.delete_old_job_executions(max_age)


# class Command(BaseCommand):
#     help = "Runs APScheduler."


# def start_schedular(*args, **options):

#     scheduler.add_job(
#         my_job,
#         trigger=CronTrigger(second="*/10"),  # Every 10 seconds
#         id="my_job",  # The `id` assigned to each job MUST be unique
#         max_instances=1,
#         replace_existing=True,
#     )
#     logger.info("Added job 'my_job'.")

#     scheduler.add_job(
#         delete_old_job_executions,
#         trigger=CronTrigger(
#             day_of_week="mon", hour="00", minute="00"
#         ),  # Midnight on Monday, before start of the next work week.
#         id="delete_old_job_executions",
#         max_instances=1,
#         replace_existing=True,
#     )
#     logger.info("Added weekly job: 'delete_old_job_executions'.")

#     try:
#         logger.info("Starting scheduler...")

#         # return scheduler
#     except KeyboardInterrupt:
#         logger.info("Stopping scheduler...")
#         scheduler.shutdown()
#         logger.info("Scheduler shut down successfully!")
# scheduler = Schedular()
# scheduler.scheduler.add_job()
