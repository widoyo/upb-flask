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

from upb_app import app, db
from upb_app.models import Bendungan, Embung, Rencana, Users, Asset
from upb_app.models import Kerusakan, Kegiatan, Foto, BendungAlert, CurahHujanTerkini
from upb_app.models import ManualDaily, ManualTma, ManualVnotch, ManualPiezo

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

mydb = mysql.connector.connect(
    host="localhost",
    user=os.environ['MYSQL_USER'],
    passwd=os.environ['MYSQL_PASS'],
    port=3306,
    database=os.environ['MYSQL_DB']
)
mycursor = mydb.cursor()


@app.cli.command()
@click.option('-s', '--sampling', default='', help='Awal waktu sampling')
def mysql_test(sampling):
    all_waduk = custom_query(mycursor, 'agent', limit=None)
    for waduk in all_waduk:
        print(waduk['AgentName'])


@app.cli.command()
def import_manual_data():
    print("Disabled")
    return

    waduk_daily = custom_query(mycursor, 'waduk_daily', limit=None)
    print(f"Importing Manual Data")
    count = 0
    for daily in waduk_daily:
        count += 1
        if count % 1000 == 0:
            print(f"At {count} Data")
        # Manual Daily
        try:
            obj_dict = {
                "sampling": daily['waktu'],
                "ch": daily['curahhujan'],
                "inflow_vol": daily['inflow_v'],
                "inflow_deb": daily['inflow_q'],
                "intake_vol": daily['intake_v'],
                "intake_deb": daily['intake_q'],
                "outflow_vol": daily['outflow_v'],
                "outflow_deb": daily['outflow_q'],
                "spillway_vol": daily['spillway_v'],
                "spillway_deb": daily['spillway_q'],
                "bendungan_id": daily['pos_id']
            }
            md = ManualDaily.query.filter(
                                        ManualDaily.sampling == daily['waktu'],
                                        ManualDaily.bendungan_id == daily['pos_id']
                                    ).first()
            if md:
                # print(f"Updating manual daily {daily['waktu']} for id {daily['pos_id']}")
                for key, value in obj_dict.items():
                    setattr(md, key, value)
            else:
                # print(f"Inserting manual daily {daily['waktu']} for id {daily['pos_id']}")
                manual_daily = ManualDaily(**obj_dict)
                db.session.add(manual_daily)
            db.session.commit()
        except Exception as e:
            print(f"-- Error Daily : {e}")
            db.session.rollback()
        # TMA
        try:
            obj_dict = {
                "sampling": daily['waktu'].replace(hour=6),
                "bendungan_id": daily['pos_id'],
                "tma": daily['tma6'],
                "vol": daily['vol6'],
                "c_date": daily['waktu'].replace(hour=6)
            }
            tma6 = ManualTma.query.filter(
                                        ManualTma.sampling == daily['waktu'].replace(hour=6),
                                        ManualTma.bendungan_id == daily['pos_id']
                                    ).first()
            if tma6:
                # print(f"Updating tma6 {daily['waktu'].replace(hour=6)} for id {daily['pos_id']}")
                for key, value in obj_dict.items():
                    setattr(tma6, key, value)
            else:
                # print(f"Inserting tma6 {daily['waktu'].replace(hour=6)} for id {daily['pos_id']}")
                manual_tma6 = ManualTma(**obj_dict)
                db.session.add(manual_tma6)
            db.session.commit()
        except Exception as e:
            print(f"-- Error TMA6 : {type(e)}")
            db.session.rollback()
        try:
            obj_dict = {
                "sampling": daily['waktu'].replace(hour=12),
                "bendungan_id": daily['pos_id'],
                "tma": daily['tma12'],
                "vol": daily['vol12'],
                "c_date": daily['waktu'].replace(hour=12)
            }
            tma12 = ManualTma.query.filter(
                                        ManualTma.sampling == daily['waktu'].replace(hour=12),
                                        ManualTma.bendungan_id == daily['pos_id']
                                    ).first()
            if tma12:
                # print(f"Updating tma12 {daily['waktu'].replace(hour=12)} for id {daily['pos_id']}")
                for key, value in obj_dict.items():
                    setattr(tma12, key, value)
            else:
                # print(f"Inserting tma12 {daily['waktu'].replace(hour=12)} for id {daily['pos_id']}")
                manual_tma12 = ManualTma(**obj_dict)
                db.session.add(manual_tma12)
            db.session.commit()
        except Exception as e:
            print(f"-- Error TMA12 : {type(e)}")
            db.session.rollback()
        try:
            obj_dict = {
                "sampling": daily['waktu'].replace(hour=18),
                "bendungan_id": daily['pos_id'],
                "tma": daily['tma18'],
                "vol": daily['vol18'],
                "c_date": daily['waktu'].replace(hour=18)
            }
            tma18 = ManualTma.query.filter(
                                        ManualTma.sampling == daily['waktu'].replace(hour=18),
                                        ManualTma.bendungan_id == daily['pos_id']
                                    ).first()
            if tma18:
                # print(f"Updating tma18 {daily['waktu'].replace(hour=18)} for id {daily['pos_id']}")
                for key, value in obj_dict.items():
                    setattr(tma18, key, value)
            else:
                # print(f"Inserting tma18 {daily['waktu'].replace(hour=18)} for id {daily['pos_id']}")
                manual_tma18 = ManualTma(**obj_dict)
                db.session.add(manual_tma18)
            db.session.commit()
        except Exception as e:
            print(f"-- Error TMA18 : {type(e)}")
            db.session.rollback()
        # VNotch
        try:
            obj_dict = {
                "sampling": daily['waktu'],
                "vn_tma": daily['vnotch_tin'],
                "vn_deb": daily['vnotch_q'],
                "vn1_tma": daily['vnotch_tin1'],
                "vn1_deb": daily['vnotch_q1'],
                "vn2_tma": daily['vnotch_tin2'],
                "vn2_deb": daily['vnotch_q2'],
                "vn3_tma": daily['vnotch_tin3'],
                "vn3_deb": daily['vnotch_q3'],
                "bendungan_id": daily['pos_id']
            }
            vn = ManualVnotch.query.filter(
                                        ManualVnotch.sampling == daily['waktu'],
                                        ManualVnotch.bendungan_id == daily['pos_id']
                                    ).first()
            if vn:
                # print(f"Updating manual vnotch {daily['waktu']} for id {daily['pos_id']}")
                for key, value in obj_dict.items():
                    setattr(vn, key, value)
            else:
                # print(f"Inserting manual vnotch {daily['waktu']} for id {daily['pos_id']}")
                manual_vnotch = ManualVnotch(**obj_dict)
                db.session.add(manual_vnotch)
            db.session.commit()
        except Exception as e:
            print(f"-- Error VNotch : {type(e)}")
            db.session.rollback()
        # Piezo
        try:
            obj_dict = {
                "sampling": daily['waktu'],
                "p1a": daily['a1'],
                "p1b": daily['b1'],
                "p1c": daily['c1'],
                "p2a": daily['a2'],
                "p2b": daily['b2'],
                "p2c": daily['c2'],
                "p3a": daily['a3'],
                "p3b": daily['b3'],
                "p3c": daily['c3'],
                "p4a": daily['a4'],
                "p4b": daily['b4'],
                "p4c": daily['c4'],
                "p5a": daily['a5'],
                "p5b": daily['b5'],
                "p5c": daily['c5'],
                "bendungan_id": daily['pos_id']
            }
            pz = ManualPiezo.query.filter(
                                        ManualPiezo.sampling == daily['waktu'],
                                        ManualPiezo.bendungan_id == daily['pos_id']
                                    ).first()
            if pz:
                # print(f"Updating manual piezo {daily['waktu']} for id {daily['pos_id']}")
                for key, value in obj_dict.items():
                    setattr(pz, key, value)
            else:
                # print(f"Inserting manual piezo {daily['waktu']} for id {daily['pos_id']}")
                manual_piezo = ManualPiezo(**obj_dict)
                db.session.add(manual_piezo)
            db.session.commit()
        except Exception as e:
            print(f"-- Error Piezo : {type(e)}")
            db.session.rollback()
        # RTOW
        try:
            obj_dict = {
                "sampling": daily['waktu'],
                "po_tma": daily['po_tma'],
                "po_vol": daily['po_vol'],
                "po_inflow_deb": daily['po_inflow_q'],
                "po_outflow_deb": daily['po_outflow_q'],
                "po_bona": daily['po_bona'],
                "po_bonb": daily['po_bonb'],
                "vol_bona": daily['vol_bona'],
                "vol_bonb": daily['vol_bonb'],
                "bendungan_id": daily['pos_id']
            }
            rc = Rencana.query.filter(
                                    Rencana.sampling == daily['waktu'],
                                    Rencana.bendungan_id == daily['pos_id']
                                ).first()
            if rc:
                # print(f"Updating rencana {daily['waktu']} for id {daily['pos_id']}")
                for key, value in obj_dict.items():
                    setattr(rc, key, value)
            else:
                # print(f"Inserting rencana {daily['waktu']} for id {daily['pos_id']}")
                rencana = Rencana(**obj_dict)
                db.session.add(rencana)
            db.session.commit()
        except Exception as e:
            print(f"-- Error Rencana : {type(e)}")
            db.session.rollback()
    mycursor.close()


