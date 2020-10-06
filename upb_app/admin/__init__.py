from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from flask_login import login_required
from upb_app.models import Bendungan, Embung, Users, KegiatanEmbung, Foto, wil_sungai
from upb_app import db
from upb_app import admin_only
from upb_app.helper import day_range
from sqlalchemy import and_
from telegram import Bot
import datetime

import paho.mqtt.client as mqtt

bp = Blueprint('admin', __name__)


@bp.route('/bendungan')
@login_required
@admin_only
def bendungan():
    ''' Home Bendungan '''
    waduk = Bendungan.query.order_by(Bendungan.wil_sungai, Bendungan.id).all()
    bends = {
        '1': {},
        '2': {},
        '3': {}
    }
    count = 1
    for w in waduk:
        bends[w.wil_sungai][count] = w
        count += 1
    return render_template('bendungan/admin.html',
                            bends=bends,
                            wil_sungai=wil_sungai)


@bp.route('/bendungan/update', methods=['POST'])  # @login_required
def bend_update():
    pk = request.values.get('pk')
    attr = request.values.get('name')
    val = request.values.get('value')
    row = Bendungan.query.get(pk)
    setattr(row, attr, val)
    db.session.commit()

    result = {
        "name": attr,
        "pk": pk,
        "value": val
    }
    return jsonify(result)


@bp.route('/embung')
@login_required
@admin_only
def embung():
    ''' Home Embung '''
    all_embung = Embung.query.order_by(Embung.is_verified.desc(), Embung.id).all()

    embung = []
    for e in all_embung:
        if e.jenis == 'a':
            embung.append(e)
        elif e.jenis == 'b':
            embung.append(e)
    return render_template('embung/admin.html',
                            embung=embung)


@bp.route('/embung/update', methods=['POST'])  # @login_required
def emb_update():
    pk = request.values.get('pk')
    attr = request.values.get('name')
    val = request.values.get('value')
    row = Embung.query.get(pk)
    setattr(row, attr, val)
    db.session.commit()

    result = {
        "name": attr,
        "pk": pk,
        "value": val
    }
    return jsonify(result)


@bp.route('/embung/<emb_id>/verify', methods=['POST'])  # @login_required
def embung_verify(emb_id):
    password = request.values.get('password')

    embung = Embung.query.get(emb_id)
    if embung:
        embung.is_verified = '1'
        username = embung.gen_username()
        user = Users.query.filter(Users.username == username).first()
        if not user:
            new_user = Users(
                username=username,
                role='3',
                embung_id=embung.id
            )
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.flush()
            db.session.commit()
        else:
            flash(f"Username sudah ada", 'danger')
            return redirect(url_for('admin.embung'))
        flash(f"Berhasil verifikasi dan tambah user untuk {embung.nama}", 'success')
    else:
        flash(f"Terjadi kesalahan saat mencoba menyimpan data", 'danger')

    return redirect(url_for('admin.embung'))


@bp.route('/embung/harian')
@login_required
@admin_only
def embung_harian():
    ''' Harian Embung '''
    sampling, end = day_range(request.values.get('sampling'))

    embung = Embung.query.filter(Embung.is_verified == '1').order_by(Embung.wil_sungai, Embung.id).all()
    kegiatan = KegiatanEmbung.query.filter(
                                KegiatanEmbung.sampling == sampling.strftime('%Y-%m-%d')
                            ).all()

    embung_a = {
        '1': {},
        '2': {},
        '3': {},
        '4': {}
    }
    embung_b = {
        '1': {},
        '2': {},
        '3': {},
        '4': {}
    }
    wilayah = wil_sungai
    wilayah['4'] = "Lain-Lain"
    count_a = 0
    count_b = 0
    for e in embung:
        if e.jenis == 'a':
            count_a += 1
            embung_a[e.wil_sungai or '4'][e.id] = {
                'embung': e,
                'kegiatan': [],
                'count': count_a
            }
        elif e.jenis == 'b':
            count_b += 1
            embung_b[e.wil_sungai or '4'][e.id] = {
                'embung': e,
                'kegiatan': [],
                'count': count_b
            }
    for keg in kegiatan:
        if keg.embung_id in embung_a[keg.embung.wil_sungai or '4']:
            embung_a[keg.embung.wil_sungai or '4'][keg.embung_id]['kegiatan'].append(keg)
        elif keg.embung_id in embung_b[keg.embung.wil_sungai or '4']:
            embung_b[keg.embung.wil_sungai or '4'][keg.embung_id]['kegiatan'].append(keg)
    return render_template('embung/harian.html',
                            sampling=sampling,
                            wil_sungai=wilayah,
                            embung_a=embung_a,
                            embung_b=embung_b)


@bp.route('/showcase/toggle', methods=['POST'])
@login_required
@admin_only
def showcase_toggle():
    ''' Home Embung '''
    foto_id = request.form.get('foto_id')

    foto = Foto.query.get(foto_id)
    if foto.showcase:
        foto.showcase = False
        msg = "hide"
    else:
        foto.showcase = True
        msg = "show"
    db.session.commit()

    return msg


@bp.route('/alert/button')
@login_required
@admin_only
def alert_button():
    ''' Return html with button to trigger alert notice '''
    return render_template('operasi/alert.html')


@bp.route('/alert/test')
@login_required
@admin_only
def alert_test():
    ''' Return html with button to trigger alert notice '''
    MQTT_HOST = "mqtt.bbws-bsolo.net"
    MQTT_PORT = 14983
    client = mqtt.Client("overseer")

    print("connecting to broker")
    client.connect(MQTT_HOST, port=MQTT_PORT)

    client.loop_start()
    print("sending alert")
    client.publish("alert/test", "ON")
    client.loop_stop()

    # send telegram
    try:
        desa = request.values.get('desa')
        with open('telegram_token.txt', 'r') as openfile:
            token = openfile.read()
        bot = Bot(token=token.strip())
        bot.sendMessage(chat_id='@ewsbbwspj', text=f"*Status AWAS bendungan Logung*\nSirine {desa} dibunyikan.", parse_mode='Markdown')
    except Exception as e:
        print(e)

    return redirect(url_for('admin.alert_button'))


import upb_app.admin.keamanan
import upb_app.admin.kegiatan
import upb_app.admin.kinerja
import upb_app.admin.operasi
import upb_app.admin.petugas
import upb_app.admin.rencana
import upb_app.admin.users
