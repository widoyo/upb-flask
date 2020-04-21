from flask import Blueprint, jsonify, request, render_template, redirect, url_for
from flask_login import login_required
from upb_app.models import Bendungan, ManualDaily, ManualTma, ManualVnotch, wil_sungai
from upb_app import db
from sqlalchemy import and_
import datetime

bp = Blueprint('admin', __name__)


@bp.route('/bendungan')
@login_required
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

import upb_app.admin.keamanan
import upb_app.admin.kegiatan
import upb_app.admin.kinerja
import upb_app.admin.operasi
import upb_app.admin.petugas
import upb_app.admin.rencana
import upb_app.admin.users
