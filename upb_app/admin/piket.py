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
                            sampling=sampling,
                            now=now,
                            bend=bend,
                            reports=reports,
                            petugas=petugas)


@bp.route('/bendungan/<bendungan_id>/piket/banjir', methods=['POST'])
@login_required  # @petugas_only
@role_check
def piket_banjir_vnotch(bendungan_id):
    form = AddPiketBanjir()
    # print(form.vn1_tma.data)
    # if form.validate_on_submit():
    #     try:
    #         obj_dict = {
    #             'sampling': form.sampling.data,
    #             'vn1_tma': form.vn1_tma.data,
    #             'vn1_deb': form.vn1_deb.data,
    #             'vn2_tma': form.vn2_tma.data,
    #             'vn2_deb': form.vn2_deb.data,
    #             'vn3_tma': form.vn3_tma.data,
    #             'vn3_deb': form.vn3_deb.data,
    #             'bendungan_id': bendungan_id
    #         }
    #         vn = "ManualVnotch.query.filter(
    #                                     ManualVnotch.sampling == obj_dict['sampling'],
    #                                     ManualVnotch.bendungan_id == obj_dict['bendungan_id']
    #                                 ).first()"
    #         if vn:
    #             for key, value in obj_dict.items():
    #                 setattr(vn, key, value)
    #         else:
    #             vnotch = ManualVnotch(**obj_dict)
    #             db.session.add(vnotch)
    #         db.session.commit()
    #         flash('Tambah Vnotch berhasil !', 'success')
    #     except Exception as e:
    #         db.session.rollback()
    #         print(f"Piket Banjir Error : {e.__class__.__name__}")
    #         flash(f"Terjadi kesalahan saat mencoba menyimpan form Piket Banjir", 'danger')

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
