from flask import Blueprint, request, render_template, redirect, flash
from flask import Response, url_for, jsonify
from flask_login import login_required
from sqlalchemy import and_
from upb_app.helper import to_date
from upb_app.models import Bendungan, Rencana, wil_sungai
from upb_app import db, admin_only
import datetime
import calendar
import csv
import io

from upb_app.admin import bp
# bp = Blueprint('rtow', __name__)


@bp.route('/bendungan/rtow')
@login_required
@admin_only
def rtow():
    sampling = request.values.get('sampling')
    sampling = datetime.datetime.strptime(sampling, "%Y-%m-%d") if sampling else datetime.datetime.now()

    year = (sampling.year) if sampling.month < 11 else sampling.year + 1
    start = datetime.datetime.strptime(f"{year - 1}-11-01", "%Y-%m-%d")
    end = datetime.datetime.strptime(f"{year}-10-31", "%Y-%m-%d")

    bends = Bendungan.query.all()
    rencana = Rencana.query.filter(
                            and_(
                                Rencana.sampling >= start,
                                Rencana.sampling <= end),
                            ).order_by(Rencana.sampling).all()
    rencana_s = {}
    for bend in bends:
        rencana_s[bend.id] = []
    for ren in rencana:
        rencana_s[ren.bendungan_id].append(ren)

    rtow = {
        '1': {
            'date_list': [],
            'data': {}
        },
        '2': {
            'date_list': [],
            'data': {}
        },
        '3': {
            'date_list': [],
            'data': {}
        }
    }
    for bend in bends:
        temp = {}
        for ren in rencana_s[bend.id]:
            index = ren.sampling.strftime('%d %b %y')
            last_day = calendar.monthrange(ren.sampling.year, ren.sampling.month)[1]

            if sampling.year >= 2020 and bend.wil_sungai in ['2', '3']:
                if ren.sampling.day in [10, 20, last_day]:
                    temp[index] = ren
                    if index not in rtow[bend.wil_sungai]['date_list']:
                        rtow[bend.wil_sungai]['date_list'].append(index)
            elif sampling.year >= 2019 and ren.sampling.day in [15, last_day]:
                temp[index] = ren
                if index not in rtow[bend.wil_sungai]['date_list']:
                    rtow[bend.wil_sungai]['date_list'].append(index)
            elif sampling.year <= 2018 and ren.sampling.day in [1, 16]:
                temp[index] = ren
                if index not in rtow[bend.wil_sungai]['date_list']:
                    rtow[bend.wil_sungai]['date_list'].append(index)

        rtow[bend.wil_sungai]['data'][bend.id] = {
            "bend": bend,
            "data": temp
        }

    return render_template('rencana/index.html',
                            sampling=sampling,
                            rtow=rtow,
                            wil_sungai=wil_sungai,
                            year=year)


@bp.route('/bendungan/<bendungan_id>/rtow/export', methods=['GET'])
@login_required
@admin_only
def rtow_exports(bendungan_id):
    sampling = datetime.datetime.strptime("2019-01-01", "%Y-%m-%d")
    start = datetime.datetime.strptime(f"{sampling.year -1}-11-01", "%Y-%m-%d")
    end = datetime.datetime.strptime(f"{sampling.year}-10-31", "%Y-%m-%d")

    bend = Bendungan.query.get(bendungan_id)
    rencana = Rencana.query.filter(
                            and_(
                                Rencana.sampling >= start,
                                Rencana.sampling <= end),
                            Rencana.bendungan_id == bendungan_id
                            ).order_by(Rencana.sampling).all()

    data = []
    for ren in rencana:
        # index = ren.sampling.strftime('%d %b %y')
        if ren.sampling.day == 15 or ren.sampling.day == calendar.monthrange(ren.sampling.year, ren.sampling.month)[1]:
            data.append(ren)
    pre_csv = [[bend.nama]]
    pre_csv.append(['waktu', 'po_tma', 'po_vol', 'po_outflow_q', 'po_inflow_q', 'po_bona', 'po_bonb', 'vol_bona', 'vol_bonb'])
    for d in data:
        pre_csv.append([
            d.sampling.strftime("%Y-%m-%d"),
            d.po_tma or None,
            d.po_vol or None,
            d.po_outflow_deb or None,
            d.po_inflow_deb or None,
            d.po_bona or None,
            d.po_bonb or None,
            d.vol_bona or None,
            d.vol_bonb or None
        ])
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    for l in pre_csv:
        writer.writerow(l)
    output.seek(0)

    return Response(output,
                    mimetype="text/csv",
                    headers={
                        "Content-Disposition": f"attachment;filename={bend.nama}.csv"
                    })


@bp.route('/bendungan/<bendungan_id>/rtow/import', methods=['GET', 'POST'])
@login_required
@admin_only
def rtow_imports(bendungan_id):
    bend = Bendungan.query.get(bendungan_id)

    if request.method == "POST":
        upload = request.files['upload'].read().decode("utf-8")
        print(upload)
        raw = upload.splitlines()
        seps = "\t_;_,_|".split('_')
        sep = None

        for s in seps:
            length = len(raw[1].split(s))
            if length > 5:
                sep = s

        data = []
        for r in raw[:len(raw)-1]:
            data.append(r.split(sep))

        if not data:
            flash(f"File Kosong", 'danger')
            return redirect(url_for('admin.rtow_imports', bendungan_id=bendungan_id))

        rtow_upload(data, bendungan_id)
        return redirect(url_for('admin.rtow'))

    return render_template('rencana/import.html',
                            bend=bend)


@bp.route('/bendungan/rtow/update', methods=['POST'])  # @login_required  # @admin_only
def rtow_update():
    pk = request.values.get('pk')
    attr = request.values.get('name')
    val = request.values.get('value')
    row = Rencana.query.get(pk)
    setattr(row, attr, val)
    db.session.commit()

    result = {
        "name": attr,
        "pk": pk,
        "value": val
    }
    return jsonify(result)


def rtow_upload(data, bend_id):
    columns = [col.replace('q', 'deb') for col in data[1]]
    for row in data[2:]:
        sampling = to_date(row[0])
        rencana = Rencana.query.filter(
                                    Rencana.sampling == sampling,
                                    Rencana.bendungan_id == bend_id
                                ).first()
        if not rencana:
            rencana = Rencana(sampling=sampling, bendungan_id=bend_id)
            db.session.add(rencana)

        for i, col in enumerate(columns[1:]):
            if row[i+1]:
                setattr(rencana, col, float(row[i+1].replace(',', '.')))

    try:
        db.session.commit()
        flash('RTOW berhasil ditambahkan !', 'success')
    except Exception as e:
        db.session.rollback()
        print(e)
        flash(f"RTOW gagal ditambahkan", 'danger')
