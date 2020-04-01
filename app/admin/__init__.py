from flask import Blueprint, jsonify, request, render_template, redirect, url_for
from flask_login import login_required
from app.models import Bendungan, ManualDaily, ManualTma, ManualVnotch
from app import db
from sqlalchemy import and_
import datetime

bp = Blueprint('admin', __name__)


@bp.route('/bendungan')
@login_required
def bendungan():
    ''' Home Bendungan '''
    waduk = Bendungan.query.all()
    bends = {}
    for w in waduk:
        arr = w.nama.split('_')
        name = f"{arr[0].title()}.{arr[1].title()}"
        bends[name] = w
    return render_template('bendungan/admin.html',
                            bends=bends)


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

import app.admin.keamanan
import app.admin.kegiatan
import app.admin.kinerja
import app.admin.operasi
import app.admin.rencana
import app.admin.users
