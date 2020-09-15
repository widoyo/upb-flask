from flask import Blueprint, render_template, request
from upb_app.helper import day_range
from upb_app.models import Bendungan, Petugas
from upb_app.models import ManualDaily, ManualTma, ManualVnotch, ManualPiezo
from upb_app.models import Kegiatan, Rencana, BendungAlert, CurahHujanTerkini, wil_sungai
from sqlalchemy import and_, desc, cast, Date, extract
from pprint import pprint
from pytz import timezone
import datetime
import calendar

bp = Blueprint('bendungan', __name__)


@bp.route('/', strict_slashes=False)
def index():
    ''' Home Bendungan '''
    waduk = Bendungan.query.order_by(Bendungan.wil_sungai, Bendungan.id).all()

    sampling, end = day_range(request.values.get('sampling'))
    data = {
        '1': [],
        '2': [],
        '3': []
    }
    count = 1
    for w in waduk:
        daily = ManualDaily.query.filter(
                                    and_(
                                        extract('month', ManualDaily.sampling) == sampling.month,
                                        extract('year', ManualDaily.sampling) == sampling.year,
                                        extract('day', ManualDaily.sampling) == sampling.day),
                                    ManualDaily.bendungan_id == w.id
                                    ).first()
        vnotch = ManualVnotch.query.filter(
                                    and_(
                                        extract('month', ManualVnotch.sampling) == sampling.month,
                                        extract('year', ManualVnotch.sampling) == sampling.year,
                                        extract('day', ManualVnotch.sampling) == sampling.day),
                                    ManualVnotch.bendungan_id == w.id
                                    ).first()
        tma = ManualTma.query.filter(
                                    and_(
                                        extract('month', ManualTma.sampling) == sampling.month,
                                        extract('year', ManualTma.sampling) == sampling.year,
                                        extract('day', ManualTma.sampling) == sampling.day),
                                    ManualTma.bendungan_id == w.id
                                    ).all()
        alert = BendungAlert.query.filter(and_(
                                        extract('month', BendungAlert.sampling) == sampling.month,
                                        extract('year', BendungAlert.sampling) == sampling.year,
                                        extract('day', BendungAlert.sampling) == sampling.day),
                                    BendungAlert.bendungan_id == w.id
                                    ).order_by(BendungAlert.sampling.desc()).all()
        ch_t = CurahHujanTerkini.query.filter(and_(
                                        extract('month', CurahHujanTerkini.sampling) == sampling.month,
                                        extract('year', CurahHujanTerkini.sampling) == sampling.year,
                                        extract('day', CurahHujanTerkini.sampling) == sampling.day),
                                    CurahHujanTerkini.bendungan_id == w.id
                                    ).order_by(CurahHujanTerkini.sampling.desc()).first()

        tma_d = {
            '6': None,
            '12': None,
            '18': None,
        }
        vol = None
        kondisi = ""
        flood = 0
        time = ""
        for t in tma:
            vol = t.vol/1000000 if t.vol else vol
            if t.tma:
                spill = t.tma - w.muka_air_normal
                if spill >= flood:
                    flood = spill
                    time = t.sampling.strftime("%H:%M:%S")
            tma_d[f"{t.sampling.hour}"] = None if not t.tma else "{:,.2f}".format(t.tma)

        for al in alert[::-1]:
            spill = al.tma - w.muka_air_normal
            if spill >= flood:
                flood = spill
                time = al.sampling.strftime("%H:%M:%S")

        if round(flood, 2) > 0:
            kondisi = f"<b>Normal</b><br><span style='color: red'>+{round(flood, 3)}</span> <small><i>{time}</i></small>"

        data[w.wil_sungai].append({
            'id': w.id,
            'no': count,
            'nama': w.name,
            'kab': w.kab,
            'volume': "{:,.3f}".format(w.volume/1000000),
            'lbi': "{:,.2f}".format(w.lbi),
            'elev_puncak': "{:,.2f}".format(w.elev_puncak),
            'muka_air_normal': "{:,.2f}".format(w.muka_air_normal),
            'muka_air_min': "{:,.2f}".format(w.muka_air_min),
            'tma6': tma_d['6'],
            'tma12': tma_d['12'],
            'tma18': tma_d['18'],
            'vol': None if not vol else "{:,.3f}".format(vol),
            'intake_deb': None if not daily or not daily.intake_deb else "{:,.2f}".format(daily.intake_deb),
            'spillway_deb': None if not daily or not daily.spillway_deb else "{:,.2f}".format(daily.spillway_deb),
            'debit': None if not vnotch or not vnotch.vn1_deb else "{:,.2f}".format(vnotch.vn1_deb),
            'kondisi': kondisi or "Normal",
            'curahhujan': None if not ch_t else {'ch': ch_t.ch, 'time': ch_t.sampling},
            'tma_banjir': None if not alert else {'tma': alert[0].tma, 'time': alert[0].sampling}
        })
        count += 1

    return render_template('bendungan/index.html',
                            waduk=data,
                            wil_sungai=wil_sungai,
                            sampling=sampling)


