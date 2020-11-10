from flask import Blueprint, request, render_template, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from sqlalchemy import extract, and_
from psycopg2 import IntegrityError
from upb_app.helper import utc2wib, month_range, day_range
from upb_app.models import PiketBanjir, Bendungan, Petugas, wil_sungai
from upb_app.forms import AddPiketBanjir
from upb_app import db, petugas_only, role_check, admin_only
import datetime
import calendar

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
            piket_banjir = PiketBanjir.query.filter(
                                        PiketBanjir.sampling == obj_dict['sampling'],
                                        PiketBanjir.obj_type == 'bendungan',
                                        PiketBanjir.obj_id == obj_dict['obj_id']
                                    ).first()
            if piket_banjir:
                for key, value in obj_dict.items():
                    setattr(piket_banjir, key, value)
            else:
                pb_new = PiketBanjir(**obj_dict)
                db.session.add(pb_new)
            db.session.commit()
            flash('Laporan Piket Banjir berhasil ditambahkan !', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Piket Banjir Error : {e}")
            flash(f"Terjadi kesalahan saat mencoba menyimpan laporan Piket Banjir", 'danger')

    return redirect(url_for('admin.piket_bendungan', bendungan_id=bendungan_id))


@bp.route('/bendungan/keamanan/piket/update', methods=['POST'])  # @login_required
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


@bp.route('/bendungan/operasi/csv', methods=['GET'])
@login_required
@admin_only
def piket_banjir_csv():
    # waduk = Bendungan.query.order_by(Bendungan.wil_sungai, Bendungan.id).all()
    # sampling, end = day_range(request.values.get('sampling'))
    #
    # pre_csv = []
    # pre_csv.append(['Data Operasi Harian Bendungan'])
    # pre_csv.append([sampling.strftime("%d %B %Y")])
    # pre_csv.append([
    #     'no', 'nama','curahhujan','tma6','vol6','tma12','vol12','tma18','vol18',
    #     'inflow_q','intake_q','spillway_q','vnotch_tin1','vnotch_q1',
    #     'piezo_1a','piezo_1b','piezo_1c',
    #     'piezo_2a','piezo_2b','piezo_2c',
    #     'piezo_3a','piezo_3b','piezo_3c',
    #     'piezo_4a','piezo_4b','piezo_4c',
    #     'piezo_5a','piezo_5b','piezo_5c'
    # ])
    # count = 1
    # for w in waduk:
    #     daily = ManualDaily.query.filter(
    #                                 and_(
    #                                     ManualDaily.sampling >= sampling,
    #                                     ManualDaily.sampling <= end),
    #                                 ManualDaily.bendungan_id == w.id
    #                                 ).first()
    #     vnotch = ManualVnotch.query.filter(
    #                                 and_(
    #                                     ManualVnotch.sampling >= sampling,
    #                                     ManualVnotch.sampling <= end),
    #                                 ManualVnotch.bendungan_id == w.id
    #                                 ).first()
    #     tma = ManualTma.query.filter(
    #                                 and_(
    #                                     ManualTma.sampling >= sampling,
    #                                     ManualTma.sampling <= end),
    #                                 ManualTma.bendungan_id == w.id
    #                                 ).all()
    #     piezo = ManualPiezo.query.filter(
    #                                 and_(
    #                                     ManualPiezo.sampling >= sampling,
    #                                     ManualPiezo.sampling <= end),
    #                                 ManualPiezo.bendungan_id == w.id
    #                                 ).first()
    #
    #     tma_d = {
    #         '6': {
    #             'tma': None,
    #             'vol': None
    #         },
    #         '12': {
    #             'tma': None,
    #             'vol': None
    #         },
    #         '18': {
    #             'tma': None,
    #             'vol': None
    #         },
    #     }
    #     for t in tma:
    #         tma_d[f"{t.sampling.hour}"]['tma'] = None if not t.tma else round(t.tma, 2)
    #         tma_d[f"{t.sampling.hour}"]['vol'] = None if not t.vol else round(t.vol, 2)
    #
    #     pre_csv.append([
    #         count, w.name, None if not daily else daily.ch,
    #         tma_d['6']['tma'], tma_d['6']['vol'],
    #         tma_d['12']['tma'], tma_d['12']['vol'],
    #         tma_d['18']['tma'], tma_d['18']['vol'],
    #         None if not daily else daily.inflow_deb,
    #         None if not daily else daily.intake_deb,
    #         None if not daily else daily.spillway_deb,
    #         None if not vnotch else vnotch.vn1_tma,
    #         None if not vnotch else vnotch.vn1_deb,
    #         None if not piezo else piezo.p1a, None if not piezo else piezo.p1b, None if not piezo else piezo.p1c,
    #         None if not piezo else piezo.p2a, None if not piezo else piezo.p2b, None if not piezo else piezo.p2c,
    #         None if not piezo else piezo.p3a, None if not piezo else piezo.p3b, None if not piezo else piezo.p3c,
    #         None if not piezo else piezo.p4a, None if not piezo else piezo.p4b, None if not piezo else piezo.p4c,
    #         None if not piezo else piezo.p5a, None if not piezo else piezo.p5b, None if not piezo else piezo.p5c
    #     ])
    #     count += 1
    # output = io.StringIO()
    # writer = csv.writer(output, delimiter='\t')
    # for l in pre_csv:
    #     writer.writerow(l)
    # output.seek(0)

    return "Hello"

    return Response(output,
                    mimetype="text/csv",
                    headers={
                        "Content-Disposition": f"attachment;filename=operasi_harian_bendungan-{sampling.strftime('%d %B %Y')}.csv"
                    })
