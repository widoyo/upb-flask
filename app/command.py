import click
import logging
import requests
import datetime
import os
import json
import daemonocle
import paho.mqtt.subscribe as subscribe
import mysql.connector

from pprint import pprint

from sqlalchemy import func, or_, desc
from sqlalchemy.exc import IntegrityError

from telegram import Bot

from app import app, db
from app.models import Bendungan, Embung

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


@app.cli.command()
def import_master():
    mydb = mysql.connector.connect(
        host="localhost",
        user=os.environ['MYSQL_USER'],
        passwd=os.environ['MYSQL_PASS'],
        database=os.environ['MYSQL_DB']
    )
    mycursor = mydb.cursor()

    all_waduk = custom_query(mycursor, 'agent', limit=None)
    # pprint(all_waduk)
    for waduk in all_waduk:
        try:
            pprint(waduk)
            new_bend = Bendungan(
                id=waduk["AgentID"],
                nama=waduk["cname"],
                ll=waduk["ll"],
                muka_air_min=waduk["CriticalLower"],
                muka_air_normal=waduk["Normal"],
                muka_air_max=waduk["SiagaUpper"],
                sedimen=waduk["Sedimen"],
                bts_elev_awas=waduk["bts_elev_awas"],
                bts_elev_siaga=waduk["bts_elev_siaga"],
                bts_elev_waspada=waduk["bts_elev_waspada"],
                lbi=waduk["lbi"],
                volume=waduk["volume"],
                lengkung_kapasitas=waduk["lengkung_kapasitas"],
                elev_puncak=waduk["elev_puncak"],
                kab=waduk["kab"],
                vn1_panjang_saluran=waduk["vn1_panjang_saluran"],
                vn2_panjang_saluran=waduk["vn2_panjang_saluran"],
                vn3_panjang_saluran=waduk["vn3_panjang_saluran"],
                vn1_q_limit=waduk["vn_q1_limit"],
                vn2_q_limit=waduk["vn_q2_limit"],
                vn3_q_limit=waduk["vn_q3_limit"],
                vn1_tin_limit=waduk["vn_tin1_limit"],
                vn2_tin_limit=waduk["vn_tin2_limit"],
                vn3_tin_limit=waduk["vn_tin3_limit"]
            )
            db.session.add(new_bend)
            db.session.commit()
        except Exception as e:
            print(f"Error : {e}")
            db.session.rollback()

    all_embung = custom_query(mycursor, 'embung', limit=None)
    for embung in all_embung:
        try:
            pprint(embung)
            new_emb = Embung(
                id=embung["id"],
                nama=embung["nama"],
                jenis=embung["jenis"],
                desa=embung["desa"],
                kec=embung["kec"],
                kab=embung["kab"],
                ll=embung["ll"],
                sumber_air=embung["sumber_air"],
                tampungan=embung["tampungan"],
                debit=embung["debit"],
                pipa_transmisi=embung["pipa_transmisi"],
                saluran_transmisi=embung["saluran_transmisi"],
                air_baku=embung["air_baku"],
                irigasi=embung["irigasi"],
                c_user=embung["cuser"],
                c_date=embung["cdate"],
                m_user=embung["muser"],
                m_date=embung["mdate"]
            )
            db.session.add(new_emb)
            db.session.commit()
        except Exception as e:
            print(f"Error : {e}")
            db.session.rollback()


def custom_query(cursor, table, filter=None, limit=None):
    cursor.execute(f"SHOW columns FROM {table}")
    columns = [column[0] for column in cursor.fetchall()]

    where = ""
    data_limit = ""
    if filter:
        for col in filter:
            if where:
                where += " AND "
            else:
                where += " WHERE "

            if isinstance(filter[col], str):
                where += f"{col}='{filter[col]}'"
            else:
                where += f"{col}={filter[col]}"
    if limit:
        data_limit += f" LIMIT {limit}"
    cursor.execute(f"SELECT * FROM {table}{where}{data_limit}")
    result = cursor.fetchall()
    results = []
    for res in result:
        results.append(dict(zip(columns, res)))
    return results
