import click
import logging
import requests
import datetime
import os
import json
import daemonocle
import paho.mqtt.subscribe as subscribe

from sqlalchemy import func, or_, desc
from sqlalchemy.exc import IntegrityError

from telegram import Bot

from app import app, db
from app.models import Device, Raw, Periodik, Lokasi

upbbendungan = ("upbuser", "upbsecret")

UPB_API = ""
URL = "https://prinus.net/api/sensor"
MQTT_HOST = "mqtt.bbws-bsolo.net"
MQTT_PORT = 14983
MQTT_TOPIC = "upbbendungan"
MQTT_CLIENT = ""

logging.basicConfig(
        filename='/tmp/upbflask.log',
        level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')


@app.cli.command()
@click.option('-s', '--sampling', default='', help='Awal waktu sampling')
def example(sampling):
    print("Example Command")
