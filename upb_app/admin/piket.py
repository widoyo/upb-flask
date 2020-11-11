from flask import Blueprint, request, render_template, redirect, url_for, jsonify, flash
from flask import Response
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from sqlalchemy import extract, and_
from psycopg2 import IntegrityError
from upb_app.helper import utc2wib, month_range, day_range, get_hari_tanggal
from upb_app.models import PiketBanjir, Bendungan, Petugas, wil_sungai
from upb_app.forms import AddPiketBanjir
from upb_app import db, petugas_only, role_check, admin_only
import datetime
import calendar
import csv
import io

from upb_app.admin import bp
# bp = Blueprint('keamanan', __name__)


@bp.route('/bendungan/piket')
@admin_only
def piket_index():
    waduk = Bendungan.query.order_by(Bendungan.wil_sungai, Bendungan.id).all()

    sampling, end = day_range(request.values.get('sampling'))
    data = {
        '1': [],
        '2': [],
        '3': []
    }
    count = 1
    for w in waduk:
        piket_banjir = PiketBanjir.query.filter(
                                        and_(
                                            PiketBanjir.sampling >= sampling,
                                            PiketBanjir.sampling <= end),
                                        PiketBanjir.obj_type == 'bendungan',
                                        PiketBanjir.obj_id == w.id
                                    ).first()

        data[w.wil_sungai].append({
            'no': count,
            'bendungan': w,
            'piket_banjir': piket_banjir or {}
        })
        count += 1

    return render_template('piket/index.html',
                            sampling=sampling,
                            bends=data,
                            wil_sungai=wil_sungai)


@bp.route('/bendungan/<bendungan_id>/piket')
@login_required  # @petugas_only
@role_check
def piket_bendungan(bendungan_id):
    bend = Bendungan.query.get(bendungan_id)

    sampling = request.values.get('sampling')
    now = utc2wib(datetime.datetime.now())
    sampling = sampling or now.strftime("%Y-%m-%d")
    start, end, days = month_range(sampling)
    # print(start, end, days)

    piket_banjir_query = PiketBanjir.query.filter(
                                        PiketBanjir.obj_type == 'bendungan',
                                        PiketBanjir.obj_id == bendungan_id,
                                        PiketBanjir.sampling.between(start, end)
                                    ).all()
    piket_banjir = {}
    for piket in piket_banjir_query:
        piket_banjir[piket.sampling] = piket

    reports = []
    relay = end - datetime.timedelta(hours=23)
    while True:
        if relay < start:
            break

        reports.append({
            'sampling': relay,
            'piket_banjir': piket_banjir[relay] if relay in piket_banjir else None
        })
        relay -= datetime.timedelta(days=1)

    sampling = datetime.datetime.strptime(sampling, "%Y-%m-%d")
    petugas = Petugas.query.filter(Petugas.bendungan_id==bendungan_id).all()

    return render_template('piket/bendungan.html',
                            csrf=generate_csrf(),
                            sampling=sampling,
                            now=now,
                            bend=bend,
                            reports=reports,
                            petugas=petugas)