@bp.route('/<lokasi_id>', methods=['GET'])
def tma(lokasi_id):
    date = request.values.get('sampling')
    def_date = datetime.datetime.utcnow()
    sampling = datetime.datetime.strptime(date, "%Y-%m-%d") if date else def_date
    end = sampling + datetime.timedelta(days=1)

    pos = Bendungan.query.get(lokasi_id)
    tma = ManualTma.query.filter(
                                and_(
                                    ManualTma.sampling >= sampling,
                                    ManualTma.sampling <= end),
                                ManualTma.bendungan_id == pos.id
                            ).order_by(desc(ManualTma.sampling)).first()

    return render_template('bendungan/info.html', waduk=pos, tma=tma)


@bp.route('/<lokasi_id>/operasi', methods=['GET'])
def operasi(lokasi_id):
    sampling = request.values.get('sampling')
    sampling = datetime.datetime.strptime(sampling, "%Y") if sampling else datetime.datetime.now()
    start = datetime.datetime.strptime(f"{sampling.year -1}-11-01", "%Y-%m-%d")
    end = datetime.datetime.strptime(f"{sampling.year}-10-31", "%Y-%m-%d")

    pos = Bendungan.query.get(lokasi_id)
    rtow = Rencana.query.filter(
                            and_(
                                Rencana.sampling >= start,
                                Rencana.sampling <= end),
                            Rencana.bendungan_id == pos.id
                            ).order_by(Rencana.sampling).all()

    tanggal = ""
    operasi = {
        'po_bona': "",
        'po_bonb': "",
        'po_tma': "",
        'real': "",
        'elev_min': "",
        'sedimen': "",
        'po_outflow': "",
        'po_inflow': "",
        'real_outflow': "",
        'real_inflow': ""
    }
    i = 0
    for rt in rtow:
        last_day = calendar.monthrange(rt.sampling.year, rt.sampling.month)[1]

        cond = sampling.year >= 2020 and pos.wil_sungai in ['2', '3']
        if cond and rt.sampling.day == 15:
            continue

        cond1 = sampling.year <= 2018 and rt.sampling.day in [1, 16]
        cond2 = sampling.year >= 2019 and rt.sampling.day in [15, last_day]
        cond3 = rt.sampling.day in [10, 20, last_day]
        if cond1 or cond2 or (cond and cond3):
            if (i != 0):
                tanggal += ","
                operasi['po_bona'] += ","
                operasi['po_bonb'] += ","
                operasi['po_tma'] += ","
                operasi['real'] += ","
                operasi['elev_min'] += ","
                operasi['sedimen'] += ","
                operasi['po_outflow'] += ","
                operasi['po_inflow'] += ","
                operasi['real_outflow'] += ","
                operasi['real_inflow'] += ","

            daily = ManualDaily.query.filter(
                                        and_(
                                            extract('month', ManualDaily.sampling) == rt.sampling.month,
                                            extract('year', ManualDaily.sampling) == rt.sampling.year,
                                            extract('day', ManualDaily.sampling) == rt.sampling.day),
                                        ManualDaily.bendungan_id == lokasi_id
                                        ).first()
            tma = ManualTma.query.filter(
                                    and_(
                                        extract('month', ManualTma.sampling) == rt.sampling.month,
                                        extract('year', ManualTma.sampling) == rt.sampling.year,
                                        extract('day', ManualTma.sampling) == rt.sampling.day),
                                    ManualTma.bendungan_id == lokasi_id
                                    ).first()

            tgl_str = rt.sampling.strftime("%d %b %Y")
            tanggal += f"'{tgl_str}'"
            operasi['po_bona'] += f"{rt.po_bona}" if rt.po_bona else "0"
            operasi['po_bonb'] += f"{rt.po_bonb}" if rt.po_bonb else "0"
            operasi['po_tma'] += f"{rt.po_tma}" if rt.po_tma else "0"
            operasi['real'] += str(tma.tma) if tma and tma.tma else "null"
            operasi['elev_min'] += f"{pos.muka_air_min or '0'}"
            operasi['sedimen'] += f"{pos.sedimen or '0'}"
            operasi['po_outflow'] += '0' if not rt.po_outflow_deb else str(rt.po_outflow_deb)
            operasi['po_inflow'] += '0' if not rt.po_inflow_deb else str(rt.po_inflow_deb)
            operasi['real_outflow'] += str(daily.intake_deb) if daily and daily.intake_deb else "0"
            operasi['real_inflow'] += str(daily.inflow_deb) if daily and daily.inflow_deb else "0"
            i += 1

    return render_template('bendungan/operasi.html',
                            waduk=pos,
                            sampling=sampling,
                            operasi=operasi,
                            tanggal=tanggal)


