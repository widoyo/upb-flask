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
from app.models import Bendungan, Embung, Rencana, Users, Asset
from app.models import Kerusakan, Kegiatan, Foto
from app.models import ManualDaily, ManualTma, ManualVnotch, ManualPiezo

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
    waduk_daily = custom_query(mycursor, 'waduk_daily', limit=None)
    for daily in waduk_daily:
        print(f"Inserting data {daily['id']} at {daily['waktu']}")
        # Manual Daily
        try:
            manual_daily = ManualDaily(
                sampling=daily['waktu'],
                ch=daily['curahhujan'],
                inflow_vol=daily['inflow_v'],
                inflow_deb=daily['inflow_q'],
                outflow_vol=daily['outflow_v'],
                outflow_deb=daily['outflow_q'],
                spillway_vol=daily['spillway_v'],
                spillway_deb=daily['spillway_q'],
                bendungan_id=daily['pos_id']
            )
            db.session.add(manual_daily)
            db.session.commit()
        except Exception as e:
            print(f"-- Error Daily : {type(e)}")
            db.session.rollback()
        # TMA
        try:
            manual_tma6 = ManualTma(
                sampling=daily['waktu'].replace(hour=6),
                bendungan_id=daily['pos_id'],
                tma=daily['tma6'],
                vol=daily['vol6']
            )
            db.session.add(manual_tma6)
            db.session.commit()
        except Exception as e:
            print(f"-- Error TMA6 : {type(e)}")
            db.session.rollback()
        try:
            manual_tma12 = ManualTma(
                sampling=daily['waktu'].replace(hour=12),
                bendungan_id=daily['pos_id'],
                tma=daily['tma12'],
                vol=daily['vol12']
            )
            db.session.add(manual_tma12)
            db.session.commit()
        except Exception as e:
            print(f"-- Error TMA12 : {type(e)}")
            db.session.rollback()
        try:
            manual_tma18 = ManualTma(
                sampling=daily['waktu'].replace(hour=18),
                bendungan_id=daily['pos_id'],
                tma=daily['tma18'],
                vol=daily['vol18']
            )
            db.session.add(manual_tma18)
            db.session.commit()
        except Exception as e:
            print(f"-- Error TMA18 : {type(e)}")
            db.session.rollback()
        # VNotch
        try:
            manual_vnotch = ManualVnotch(
                sampling=daily['waktu'],
                vn_tma=daily['vnotch_tin'],
                vn_deb=daily['vnotch_q'],
                vn1_tma=daily['vnotch_tin1'],
                vn1_deb=daily['vnotch_q1'],
                vn2_tma=daily['vnotch_tin2'],
                vn2_deb=daily['vnotch_q2'],
                vn3_tma=daily['vnotch_tin3'],
                vn3_deb=daily['vnotch_q3'],
                bendungan_id=daily['pos_id']
            )
            db.session.add(manual_vnotch)
            db.session.commit()
        except Exception as e:
            print(f"-- Error VNotch : {type(e)}")
            db.session.rollback()
        # Piezo
        try:
            manual_piezo = ManualPiezo(
                sampling=daily['waktu'],
                p1a=daily['a1'],
                p1b=daily['b1'],
                p1c=daily['c1'],
                p2a=daily['a2'],
                p2b=daily['b2'],
                p2c=daily['c2'],
                p3a=daily['a3'],
                p3b=daily['b3'],
                p3c=daily['c3'],
                p4a=daily['a4'],
                p4b=daily['b4'],
                p4c=daily['c4'],
                p5a=daily['a5'],
                p5b=daily['b5'],
                p5c=daily['c5'],
                bendungan_id=daily['pos_id']
            )
            db.session.add(manual_piezo)
            db.session.commit()
        except Exception as e:
            print(f"-- Error Piezo : {type(e)}")
            db.session.rollback()
        # RTOW
        try:
            rencana = Rencana(
                sampling=daily['waktu'],
                po_tma=daily['po_tma'],
                po_vol=daily['po_vol'],
                po_inflow_vol=daily['po_inflow_v'],
                po_inflow_deb=daily['po_inflow_q'],
                po_outflow_vol=daily['po_outflow_v'],
                po_outflow_deb=daily['po_outflow_q'],
                po_bona=daily['po_bona'],
                po_bonb=daily['po_bonb'],
                vol_bona=daily['vol_bona'],
                vol_bonb=daily['vol_bonb'],
                bendungan_id=daily['pos_id']
            )
            db.session.add(rencana)
            db.session.commit()
        except Exception as e:
            print(f"-- Error Rencana : {type(e)}")
            db.session.rollback()
    mycursor.close()


