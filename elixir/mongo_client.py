from django.conf import settings
from pymongo import MongoClient


def get_db_handle(db_name, host, port, username, password):
    client = MongoClient(host=host, port=int(port), username=username, password=password)
    db_handle = client["db_name"]
    return db_handle, client


def get_db_handle_conn_string(conn_string=settings.MONGO_CONN_STR):
    client = MongoClient(conn_string) if conn_string else MongoClient()
    return client