@bp.route('/<lokasi_id>/vnotch', methods=['GET'])
def vnotch(lokasi_id):
    date = request.values.get('sampling')
    def_date = datetime.datetime.utcnow()
    sampling = datetime.datetime.strptime(date, "%Y") if date else def_date
    end = datetime.datetime.strptime(f"{sampling.year}-11-1", "%Y-%m-%d")
    start = end - datetime.timedelta(days=356)

    pos = Bendungan.query.get(lokasi_id)
    sampling = datetime.datetime.now()

    manual_vn = ManualVnotch.query.filter(
                                        and_(
                                            ManualVnotch.sampling >= start,
                                            ManualVnotch.sampling <= end),
                                        ManualVnotch.bendungan_id == pos.id
                                    ).order_by(ManualVnotch.sampling).all()
    manual_daily = ManualDaily.query.filter(
                                        and_(
                                            ManualDaily.sampling >= start,
                                            ManualDaily.sampling <= end),
                                        ManualDaily.bendungan_id == pos.id
                                    ).order_by(ManualDaily.sampling).all()
    filtered_daily = {}
    for daily in manual_daily:
        filtered_daily[daily.sampling.strftime("%d %b %Y")] = daily
    filtered_vnotch = {}
    for vn in manual_vn:
        tgl = vn.sampling.strftime("%d %b %Y")
        if tgl not in filtered_vnotch:
            filtered_vnotch[tgl] = {
                'ch': 0,
                'bts_remb': pos.vn1_q_limit,
                'vn': {
                    'VNotch 1': vn.vn1_deb,
                    'VNotch 2': vn.vn2_deb,
                    'VNotch 3': vn.vn3_deb
                }
            }

        if tgl in filtered_daily:
            filtered_vnotch[tgl]['ch'] += filtered_daily[tgl].ch or 0
        else:
            filtered_vnotch[tgl]['ch'] += 0

    vnotch = {
        'tanggal': "",
        'ch': "",
        'bts_remb': "",
        'vn': {}
    }
    for i, vn in enumerate(filtered_vnotch):
        if i != 0:
            vnotch['tanggal'] += ","
            vnotch['ch'] += ","
            vnotch['bts_remb'] += ","
            for vnn in filtered_vnotch[vn]['vn']:
                vnotch['vn'][vnn] += ","

        tgl = vn
        vnotch['tanggal'] += f"'{tgl}'"
        vnotch['ch'] += f"{filtered_vnotch[vn]['ch']}"
        vnotch['bts_remb'] += f"{filtered_vnotch[vn]['bts_remb'] or 0}"
        for vnn in filtered_vnotch[vn]['vn']:
            if vnn not in vnotch['vn']:
                vnotch['vn'][vnn] = ""
            val = "0" if not filtered_vnotch[vn]['vn'][vnn] else filtered_vnotch[vn]['vn'][vnn]
            vnotch['vn'][vnn] += f"{val}"
    # pprint(vnotch)

    return render_template('bendungan/vnotch.html',
                            waduk=pos,
                            sampling=sampling,
                            vnotch=vnotch)