@app.cli.command()
def import_master():
    print("Disabled")
    return

    print("Importing Bendungan")
    all_waduk = custom_query(mycursor, 'agent', limit=None)
    for waduk in all_waduk:
        try:
            waduk_name = waduk['AgentName'].replace('.', '_').lower()
            waduk_name = waduk_name.replace(' ', '_').lower()
            bend_id = waduk["AgentID"]
            obj_dict = {
                "id": waduk["AgentID"],
                "nama": waduk_name,
                "ll": waduk["ll"],
                "muka_air_min": waduk["CriticalLower"],
                "muka_air_normal": waduk["Normal"],
                "muka_air_max": waduk["SiagaUpper"],
                "sedimen": waduk["Sedimen"],
                "bts_elev_awas": waduk["bts_elev_awas"],
                "bts_elev_siaga": waduk["bts_elev_siaga"],
                "bts_elev_waspada": waduk["bts_elev_waspada"],
                "lbi": waduk["lbi"],
                "volume": waduk["volume"],
                "lengkung_kapasitas": waduk["lengkung_kapasitas"],
                "elev_puncak": waduk["elev_puncak"],
                "kab": waduk["kab"],
                "vn1_panjang_saluran": waduk["vn1_panjang_saluran"],
                "vn2_panjang_saluran": waduk["vn2_panjang_saluran"],
                "vn3_panjang_saluran": waduk["vn3_panjang_saluran"],
                "vn1_q_limit": waduk["vn_q1_limit"],
                "vn2_q_limit": waduk["vn_q2_limit"],
                "vn3_q_limit": waduk["vn_q3_limit"],
                "vn1_tin_limit": waduk["vn_tin1_limit"],
                "vn2_tin_limit": waduk["vn_tin2_limit"],
                "vn3_tin_limit": waduk["vn_tin3_limit"]
            }
            bend = Bendungan.query.get(waduk['AgentID'])
            if bend:
                print(f"Updating bendungan {waduk_name}")
                for key, value in obj_dict.items():
                    setattr(bend, key, value)
            else:
                print(f"Inserting bendungan {waduk_name}")
                new_bend = Bendungan(**obj_dict)
                db.session.add(new_bend)
                db.session.flush()
            db.session.commit()

            insert_assets(waduk_name, bend_id)
            insert_user(waduk_name, bend_id)
            insert_kegiatan(waduk_name, bend_id)
            insert_kerusakan(waduk_name, bend_id)
            insert_alert(bend_id)
            insert_chterkini(bend_id)
        except Exception as e:
            print(f"--Error Bendungan : {e}")
            db.session.rollback()

    print("Importing Embung")
    all_embung = custom_query(mycursor, 'embung', limit=None)
    for embung in all_embung:
        try:
            obj_dict = {
                "id": embung["id"],
                "nama": embung["nama"],
                "jenis": embung["jenis"],
                "desa": embung["desa"],
                "kec": embung["kec"],
                "kab": embung["kab"],
                # "ll": embung["ll"],
                "is_verified": embung['is_verified'],
                "sumber_air": embung["sumber_air"],
                "tampungan": embung["tampungan"],
                "debit": embung["debit"],
                "pipa_transmisi": embung["pipa_transmisi"],
                "saluran_transmisi": embung["saluran_transmisi"],
                "air_baku": embung["air_baku"],
                "irigasi": embung["irigasi"],
                "c_user": embung["cuser"],
                "c_date": embung["cdate"],
                "m_user": embung["muser"],
                "m_date": embung["mdate"]
            }
            emb = Embung.query.get(embung['id'])
            if emb:
                print(f"Updating embung {embung['nama']}")
                for key, value in obj_dict.items():
                    setattr(emb, key, value)
            else:
                print(f"Inserting embung {embung['nama']}")
                new_emb = Embung(**obj_dict)
                db.session.add(new_emb)
            db.session.commit()
        except Exception as e:
            print(f"--Error Embung : {e}")
            db.session.rollback()

    print("Importing User")
    all_user = custom_query(mycursor, 'passwd', limit=None)
    for user in all_user:
        role = '1'
        if not user['table_name'] and user['username'] != "admin":
            role = '1'
            if user['is_admin'] == 3:
                role = '1'
            else:
                role = '4'

            try:
                obj_dict = {
                    "id": user['id'],
                    "username": user['username'],
                    "password": user['password'],
                    "role": role
                }
                usr = Users.query.get(user['id'])
                if usr:
                    print(f"Updating user {user['id']}")
                    for key, value in obj_dict.items():
                        setattr(usr, key, value)
                else:
                    print(f"Inserting user {user['id']}")
                    new_user = Users(**obj_dict)
                    db.session.add(new_user)
                db.session.commit()
            except Exception as e:
                print(f"--Error User : {e}")
                db.session.rollback()

    print("Importing Foto")
    all_foto = custom_query(mycursor, 'foto', limit=None)
    for foto in all_foto:
        try:
            obj_dict = {
                "id": foto["id"],
                "url": foto["filepath"],
                "keterangan": foto["keterangan"],
                "obj_type": foto["obj_type"],
                "obj_id": foto["obj_id"],
                "c_user": foto["cuser"],
                "c_date": foto["cdate"],
                "m_user": foto["muser"],
                "m_date": foto["mdate"]
            }
            photo = Foto.query.get(foto["id"])
            if photo:
                # print(f"Updating foto {foto['id']}")
                for key, value in obj_dict.items():
                    setattr(photo, key, value)
            else:
                # print(f"Inserting foto {foto['id']}")
                new_foto = Foto(**obj_dict)
                db.session.add(new_foto)
            db.session.commit()
        except Exception as e:
            print(f"--Error Foto : {e}")
            db.session.rollback()
    mycursor.close()