@app.cli.command()
def import_master():
    print("Importing Bendungan")
    all_waduk = custom_query(mycursor, 'agent', limit=None)
    for waduk in all_waduk:
        try:
            waduk_name = waduk['AgentName'].replace('.', '_').lower()
            print(f"Inserting data {waduk_name}")
            new_bend = Bendungan(
                id=waduk["AgentID"],
                nama=waduk_name,
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
            db.session.flush()
            db.session.commit()
            insert_assets(waduk_name, new_bend.id)
            insert_user(waduk_name, new_bend.id)
            insert_kegiatan(waduk_name, new_bend.id)
            insert_kerusakan(waduk_name, new_bend.id)
        except Exception as e:
            print(f"Error Bendungan : {e}")
            db.session.rollback()

    print("Importing Embung")
    all_embung = custom_query(mycursor, 'embung', limit=None)
    for embung in all_embung:
        try:
            print(f"Inserting data {embung['nama']}")
            new_emb = Embung(
                id=embung["id"],
                nama=embung["nama"],
                jenis=embung["jenis"],
                desa=embung["desa"],
                kec=embung["kec"],
                kab=embung["kab"],
                ll=embung["ll"],
                is_verified=embung['is_verified'],
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
            print(f"Error Embung : {e}")
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
                new_user = Users(
                    id=user['id'],
                    username=user['username'],
                    password=user['password'],
                    role=role
                )
                db.session.add(new_user)
                db.session.commit()
            except Exception as e:
                print(f"Error User : {e}")
                db.session.rollback()

    print("Importing Foto")
    all_foto = custom_query(mycursor, 'foto', limit=None)
    for foto in all_foto:
        try:
            new_foto = Foto(
                id=foto["id"],
                url=foto["filepath"],
                keterangan=foto["keterangan"],
                obj_type=foto["obj_type"],
                obj_id=foto["obj_id"],
                c_user=foto["cuser"],
                c_date=foto["cdate"],
                m_user=foto["muser"],
                m_date=foto["mdate"]
            )
            db.session.add(new_foto)
            db.session.commit()
        except Exception as e:
            print(f"Error Foto : {e}")
            db.session.rollback()
    mycursor.close()


def insert_user(waduk_name, waduk_id):
    user_info = custom_query(mycursor, 'passwd', {'table_name': waduk_name})
    try:
        new_user = Users(
            id=user_info[0]['id'],
            username=user_info[0]['username'],
            password=user_info[0]['password'],
            role='2',
            bendungan_id=waduk_id
        )
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        print(f"Error User : {e}")
        db.session.rollback()


def insert_kerusakan(waduk_name, waduk_id):
    mycursor.execute(f"SHOW columns FROM kerusakan")
    columns = [column[0] for column in mycursor.fetchall()]

    kerusakan_query = """SELECT kerusakan.*,
                            asset.kategori AS komponen
                        FROM kerusakan
                            LEFT JOIN asset ON kerusakan.asset_id=asset.id"""
    mycursor.execute(kerusakan_query + f" WHERE kerusakan.table_name='{waduk_name}'")

    all_kerusakan = res2array(mycursor.fetchall(), columns)
    for ker in all_kerusakan:
        mycursor.execute(f"SHOW columns FROM tanggapan1")
        columns = [column[0] for column in mycursor.fetchall()]

        tanggapan_query = f"SELECT * FROM tanggapan1 WHERE kerusakan_id={ker['id']} ORDER BY id DESC LIMIT 1"
        mycursor.execute(tanggapan_query)
        tanggapan = res2array(mycursor.fetchall(), columns)
        try:
            new_ker = Kerusakan(
                id=ker['id'],
                tgl_lapor=ker['cdate'],
                uraian=ker['uraian'],
                kategori=ker['kategori'],
                komponen=ker['komponen'],
                tgl_tanggapan=tanggapan[0]['cdate'],
                tanggapan=tanggapan[0]['uraian'],
                bendungan_id=waduk_id,
                asset_id=ker['asset_id'],
                c_user=ker["cuser"],
                c_date=ker["cdate"]
            )
            db.session.add(new_ker)
            db.session.commit()
        except Exception as e:
            print(f"Error Kerusakan : {e}")
            db.session.rollback()


def insert_kegiatan(waduk_name, waduk_id):
    mycursor.execute(f"SHOW columns FROM kegiatan")
    columns = [column[0] for column in mycursor.fetchall()]

    kegiatan_query = """SELECT kegiatan.*, foto.filepath AS filepath, foto.keterangan AS keterangan
                        FROM kegiatan LEFT JOIN foto ON kegiatan.id=foto.obj_id"""
    mycursor.execute(kegiatan_query + f" WHERE kegiatan.table_name='{waduk_name}'")

    all_kegiatan = res2array(mycursor.fetchall(), columns)
    for keg in all_kegiatan:
        try:
            new_keg = Kegiatan(
                # id=keg['id'],
                sampling=keg['sampling'],
                petugas=keg['petugas'],
                uraian=keg['uraian'],
                foto_id=keg['foto_id'],
                bendungan_id=waduk_id,
                c_user=keg["cuser"],
                c_date=keg["cdate"],
                m_user=keg["muser"],
                m_date=keg["mdate"]
            )
            db.session.add(new_keg)
            db.session.commit()
        except Exception as e:
            print(f"Error Kegiatan : {e}")
            db.session.rollback()


def insert_assets(waduk_name, waduk_id):
    mycursor.execute(f"SHOW columns FROM asset")
    columns = [column[0] for column in mycursor.fetchall()]

    kerusakan_query = """SELECT * FROM asset"""
    mycursor.execute(kerusakan_query + f" WHERE table_name='{waduk_name}'")
    all_asset = res2array(mycursor.fetchall(), columns)
    for asset in all_asset:
        try:
            pprint(waduk_name)
            new_emb = Asset(
                id=asset['id'],
                kategori=asset['kategori'],
                nama=asset['nama'],
                merk=asset['merk'],
                model=asset['model'],
                perolehan=asset['perolehan'],
                nilai_perolehan=asset['nilai_perolehan'],
                bmn=asset['bmn'],
                bendungan_id=waduk_id,
                c_user=asset["cuser"],
                c_date=asset["cdate"]
            )
            db.session.add(new_emb)
            db.session.commit()
        except Exception as e:
            print(f"Error Asset : {e}")
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