@bp.route('/<lokasi_id>/piezo', methods=['GET'])
def piezo(lokasi_id):
    date = request.values.get('sampling')
    def_date = datetime.datetime.utcnow()
    sampling = datetime.datetime.strptime(date, "%Y") if date else def_date
    end = datetime.datetime.strptime(f"{sampling.year}-11-1", "%Y-%m-%d")
    start = end - datetime.timedelta(days=356)

    pos = Bendungan.query.get(lokasi_id)
    sampling = datetime.datetime.now()

    manual_piezo = ManualPiezo.query.filter(
                                            and_(
                                                ManualPiezo.sampling >= start,
                                                ManualPiezo.sampling <= end),
                                            ManualPiezo.bendungan_id == pos.id
                                        ).order_by(ManualPiezo.sampling).all()
    profile = ['1', '2', '3', '4', '5']
    alpha = ['a', 'b', 'c']
    tgl_labels = ""
    piezodata = {}
    for p in profile:
        piezodata[p] = {}
        for a in alpha:
            piezodata[p][a] = ""

    for i, piezo in enumerate(manual_piezo):
        if piezo.sampling.strftime("%a") == "Mon":
            if i == 0:
                tgl_labels += f"'{piezo.sampling.strftime('%d %b %Y')}'"
                for p in profile:
                    for a in alpha:
                        val = getattr(piezo, f"p{p}{a}")
                        val = val or "0"
                        piezodata[p][a] += f"{val}"
                continue

            tgl_labels += f",'{piezo.sampling.strftime('%d %b %Y')}'"
            for p in profile:
                for a in alpha:
                    val = getattr(piezo, f"p{p}{a}")
                    val = val or "0"
                    piezodata[p][a] += f",{val}"
    # pprint(piezodata)

    return render_template('bendungan/piezo.html',
                            waduk=pos,
                            sampling=sampling,
                            tgl_labels=tgl_labels,
                            piezodata=piezodata)


@bp.route('/petugas')
def petugas():
    waduk = Bendungan.query.all()
    petugas = Petugas.query.filter(Petugas.is_active == '1').all()

    data = {}
    for w in waduk:
        data[w.id] = {
            'nama': w.name,
            'petugas': []
        }
    for p in petugas:
        if p.tugas == "Koordinator":
            data[p.bendungan.id]['petugas'].insert(0, {
                'nama': p.nama,
                'tugas': p.tugas
            })
        else:
            data[p.bendungan.id]['petugas'].append({
                'nama': p.nama,
                'tugas': p.tugas
            })

    return render_template('bendungan/petugas.html',
                            data=data)


@bp.route('/kegiatan')
def kegiatan():
    # date = request.values.get('sampling')
    # now = datetime.datetime.now() + datetime.timedelta(hours=7)
    # def_date = date if date else now.strftime("%Y-%m-%d")
    # sampling = datetime.datetime.strptime(def_date, "%Y-%m-%d")
    # end = sampling + datetime.timedelta(hours=23, minutes=55)
    sampling, end = day_range(request.values.get('sampling'))

    kegiatan = Kegiatan.query.filter(
                                and_(
                                    Kegiatan.sampling >= sampling,
                                    Kegiatan.sampling <= end)
                                ).order_by(Kegiatan.c_date).all()
    data = {}
    for keg in kegiatan:
        if keg.bendungan_id not in data:
            data[keg.bendungan_id] = {
                'bend': keg.bendungan,
                'kegiatan': {}
            }

        if keg.petugas not in data[keg.bendungan_id]['kegiatan']:
            data[keg.bendungan_id]['kegiatan'][keg.petugas] = []

        data[keg.bendungan_id]['kegiatan'][keg.petugas].append(keg)

    return render_template('bendungan/kegiatan.html',
                            data=data,
                            sampling=sampling)
