from flask import Blueprint, render_template

bp = Blueprint('profile', __name__)


@bp.route('/wilayah-kerja')
def wil_ker():
    return render_template('about/wil_ker.html')


@bp.route('/struktur-organisasi')
def struktur_org():
    return render_template('about/struktur_org.html')


@bp.route('/kontak-kami')
def kontak():
    return render_template('about/kontak.html')