@bp.route('/bendungan/<bendungan_id>/piket/banjir', methods=['POST'])
@login_required  # @petugas_only
@role_check
def piket_banjir_add(bendungan_id):
    bend = Bendungan.query.get(bendungan_id)
    form = AddPiketBanjir()
    print(form.data)

    if form.validate_on_submit():
        print("Validated")
        try:
            obj_dict = {
                'sampling': form.sampling.data,
                'cuaca': form.cuaca.data,
                'ch': form.curahhujan.data,
                'durasi': form.durasi.data,
                'tma': form.tma.data,
                'volume': form.volume.data,
                'spillway_tma': form.spillway_tma.data,
                'spillway_deb': form.spillway_deb.data,
                'kondisi': form.kondisi.data,
                'petugas_id': int(form.petugas_id.data),
                'obj_type': 'bendungan',
                'obj_id': bendungan_id
            }
            pb_new = PiketBanjir.query.filter(
                                        PiketBanjir.sampling == obj_dict['sampling'],
                                        PiketBanjir.obj_type == 'bendungan',
                                        PiketBanjir.obj_id == obj_dict['obj_id']
                                    ).first()
            if pb_new:
                for key, value in obj_dict.items():
                    setattr(pb_new, key, value)
            else:
                pb_new = PiketBanjir(**obj_dict)
                db.session.add(pb_new)
            db.session.commit()
            flash('Laporan Piket Banjir berhasil ditambahkan !', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Piket Banjir Error : {e}")
            flash(f"Terjadi kesalahan saat mencoba menyimpan laporan Piket Banjir", 'danger')

    sent = pb_new.cdate_wib.strftime("%H.%M")
    limpasan = "mengalami" if pb_new.spillway_tma else "tidak mengalami"
    notify = f"*LAPORAN PIKET*\n \
Bendungan {bend.name.split(' ')[1]}\n \
Pukul : {sent} WIB\n \
*1. Data Bendungan dan Waduk*\n \
Cuaca : {pb_new.cuaca.title()}\n \
Curah hujan saat ini : {pb_new.ch} mm\n  \
El. MA terkini : {pb_new.tma} m\n \
Volume terkini : {pb_new.volume} m3\n \
*2. Kondisi Spilway*\n \
Saat ini kondisi Spillway *{limpasan}* limpasan\n \
Ketinggian Limpasan : {pb_new.spillway_tma or '-'} cm\n \
Debit Limpasan      : {pb_new.spillway_deb or '-'} m3/dt\n \
*3. Kondisi visual bendungan : {pb_new.kondisi}*\n \
*4. Nama petugas piket*\n \
- {pb_new.petugas.nama}"
    flash(notify, 'notify')

    return redirect(url_for('admin.piket_bendungan', bendungan_id=bendungan_id))


@bp.route('/bendungan/piket/update', methods=['POST'])  # @login_required
def piket_banjir_update():
    pk = request.values.get('pk')
    attr = request.values.get('name')
    val = request.values.get('value')
    row = PiketBanjir.query.get(pk)
    setattr(row, attr, val)
    db.session.commit()

    result = {
        "name": attr,
        "pk": pk,
        "value": val
    }
    return jsonify(result)


@bp.route('/bendungan/piket/csv', methods=['GET'])
@login_required
@admin_only
def piket_banjir_csv():
    waduk = Bendungan.query.order_by(Bendungan.wil_sungai, Bendungan.id).all()
    sampling, end = day_range(request.values.get('sampling'))

    pre_csv = []
    pre_csv.append(['REKAPITULASI LAPORAN PIKET'])
    pre_csv.append(['PETUGAS UNIT PENGELOLA BENDUNGAN'])
    pre_csv.append(['BALAI BESAR WILAYAH SUNGAI BENGAWAN SOLO'])
    pre_csv.append(["Hari/Tanggal", get_hari_tanggal(sampling)])
    pre_csv.append(['Waktu', '20.35 WIB'])
    pre_csv.append([
        'No','Nama Bendungan','Cuaca Terkini','Curah Hujan Terkini (mm)','Durasi Hujan','Elevasi Normal (meter)','Volume Waduk Normal (Juta m3)','TMA Terkini (meter)','Volume Waduk Terkini (Juta m3)','Tinggi Limpasan Spillway (cm)','Debit Limpasan Spillway (m3/detik)','Tampungan Waduk Saat Ini (%)','Kondisi Visual Bendungan','Nama Petugas Piket'
    ])

    data = {
        '1': [],
        '2': [],
        '3': []
    }
    count = 1
    for w in waduk:
        piket_banjir = PiketBanjir.query.filter(
                                        and_(
                                            PiketBanjir.sampling >= sampling,
                                            PiketBanjir.sampling <= end),
                                        PiketBanjir.obj_type == 'bendungan',
                                        PiketBanjir.obj_id == w.id
                                    ).first()

        data[w.wil_sungai].append({
            'no': count,
            'bendungan': w,
            'piket_banjir': piket_banjir or {}
        })
        count += 1

    for wil, da in data.items():
        pre_csv.append([wil_sungai[wil]])
        for d in da:
            pre_csv.append([
                d['no'], d['bendungan'].name,
                None if not d['piket_banjir'] else d['piket_banjir'].cuaca.title(),
                None if not d['piket_banjir'] else d['piket_banjir'].ch,
                None if not d['piket_banjir'] else d['piket_banjir'].durasi,
                d['bendungan'].muka_air_normal,
                round(d['bendungan'].volume/1000000, 2),
                None if not d['piket_banjir'] else d['piket_banjir'].tma,
                None if not d['piket_banjir'] else round(d['piket_banjir'].volume/1000000, 2),
                None if not d['piket_banjir'] else d['piket_banjir'].spillway_tma,
                None if not d['piket_banjir'] else d['piket_banjir'].spillway_deb,
                None if not d['piket_banjir'] else d['piket_banjir'].volume_percent,
                None if not d['piket_banjir'] else d['piket_banjir'].kondisi,
                None if not d['piket_banjir'] else d['piket_banjir'].petugas.nama
            ])
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    for l in pre_csv:
        writer.writerow(l)
    output.seek(0)

    return Response(output,
                    mimetype="text/csv",
                    headers={
                        "Content-Disposition": f"attachment;filename=rekap_laporan_piket-{sampling.strftime('%d %B %Y')}.csv"
                    })
