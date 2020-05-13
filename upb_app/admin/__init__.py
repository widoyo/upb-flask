from flask import Blueprint, jsonify, request, render_template, redirect, url_for
from flask_login import login_required
from upb_app.models import Bendungan, Embung, wil_sungai
from upb_app import db
from upb_app import admin_only
from sqlalchemy import and_
import datetime

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
    ''' Home Bendungan '''
    embung = Embung.query.filter(Embung.is_verified == '1').order_by(Embung.id).all()

    embung_a = []
    embung_b = []
    for e in embung:
        if e.jenis == 'a':
            embung_a.append(e)
        elif e.jenis == 'b':
            embung_b.append(e)
    return render_template('embung/admin.html',
                            embung_a=embung_a,
                            embung_b=embung_b)


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


import upb_app.admin.keamanan
import upb_app.admin.kegiatan
import upb_app.admin.kinerja
import upb_app.admin.operasi
import upb_app.admin.petugas
import upb_app.admin.rencana
import upb_app.admin.users