def insert_user(waduk_name, waduk_id):
    print("Importing User")
    user_info = custom_query(mycursor, 'passwd', {'table_name': waduk_name})
    try:
        obj_dict = {
            "id": user_info[0]['id'],
            "username": user_info[0]['username'],
            "password": user_info[0]['password'],
            "role": '2',
            "bendungan_id": waduk_id
        }
        usr = Users.query.get(user_info[0]['id'])
        if usr:
            # print(f"Updating user {user_info[0]['id']}")
            for key, value in obj_dict.items():
                setattr(usr, key, value)
        else:
            # print(f"Inserting user {user_info[0]['id']}")
            new_user = Users(**obj_dict)
            db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        print(f"--Error User : {e}")
        db.session.rollback()


def insert_kerusakan(waduk_name, waduk_id):
    print("Importing Kerusakan")
    mycursor.execute(f"SHOW columns FROM kerusakan")
    columns = [column[0] for column in mycursor.fetchall()]

    kerusakan_query = """SELECT * FROM kerusakan"""
    mycursor.execute(kerusakan_query + f" WHERE kerusakan.table_name='{waduk_name}'")

    all_kerusakan = res2array(mycursor.fetchall(), columns)
    for ker in all_kerusakan:
        mycursor.execute(f"SHOW columns FROM tanggapan1")
        columns = [column[0] for column in mycursor.fetchall()]
        mycursor.execute(f"SHOW columns FROM asset")
        ass_columns = [column[0] for column in mycursor.fetchall()]

        tanggapan_query = f"SELECT * FROM tanggapan1 WHERE kerusakan_id={ker['id']} ORDER BY id DESC LIMIT 1"
        mycursor.execute(tanggapan_query)
        tanggapan = res2array(mycursor.fetchall(), columns)

        asset_query = f"SELECT * FROM asset WHERE id={ker['asset_id']}"
        mycursor.execute(asset_query)
        asset = res2array(mycursor.fetchall(), ass_columns)
        try:
            obj_dict = {
                "id": ker['id'],
                "tgl_lapor": ker['cdate'],
                "uraian": ker['uraian'],
                "kategori": ker['kategori'],
                "bendungan_id": waduk_id,
                "asset_id": ker['asset_id'],
                "c_user": ker["cuser"],
                "c_date": ker["cdate"]
            }
            if tanggapan:
                obj_dict["tgl_tanggapan"] = tanggapan[0]['cdate']
                obj_dict["tanggapan"] = tanggapan[0]['uraian']
            if asset:
                obj_dict["komponen"] = asset[0]['kategori']

            kerusakan = Kerusakan.query.get(ker['id'])
            if kerusakan:
                # print(f"Updating kerusakan {ker['id']}")
                for key, value in obj_dict.items():
                    setattr(kerusakan, key, value)
            else:
                # print(f"Inserting kerusakan {ker['id']}")
                new_ker = Kerusakan(**obj_dict)
                db.session.add(new_ker)
            db.session.commit()
        except Exception as e:
            print(f"--Error Kerusakan : {e}")
            db.session.rollback()


