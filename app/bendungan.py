from flask import Blueprint, render_template
from app.models import Bendungan
import datetime

bp = Blueprint('bendungan', __name__)


@bp.route('/')
def index():
    ''' Home Bendungan '''
    return render_template('bendungan/index.html')


@bp.route('/<lokasi_id>', methods=['GET', 'POST'])
def tma(lokasi_id):
    pos = Bendungan.query.get(lokasi_id)

    return render_template('bendungan/info.html', waduk=pos)


@bp.route('/<lokasi_id>/operasi', methods=['GET', 'POST'])
def operasi(lokasi_id):
    pos = Bendungan.query.get(lokasi_id)
    sampling = datetime.datetime.now()

    return render_template('bendungan/operasi.html',
                            waduk=pos,
                            sampling=sampling,
                            operasi={})


@bp.route('/<lokasi_id>/vnotch', methods=['GET', 'POST'])
def vnotch(lokasi_id):
    pos = Bendungan.query.get(lokasi_id)
    sampling = datetime.datetime.now()

    return render_template('bendungan/vnotch.html',
                            waduk=pos,
                            sampling=sampling,
                            vnotch={})


@bp.route('/<lokasi_id>/piezo', methods=['GET', 'POST'])
def piezo(lokasi_id):
    pos = Bendungan.query.get(lokasi_id)
    sampling = datetime.datetime.now()

    return render_template('bendungan/piezo.html',
                            waduk=pos,
                            sampling=sampling,
                            piezo={})
