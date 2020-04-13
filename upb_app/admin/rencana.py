from flask import Blueprint, request, render_template, redirect, flash
from flask import Response, url_for, jsonify
from flask_login import login_required
from sqlalchemy import and_
from upb_app.models import Bendungan, Rencana
from upb_app import db, admin_only
import datetime
import calendar
import csv
import io

from upb_app.admin import bp
# bp = Blueprint('rtow', __name__)


@bp.route('/rtow')
@login_required
@admin_only
def rtow():
    sampling = request.values.get('sampling')
    sampling = datetime.datetime.strptime(sampling, "%Y-%m-%d") if sampling else datetime.datetime.now()
    start = datetime.datetime.strptime(f"{sampling.year -1}-11-01", "%Y-%m-%d")
    end = datetime.datetime.strptime(f"{sampling.year}-10-31", "%Y-%m-%d")

    bends = Bendungan.query.all()
    rencana = Rencana.query.filter(
                            and_(
                                Rencana.sampling >= start,
                                Rencana.sampling <= end)
                            ).order_by(Rencana.sampling).all()

    rtow = {}
    date_list = []
    for bend in bends:
        rtow[bend.id] = {
            "bend": bend,
            "data": {}
        }
    for ren in rencana:
        index = ren.sampling.strftime('%d %b %y')
        if sampling.year <= 2018 and ren.sampling.day in [1, 16]:
            rtow[ren.bendungan_id]['data'][index] = ren
            if index not in date_list:
                date_list.append(index)
        elif sampling.year >= 2019:
            if ren.sampling.day == 15 or ren.sampling.day == calendar.monthrange(ren.sampling.year, ren.sampling.month)[1]:
                rtow[ren.bendungan_id]['data'][index] = ren
                if index not in date_list:
                    date_list.append(index)

    return render_template('rencana/index.html',
                            sampling=sampling,
                            rtow=rtow,
                            date_list=date_list)


@bp.route('/rtow/<bendungan_id>/export', methods=['GET'])
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


@bp.route('/rtow/<bendungan_id>/import', methods=['GET', 'POST'])
@login_required
@admin_only
def rtow_imports(bendungan_id):
    bend = Bendungan.query.get(bendungan_id)

    if request.method == "POST":
        upload = request.files['upload'].read().decode("utf-8")
        print(upload)
        raw = upload.split('\r\n')
        data = []
        for r in raw[:len(raw)-1]:
            data.append(r.split('\t'))

        if not data:
            flash(f"File Kosong", 'danger')
            return redirect(url_for('admin.rtow_imports', bendungan_id=bendungan_id))

        rtow_upload(data, bendungan_id)
        return redirect(url_for('admin.rtow'))

    return render_template('rencana/import.html',
                            bend=bend)


@bp.route('/rtow/update', methods=['POST'])  # @login_required  # @admin_only
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
    for row in data[2:]:
        columns = ['sampling', 'po_tma', 'po_vol', 'po_outflow_deb', 'po_inflow_deb', 'po_bona', 'po_bonb', 'vol_bona', 'vol_bonb']
        sampling = datetime.datetime.strptime(row[0], "%Y-%m-%d")
        rencana = Rencana.query.filter(
                                    Rencana.sampling == sampling,
                                    Rencana.bendungan_id == bend_id
                                ).first()
        if not rencana:
            rencana = Rencana(sampling=sampling, bendungan_id=bend_id)
            db.session.add(rencana)

        for i, col in enumerate(columns[1:]):
            if row[i+1]:
                setattr(rencana, col, float(row[i+1]))

    try:
        db.session.commit()
        flash('RTOW berhasil ditambahkan !', 'success')
    except Exception as e:
        db.session.rollback()
        print(e)
        flash(f"RTOW gagal ditambahkan", 'danger')