def insert_kegiatan(waduk_name, waduk_id):
    print("Importing Kegiatan")
    mycursor.execute(f"SHOW columns FROM kegiatan")
    columns = [column[0] for column in mycursor.fetchall()]

    kegiatan_query = """SELECT kegiatan.*, foto.filepath AS filepath, foto.keterangan AS keterangan
                        FROM kegiatan LEFT JOIN foto ON kegiatan.id=foto.obj_id"""
    mycursor.execute(kegiatan_query + f" WHERE kegiatan.table_name='{waduk_name}'")

    all_kegiatan = res2array(mycursor.fetchall(), columns)
    for keg in all_kegiatan:
        try:
            obj_dict = {
                "id": keg['id'],
                "sampling": keg['sampling'],
                "petugas": keg['petugas'],
                "uraian": keg['uraian'],
                "foto_id": keg['foto_id'],
                "bendungan_id": waduk_id,
                "c_user": keg["cuser"],
                "c_date": keg["cdate"],
                "m_user": keg["muser"],
                "m_date": keg["mdate"]
            }
            kegiatan = Kegiatan.query.get(keg['id'])
            if kegiatan:
                # print(f"Updating kegiatan {keg['id']}")
                for key, value in obj_dict.items():
                    setattr(kegiatan, key, value)
            else:
                # print(f"Inserting kegiatan {keg['id']}")
                new_keg = Kegiatan(**obj_dict)
                db.session.add(new_keg)
            db.session.commit()
        except Exception as e:
            print(f"--Error Kegiatan : {e}")
            db.session.rollback()


