import datetime
from urllib.parse import urlparse, urljoin
from flask import render_template, redirect, url_for, flash, request, abort, Blueprint
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import desc
from pytz import timezone

from app import app
from app.models import Rencana, Bendungan, Embung, ManualTma, ManualDaily
from app.forms import LoginForm

bp = Blueprint('about', __name__)


@app.route('/')
def index():
    ''' Index UPB '''
    today = datetime.datetime.utcnow().astimezone(timezone("Asia/Jakarta"))
    sampling = today
    if sampling.day < 15:
        sampling = sampling - datetime.timedelta(days=today.day)
    else:
        sampling.day = 15
    print(sampling)

    all_waduk = Bendungan.query.all()
    all_embung = Embung.query.filter(
                                Embung.is_verified == '1'
                            ).all()
    all_rencana = Rencana.query.filter(
                                Rencana.sampling == sampling
                            ).all()
    all_tma = ManualTma.query.filter(
                                ManualTma.sampling == f"{sampling.strftime('%Y-%m-%d')} 06:00:00"
                            ).all()
    all_daily = ManualDaily.query.filter(
                                ManualDaily.sampling == f"{sampling.strftime('%Y-%m-%d')} 00:00:00"
                            ).all()

    vol_potensi = round(sum([w.volume if w.volume else 0 for w in all_waduk]))
    vol_embung = round(sum([e.tampungan if e.tampungan else 0 for e in all_embung]))

    count = {
        'waduk': len(all_waduk),
        'embung': len(all_embung)
    }
    real = {
        'volume': 0,
        'inflow': 0,
        'outflow': 0
    }
    rtow = {
        'volume': 0,
        'inflow': 0,
        'outflow': 0
    }

    for t in all_tma:
        real['volume'] += t.vol if t.vol else 0
    for d in all_daily:
        real['inflow'] += d.inflow_vol if d.inflow_vol else 0
        real['outflow'] += d.outflow_vol if d.outflow_vol else 0
    for r in all_rencana:
        rtow['volume'] += r.po_vol if r.po_vol else 0
        rtow['inflow'] += r.po_inflow_vol if r.po_inflow_vol else 0
        rtow['outflow'] += r.po_outflow_vol if r.po_outflow_vol else 0

    return render_template('index.html',
                            vol_potensi=vol_potensi,
                            real=real,
                            rtow=rtow,
                            vol_embung=vol_embung,
                            tgl=today,
                            count=count,
                            title='Home')


@app.route('/map')
@login_required
def map():
    lokasis = Lokasi.query.all()
    return render_template('map.html', lokasis=lokasis)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username/Password')
            return redirect(url_for('index'))
        login_user(user, remember=form.remember_me.data)
        next = request.args.get('next')
        if not is_safe_url(next):
            return abort(400)
        return redirect(url_for('index'))
    return render_template('auth/login.html', title='Login', form=form)