def insert_assets(waduk_name, waduk_id):
    print("Importing Assets")
    mycursor.execute(f"SHOW columns FROM asset")
    columns = [column[0] for column in mycursor.fetchall()]

    kerusakan_query = """SELECT * FROM asset"""
    mycursor.execute(kerusakan_query + f" WHERE table_name='{waduk_name}'")
    all_asset = res2array(mycursor.fetchall(), columns)
    for asset in all_asset:
        try:
            obj_dict = {
                "id": asset['id'],
                "kategori": asset['kategori'],
                "nama": asset['nama'],
                "merk": asset['merk'],
                "model": asset['model'],
                "perolehan": asset['perolehan'],
                "nilai_perolehan": asset['nilai_perolehan'],
                "bmn": asset['bmn'],
                "bendungan_id": waduk_id,
                "c_user": asset["cuser"],
                "c_date": asset["cdate"]
            }
            bend_asset = Asset.query.get(asset['id'])
            if bend_asset:
                # print(f"Updating asset {asset['id']}")
                for key, value in obj_dict.items():
                    setattr(bend_asset, key, value)
            else:
                # print(f"Inserting asset {asset['id']}")
                new_emb = Asset(**obj_dict)
                db.session.add(new_emb)
            db.session.commit()
        except Exception as e:
            print(f"--Error Asset : {e}")
            db.session.rollback()


def insert_alert(bend_id):
    print("Importing Bendungan Alert")
    mycursor.execute(f"SHOW columns FROM bendung_alert")
    columns = [column[0] for column in mycursor.fetchall()]

    kerusakan_query = """SELECT * FROM bendung_alert"""
    mycursor.execute(kerusakan_query + f" WHERE bendungan_id='{bend_id}'")
    all_alert = res2array(mycursor.fetchall(), columns)
    for alert in all_alert:
        try:
            tanggal = alert['tanggall'].strftime("%Y-%m-%d")
            jam = str(alert['jam'])
            sampling = datetime.datetime.strptime(f"{tanggal} {jam}", "%Y-%m-%d %H:%M:%S")

            obj_dict = {
                "id": alert['id'],
                "sampling": sampling,
                "tma": alert['tmab'],
                "spillway_deb": alert['spillwayb_q'],
                "bendungan_id": bend_id
            }
            bend_alert = BendungAlert.query.get(alert['id'])
            if bend_alert:
                # print(f"Updating asset {asset['id']}")
                for key, value in obj_dict.items():
                    setattr(bend_alert, key, value)
            else:
                # print(f"Inserting asset {asset['id']}")
                new_alert = BendungAlert(**obj_dict)
                db.session.add(new_alert)
            db.session.commit()
        except Exception as e:
            print(f"--Error Alert : {e}")
            db.session.rollback()


def insert_chterkini(bend_id):
    print("Importing Curah Hujan Terkini")
    mycursor.execute(f"SHOW columns FROM curahhujan_terkini")
    columns = [column[0] for column in mycursor.fetchall()]

    kerusakan_query = """SELECT * FROM curahhujan_terkini"""
    mycursor.execute(kerusakan_query + f" WHERE bendungan_id='{bend_id}'")
    all_cht = res2array(mycursor.fetchall(), columns)
    for cht in all_cht:
        try:
            tanggal = cht['tanggall'].strftime("%Y-%m-%d")
            jam = str(cht['jam'])
            sampling = datetime.datetime.strptime(f"{tanggal} {jam}", "%Y-%m-%d %H:%M:%S")

            obj_dict = {
                "id": cht['id'],
                "sampling": sampling,
                "ch": cht['ch_terkini'],
                "bendungan_id": bend_id
            }
            alert = CurahHujanTerkini.query.get(cht['id'])
            if alert:
                # print(f"Updating asset {asset['id']}")
                for key, value in obj_dict.items():
                    setattr(alert, key, value)
            else:
                # print(f"Inserting asset {asset['id']}")
                new_alert = CurahHujanTerkini(**obj_dict)
                db.session.add(new_alert)
            db.session.commit()
        except Exception as e:
            print(f"--Error Terkini : {e}")
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
    return res2array(result, columns)


def res2array(result, columns):
    results = []
    for res in result:
        results.append(dict(zip(columns, res)))
    return results
