from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import flash

from upb_app import login
from upb_app import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import desc, extract
import datetime
import hashlib
import re

wil_sungai = {
    '1': "Hulu",
    '2': "Madiun",
    '3': "Hilir",
}
jenis_pemeliharaan = [
    'cabut rumput',
    'potong rumput',
    'pembersihan sampah',
    'pelumasan',
    'pengecatan',
    'penggantian oli mesin',
    'perawatan alat kerja',
    'pengangkatan sedimen',
    'tambal sulam kerusakan ringan',
    'penghijauan',
]
jenis2atuan = {
    'cabut rumput': "m<sup>2</sup>",
    'potong rumput': "m<sup>2</sup>",
    'pembersihan sampah': "m<sup>2</sup>",
    'pelumasan': "Pcs",
    'pengecatan': "m<sup>2</sup>",
    'penggantian oli mesin': "Ltr",
    'perawatan alat kerja': "Pcs",
    'pengangkatan sedimen': "m<sup>2</sup>",
    'tambal sulam kerusakan ringan': "m<sup>2</sup>",
    'penghijauan': "m<sup>2</sup>"
}
lokasi_jenis = {
# 1 CH, 2 TMA, 3 Bendungan, 4 Klim
    '1': "Curah Hujan",
    '2': "TMA",
    '3': "Bendungan",
    '4': "Klimat"
}


class BaseLog(db.Model):
    __abstract__ = True
    c_user = db.Column(db.String(30))
    c_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    m_user = db.Column(db.String(30))
    m_date = db.Column(db.DateTime)

    @property
    def cdate_wib(self):
        return self.c_date + datetime.timedelta(hours=7)


class Users(UserMixin, db.Model):
    ''' Role { 2:petugas bendungan, 3:petugas embung, 1,4:admin balai} '''
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), index=True, unique=True, nullable=False)
    password = db.Column(db.String(128))
    role = db.Column(db.String(1))
    bendungan_id = db.Column(db.Integer, db.ForeignKey('bendungan.id'), nullable=True)
    embung_id = db.Column(db.Integer, db.ForeignKey('embung.id'), nullable=True)

    bendungan = relationship('Bendungan', back_populates='users')
    embung = relationship('Embung', back_populates='users')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        self.check_md5(password)
        return check_password_hash(self.password, password)

    def check_md5(self, password):
        passbyte = bytes(password, encoding='utf-8')
        m = hashlib.md5(passbyte)
        if m.hexdigest() == self.password:
            self.set_password(password)

    def __repr__(self):
        return '<User %r>' % self.username


@login.user_loader
def load_user(id):
    return Users.query.get(int(id))


class ManualDaily(BaseLog):
    __tablename__ = 'manual_daily'

    id = db.Column(db.Integer, primary_key=True)
    sampling = db.Column(db.DateTime, index=True)
    ch = db.Column(db.Float, nullable=True)
    inflow_vol = db.Column(db.Float, nullable=True)
    inflow_deb = db.Column(db.Float, nullable=True)
    intake_vol = db.Column(db.Float, nullable=True)
    intake_deb = db.Column(db.Float, nullable=True)
    intake_ket = db.Column(db.Text, nullable=True)
    outflow_vol = db.Column(db.Float, nullable=True)
    outflow_deb = db.Column(db.Float, nullable=True)
    spillway_vol = db.Column(db.Float, nullable=True)
    spillway_deb = db.Column(db.Float, nullable=True)
    bendungan_id = db.Column(db.Integer, db.ForeignKey('bendungan.id'), nullable=True)

    __table_args__ = (db.UniqueConstraint('bendungan_id', 'sampling',
                                          name='manualdaily_bendungan_sampling'),)


class ManualVnotch(BaseLog):
    __tablename__ = 'manual_vnotch'

    id = db.Column(db.Integer, primary_key=True)
    sampling = db.Column(db.DateTime, index=True)
    vn_tma = db.Column(db.Float, nullable=True)
    vn_deb = db.Column(db.Float, nullable=True)
    vn1_tma = db.Column(db.Float, nullable=True)
    vn1_deb = db.Column(db.Float, nullable=True)
    vn2_tma = db.Column(db.Float, nullable=True)
    vn2_deb = db.Column(db.Float, nullable=True)
    vn3_tma = db.Column(db.Float, nullable=True)
    vn3_deb = db.Column(db.Float, nullable=True)
    bendungan_id = db.Column(db.Integer, db.ForeignKey('bendungan.id'), nullable=True)

    __table_args__ = (db.UniqueConstraint('bendungan_id', 'sampling',
                                          name='manualvnotch_bendungan_sampling'),)


class ManualTma(BaseLog):
    __tablename__ = 'manual_tma'

    id = db.Column(db.Integer, primary_key=True)
    sampling = db.Column(db.DateTime, index=True)
    bendungan_id = db.Column(db.Integer, db.ForeignKey('bendungan.id'), nullable=True)
    tma = db.Column(db.Float)
    vol = db.Column(db.Float)
    telemetri = db.Column(db.Float)

    __table_args__ = (db.UniqueConstraint('bendungan_id', 'sampling',
                                          name='manualtma_bendungan_sampling'),)

    def local_cdate(self):
        return self.c_date + datetime.timedelta(hours=7)


class ManualPiezo(BaseLog):
    __tablename__ = 'manual_piezo'

    id = db.Column(db.Integer, primary_key=True)
    sampling = db.Column(db.DateTime, index=True)
    p1a = db.Column(db.Float, nullable=True)
    p1b = db.Column(db.Float, nullable=True)
    p1c = db.Column(db.Float, nullable=True)
    p2a = db.Column(db.Float, nullable=True)
    p2b = db.Column(db.Float, nullable=True)
    p2c = db.Column(db.Float, nullable=True)
    p3a = db.Column(db.Float, nullable=True)
    p3b = db.Column(db.Float, nullable=True)
    p3c = db.Column(db.Float, nullable=True)
    p4a = db.Column(db.Float, nullable=True)
    p4b = db.Column(db.Float, nullable=True)
    p4c = db.Column(db.Float, nullable=True)
    p5a = db.Column(db.Float, nullable=True)
    p5b = db.Column(db.Float, nullable=True)
    p5c = db.Column(db.Float, nullable=True)
    bendungan_id = db.Column(db.Integer, db.ForeignKey('bendungan.id'), nullable=True)

    __table_args__ = (db.UniqueConstraint('bendungan_id', 'sampling',
                                          name='manualpiezo_bendungan_sampling'),)


class BendungAlert(BaseLog):
    '''TMA / Kondisi banjir Waduk'''
    __tablename__ = 'bendung_alert'

    id = db.Column(db.Integer, primary_key=True)
    sampling = db.Column(db.DateTime, index=True)
    tma = db.Column(db.Float)
    spillway_deb = db.Column(db.Float, nullable=True)

    bendungan_id = db.Column(db.Integer, db.ForeignKey('bendungan.id'), nullable=True)


class CurahHujanTerkini(BaseLog):
    ''' CH Terkini '''
    __tablename__ = 'curahhujan_terkini'

    id = db.Column(db.Integer, primary_key=True)
    sampling = db.Column(db.DateTime, index=True)
    ch = db.Column(db.Float)

    bendungan_id = db.Column(db.Integer, db.ForeignKey('bendungan.id'), nullable=True)


class ManualDailyEmbung(BaseLog):
    __tablename__ = 'manual_daily_embung'

    id = db.Column(db.Integer, primary_key=True)
    sampling = db.Column(db.DateTime, index=True)
    inflow_vol = db.Column(db.Float, nullable=True)
    inflow_deb = db.Column(db.Float, nullable=True)
    intake_vol = db.Column(db.Float, nullable=True)
    intake_deb = db.Column(db.Float, nullable=True)
    spillway_vol = db.Column(db.Float, nullable=True)
    spillway_deb = db.Column(db.Float, nullable=True)
    embung_id = db.Column(db.Integer, db.ForeignKey('embung.id'), nullable=True)

    __table_args__ = (db.UniqueConstraint('embung_id', 'sampling',
                                          name='manualdaily_embung_sampling'),)


class ManualTmaEmbung(BaseLog):
    __tablename__ = 'manual_tma_embung'

    id = db.Column(db.Integer, primary_key=True)
    sampling = db.Column(db.DateTime, index=True)
    embung_id = db.Column(db.Integer, db.ForeignKey('embung.id'), nullable=True)
    tma = db.Column(db.Float)
    vol = db.Column(db.Float)
    __table_args__ = (db.UniqueConstraint('embung_id', 'sampling',
                                          name='manualtma_embung_sampling'),)

    def local_cdate(self):
        return self.c_date + datetime.timedelta(hours=7)


class PiketBanjir(BaseLog):
    __tablename__ = 'piket_banjir'

    id = db.Column(db.Integer, primary_key=True)
    sampling = db.Column(db.DateTime, index=True)
    obj_type = db.Column(db.String, default="bendungan")
    obj_id = db.Column(db.Integer)

    cuaca = db.Column(db.Text)
    ch = db.Column(db.Float)
    durasi = db.Column(db.Text)
    tma = db.Column(db.Float)
    volume = db.Column(db.Float)
    spillway_tma = db.Column(db.Float)
    spillway_deb = db.Column(db.Float)
    kondisi = db.Column(db.Text)

    petugas_id = db.Column(db.Integer, db.ForeignKey('petugas.id'), nullable=True)
    petugas = relationship('Petugas', back_populates='piket_banjir')

    __table_args__ = (db.UniqueConstraint('obj_type', 'obj_id', 'sampling',
                                          name='piket_banjir_obj_sampling'),)
    @property
    def object(self):
        if self.obj_type == "bendungan":
            return Bendungan.query.get(self.obj_id)
        else:
            return None

    @property
    def volume_percent(self):
        return round((self.volume/self.object.volume)*100, 2)


class Asset(BaseLog):
    __tablename__ = 'asset'

    id = db.Column(db.Integer, primary_key=True)
    kategori = db.Column(db.Text)
    nama = db.Column(db.Text)
    merk = db.Column(db.Text, nullable=True)
    model = db.Column(db.Text, nullable=True)
    perolehan = db.Column(db.Date, nullable=True)
    nilai_perolehan = db.Column(db.Float, nullable=True)
    bmn = db.Column(db.Text, nullable=True)
    bendungan_id = db.Column(db.Integer, db.ForeignKey('bendungan.id'), nullable=True)

    kerusakan = relationship('Kerusakan', back_populates='asset')


class Embung(BaseLog):
    __tablename__ = 'embung'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.Text)
    jenis = db.Column(db.String(1))
    desa = db.Column(db.Text)
    kec = db.Column(db.Text)
    kab = db.Column(db.Text)
    ll = db.Column(db.Text)
    sumber_air = db.Column(db.Text)
    tampungan = db.Column(db.Float)
    debit = db.Column(db.Float)
    pipa_transmisi = db.Column(db.Float)
    saluran_transmisi = db.Column(db.Float)
    air_baku = db.Column(db.Integer)
    irigasi = db.Column(db.Float)
    is_verified = db.Column(db.String(1))
    wil_sungai = db.Column(db.String(1))

    kegiatan = relationship('KegiatanEmbung', back_populates='embung')
    bagian = relationship('BagianEmbung', back_populates='embung')
    users = relationship('Users', back_populates='embung')

    def gen_username(self):
        cleaned = re.sub('[,.-]', '', self.nama)
        return cleaned.lower().replace(' ', '_')


class Petugas(BaseLog):
    __tablename__ = 'petugas'

    id = db.Column(db.Integer, primary_key=True)
    nama = nama = db.Column(db.Text)
    tugas = db.Column(db.Text)
    tgl_lahir = db.Column(db.DateTime, nullable=True)
    alamat = db.Column(db.Text, nullable=True)
    kab = db.Column(db.Text, nullable=True)
    pendidikan = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.String(1))
    bendungan_id = bendungan_id = db.Column(db.Integer, db.ForeignKey('bendungan.id'), nullable=True)

    bendungan = relationship('Bendungan', back_populates='petugas')
    pemeliharaan_petugas = relationship('PemeliharaanPetugas', back_populates='petugas')
    kinerja_nilai = relationship('KinerjaNilai', back_populates='petugas')
    piket_banjir = relationship('PiketBanjir', back_populates='petugas')

    @property
    def birthdate(self):
        return None if not self.tgl_lahir else self.tgl_lahir.strftime("%-d %b %Y")

    def get_kinerja(self, sampling):
        sampling = sampling.strftime("%Y-%m-01")

        kinerja = KinerjaNilai.query.filter(
                                        KinerjaNilai.sampling == sampling,
                                        KinerjaNilai.petugas_id == self.id
                                    ).order_by(
                                        KinerjaNilai.kinerja_komponen_id).all()
        return kinerja

    def get_kinerja_summary(self, sampling):
        sampling = sampling.strftime("%Y-%m-01")

        kinerja = KinerjaNilai.query.filter(
                                        KinerjaNilai.sampling == sampling,
                                        KinerjaNilai.petugas_id == self.id).all()
        if not kinerja:
            return None, None, None
        else:
            nilai = sum([k.points for k in kinerja])
            nilai_max = sum([k.kinerja_komponen.nilai_max for k in kinerja])
            return nilai, nilai_max, self.get_kinerja_str(nilai)

    def get_kinerja_yearly(self, sampling):
        ''' return list of monthly kinerja summary '''
        kinerja = KinerjaNilai.query.filter(
                                        extract('year', KinerjaNilai.sampling) == sampling.year,
                                        KinerjaNilai.petugas_id == self.id
                                    ).order_by(KinerjaNilai.kinerja_komponen_id).all()
        nilai = [None for i in range(12)]
        for k in kinerja:
            if nilai[int(k.sampling.month) - 1]:
                nilai[int(k.sampling.month) - 1] += k.points
            else:
                nilai[int(k.sampling.month) - 1] = k.points

        return nilai

    def get_kinerja_str(self, nilai):
        if nilai > 90:
            return "Sangat Baik"
        elif nilai > 80:
            return "Baik"
        elif nilai > 70:
            return "Cukup"
        elif nilai > 54:
            return "Kurang"
        else:
            return "Buruk"


class Bendungan(BaseLog):
    __tablename__ = 'bendungan'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.Text)
    ll = db.Column(db.Text)
    muka_air_min = db.Column(db.Float)
    muka_air_normal = db.Column(db.Float)
    muka_air_max = db.Column(db.Float)
    sedimen = db.Column(db.Float)
    bts_elev_awas = db.Column(db.Float)
    bts_elev_siaga = db.Column(db.Float)
    bts_elev_waspada = db.Column(db.Float)
    lbi = db.Column(db.Float)
    volume = db.Column(db.Float)
    lengkung_kapasitas = db.Column(db.Text)
    elev_puncak = db.Column(db.Float)
    kab = db.Column(db.Text)
    wil_sungai = db.Column(db.String(1))

    vn1_panjang_saluran = db.Column(db.Float)
    vn2_panjang_saluran = db.Column(db.Float)
    vn3_panjang_saluran = db.Column(db.Float)
    vn1_q_limit = db.Column(db.Float)
    vn2_q_limit = db.Column(db.Float)
    vn3_q_limit = db.Column(db.Float)
    vn1_tin_limit = db.Column(db.Float)
    vn2_tin_limit = db.Column(db.Float)
    vn3_tin_limit = db.Column(db.Float)

    petugas = relationship('Petugas', back_populates='bendungan')
    users = relationship('Users', back_populates='bendungan')
    kegiatan = relationship('Kegiatan', back_populates='bendungan')
    pemeliharaan = relationship('Pemeliharaan', back_populates='bendungan')

    @property
    def name(self):
        arr = self.nama.split('_')
        return " ".join(a.title() for a in arr)

    @property
    def lokasi(self):
        return Lokasi.query.filter(
                                    Lokasi.jenis == '3',
                                    Lokasi.jenis_id == self.id
                                ).first()

    @property
    def primabots(self):
        lokasi = self.lokasi

        if not lokasi:
            return None

        return lokasi.devices

    def get_active_petugas(self):
        petugas = Petugas.query.filter(
                                    Petugas.is_active == '1',
                                    Petugas.bendungan_id == self.id
                                ).order_by(Petugas.tugas).all()
        result = []
        for p in petugas:
            if p.tugas.lower().strip() == 'koordinator':
                result.insert(0, p)
            else:
                result.append(p)
        return result


class Foto(BaseLog):
    __tablename__ = 'foto'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Text)
    keterangan = db.Column(db.Text)
    obj_type = db.Column(db.Text)
    obj_id = db.Column(db.Integer)
    showcase = db.Column(db.Boolean, default=False)


class Kerusakan(BaseLog):
    __tablename__ = 'kerusakan'

    id = db.Column(db.Integer, primary_key=True)
    tgl_lapor = db.Column(db.DateTime, index=True)
    uraian = db.Column(db.Text)
    kategori = db.Column(db.Text)
    komponen = db.Column(db.Text, nullable=True)
    tgl_tanggapan = db.Column(db.DateTime, nullable=True)
    tanggapan = db.Column(db.Text, nullable=True)
    tgl_tndk_lnjt = db.Column(db.DateTime, nullable=True)
    tndk_lnjt = db.Column(db.Text, nullable=True)
    biaya = db.Column(db.Integer, nullable=True)
    foto_id = db.Column(db.Integer, nullable=True)
    bendungan_id = db.Column(db.Integer, db.ForeignKey('bendungan.id'), nullable=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=True)
    upb_id = db.Column(db.Integer, nullable=True)

    asset = relationship('Asset', back_populates='kerusakan')

    @property
    def fotos(self):
        return Foto.query.filter(
                            Foto.obj_type == 'kerusakan',
                            Foto.obj_id == self.id).all()

    @property
    def tgl_lapor_gmt7(self):
        return self.tgl_lapor + datetime.timedelta(hours=7)


class BagianEmbung(BaseLog):
    __tablename__ = 'bagian_embung'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.Text)
    embung_id = db.Column(db.Integer, db.ForeignKey('embung.id'), nullable=True)

    embung = relationship('Embung', back_populates='bagian')
    kegiatan = relationship('KegiatanEmbung', back_populates='bagian')


class KegiatanEmbung(BaseLog):
    __tablename__ = 'kegiatan_embung'

    id = db.Column(db.Integer, primary_key=True)
    sampling = db.Column(db.DateTime)
    lokasi = db.Column(db.Text)
    rencana = db.Column(db.Text)
    pencapaian = db.Column(db.Text)
    mulai = db.Column(db.String(5))
    selesai = db.Column(db.String(5))
    kendala = db.Column(db.Text)
    nilai = db.Column(db.Float)
    petugas = db.Column(db.Text)
    bagian_id = db.Column(db.Integer, db.ForeignKey('bagian_embung.id'), nullable=True)
    embung_id = db.Column(db.Integer, db.ForeignKey('embung.id'), nullable=True)

    embung = relationship('Embung', back_populates='kegiatan')
    bagian = relationship('BagianEmbung', back_populates='kegiatan')

    __table_args__ = (db.UniqueConstraint('embung_id', 'sampling', 'bagian_id',
                                          name='kegiatan_embung_sampling_bagian_id'),)

    @property
    def fotos(self):
        fotos = Foto.query.filter(
                        Foto.obj_type == 'kegiatan_embung',
                        Foto.obj_id == self.id).all()
        result = {}
        for f in fotos:
            length = len(f.keterangan)
            tag = f.keterangan[:length-1]
            result[tag] = f
        return result

    def get_hms(self):
        return self.c_date + datetime.timedelta(hours=7)


class Kegiatan(BaseLog):
    __tablename__ = 'kegiatan'

    id = db.Column(db.Integer, primary_key=True)
    sampling = db.Column(db.DateTime)
    petugas = db.Column(db.Text)
    uraian = db.Column(db.Text)
    foto_id = db.Column(db.Integer)
    bendungan_id = db.Column(db.Integer, db.ForeignKey('bendungan.id'), nullable=True)

    bendungan = relationship('Bendungan', back_populates='kegiatan')

    def get_hms(self):
        return self.c_date + datetime.timedelta(hours=7)


class Pemeliharaan(BaseLog):
    __tablename__ = 'pemeliharaan'

    id = db.Column(db.Integer, primary_key=True)
    sampling = db.Column(db.DateTime)
    is_rencana = db.Column(db.String(1))
    jenis = db.Column(db.Text)
    komponen = db.Column(db.Text)
    nilai = db.Column(db.Float)
    keterangan = db.Column(db.Text)
    bendungan_id = db.Column(db.Integer, db.ForeignKey('bendungan.id'), nullable=True)

    bendungan = relationship('Bendungan', back_populates='pemeliharaan')
    pemeliharaan_petugas = relationship('PemeliharaanPetugas', back_populates='pemeliharaan')

    @property
    def fotos(self):
        return Foto.query.filter(
                            Foto.obj_type == 'pemeliharaan',
                            Foto.obj_id == self.id).order_by(Foto.id).all()

    def get_hms(self):
        return self.c_date + datetime.timedelta(hours=7)

    def str_nilai(self):
        if self.nilai:
            formatted = f"{self.nilai} {jenis2atuan[self.jenis]}"
        else:
            formatted = "-"
        return formatted

    def get_unit(self):
        return jenis2atuan[self.jenis]

    def set_petugas(self, petugas_id_list):
        for pet in PemeliharaanPetugas.query.filter(PemeliharaanPetugas.pemeliharaan_id == self.id).all():
            # reset association first
            db.session.delete(pet)

        for id in petugas_id_list:
            new_obj = PemeliharaanPetugas(
                pemeliharaan_id=self.id,
                petugas_id=id
            )
            db.session.add(new_obj)
        db.session.commit()

    def get_petugas(self):
        petugas = []
        for pp in self.pemeliharaan_petugas:
            petugas.append(pp.petugas)
        return petugas

    def get_fotos_description(self):
        result = []
        for f in self.fotos:
            result.append({
                'pemeliharaan': self,
                'foto': f,
                'keterangan': f"{self.jenis}, {f.keterangan}"
            })
        return result


class PemeliharaanPetugas(BaseLog):
    __tablename__ = 'pemeliharaan_petugas'

    id = db.Column(db.Integer, primary_key=True)
    pemeliharaan_id = db.Column(db.Integer, db.ForeignKey('pemeliharaan.id'))
    petugas_id = db.Column(db.Integer, db.ForeignKey('petugas.id'))

    pemeliharaan = relationship('Pemeliharaan', back_populates='pemeliharaan_petugas')
    petugas = relationship('Petugas', back_populates='pemeliharaan_petugas')


class KinerjaKomponen(BaseLog):
    __tablename__ = 'kinerja_komponen'

    id = db.Column(db.Integer, primary_key=True)
    jabatan = db.Column(db.Text)
    deskripsi = db.Column(db.Text)
    nilai_max = db.Column(db.Float)
    input_max = db.Column(db.Float)
    obj_type = db.Column(db.Text)   # endungan or embung
    is_active = db.Column(db.String(1))

    kinerja_nilai = relationship('KinerjaNilai', back_populates='kinerja_komponen')


class KinerjaNilai(BaseLog):
    __tablename__ = 'kinerja_nilai'

    id = db.Column(db.Integer, primary_key=True)
    sampling = db.Column(db.DateTime)
    nilai = db.Column(db.Float)  # nilai input
    kinerja_komponen_id = db.Column(db.Integer, db.ForeignKey('kinerja_komponen.id'))
    petugas_id = db.Column(db.Integer, db.ForeignKey('petugas.id'))

    kinerja_komponen = relationship('KinerjaKomponen', back_populates='kinerja_nilai')
    petugas = relationship('Petugas', back_populates='kinerja_nilai')

    __table_args__ = (db.UniqueConstraint('sampling', 'kinerja_komponen_id', 'petugas_id',
                                          name='sampling_kinerja_komponen_petugas'),)

    @property
    def points(self):
        points = (self.nilai/self.kinerja_komponen.input_max) * self.kinerja_komponen.nilai_max
        return round(points, 2)

    def set_nilai(self, nilai):
        self.nilai = min(max(0, nilai), self.kinerja_komponen.input_max)

    def get_kinerja_str(self):
        if self.points > 0.9 * self.kinerja_komponen.nilai_max:
            return "Sangat Baik"
        elif self.points > 0.8 * self.kinerja_komponen.nilai_max:
            return "Baik"
        elif self.points > 0.7 * self.kinerja_komponen.nilai_max:
            return "Cukup"
        elif self.points > 0.54 * self.kinerja_komponen.nilai_max:
            return "Kurang"
        else:
            return "Buruk"


class Rencana(BaseLog):
    __tablename__ = 'rencana'

    id = db.Column(db.Integer, primary_key=True)
    sampling = db.Column(db.DateTime, index=True)
    po_tma = db.Column(db.Float)
    po_vol = db.Column(db.Float)
    po_inflow_vol = db.Column(db.Float)
    po_inflow_deb = db.Column(db.Float)
    po_outflow_vol = db.Column(db.Float, nullable=True)
    po_outflow_deb = db.Column(db.Float, nullable=True)
    po_bona = db.Column(db.Float, nullable=True)
    po_bonb = db.Column(db.Float, nullable=True)
    vol_bona = db.Column(db.Float, nullable=True)
    vol_bonb = db.Column(db.Float, nullable=True)
    bendungan_id = db.Column(db.Integer, db.ForeignKey('bendungan.id'), nullable=True)

    __table_args__ = (db.UniqueConstraint('bendungan_id', 'sampling',
                                          name='rencana_bendungan_sampling'),)


class Device(BaseLog):
    __tablename__ = 'device'

    id = db.Column(db.Integer, primary_key=True)
    sn = db.Column(db.String(8), index=True, unique=True, nullable=False)
    tipe = db.Column(db.String(12), default="arr")
    lokasi_id = db.Column(db.Integer, db.ForeignKey('lokasi.id'), nullable=True)
    periodik = db.relationship('Periodik',
                               primaryjoin="and_(Device.sn==Periodik.device_sn,\
                              Periodik.sampling<=func.now())",
                               back_populates='device', lazy='dynamic')
    temp_cor = db.Column(db.Float)
    humi_cor = db.Column(db.Float)
    batt_cor = db.Column(db.Float)
    tipp_fac = db.Column(db.Float)
    ting_son = db.Column(db.Float)  # dalam centi, tinggi sonar thd dasar sungai

    lokasi = relationship('Lokasi', back_populates='devices')
    latest_sampling = db.Column(db.DateTime)
    latest_up = db.Column(db.DateTime)
    latest_id = db.Column(db.Integer)

    def periodik_latest(self):
        return self.periodik.order_by(Periodik.id.desc()).first()

    def icon(self):
        return 'arr' == self.tipe and 'cloud-download' or 'upload'

    def __repr__(self):
        return '<Device {}>'.format(self.sn)


class Lokasi(BaseLog):
    __tablename__ = 'lokasi'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(50), index=True, unique=True)
    ll = db.Column(db.String(35))
    jenis = db.Column(db.String(1))  # 1 CH, 2 TMA, 3 Bendungan, 4 Klim
    jenis_id = db.Column(db.Integer, nullable=True)
    siaga1 = db.Column(db.Float)
    siaga2 = db.Column(db.Float)
    siaga3 = db.Column(db.Float)
    devices = relationship('Device', back_populates='lokasi')
    periodik = relationship('Periodik', back_populates='lokasi',
                            order_by="desc(Periodik.sampling)")
    latest_sampling = db.Column(db.DateTime)
    latest_up = db.Column(db.DateTime)
    latest_id = db.Column(db.Integer)

    def __repr__(self):
        return '<Lokasi {}>'.format(self.nama)

    def update_latest(self):
        '''Mengupdate field latest_sampling, latest_up, latest_id'''
        try:
            latest = self.periodik[0]
            self.latest_sampling = latest.sampling
            self.latest_id = latest.id
            self.latest_up = latest.up_s
            db.session.commit()
        except IndexError:
            pass

    def hujan_hari(self, tanggal):
        '''Return dict(jam: hujan)
        Mengambil data hujan sampling tanggal, akumulasi per jam'''
        now = datetime.datetime.now()
        start_pattern = '%Y-%m-%d 07:00:00'
        date_pattern = '%Y-%m-%d %H:%M:%S'
        mulai = datetime.datetime.strptime(
            tanggal.strftime(start_pattern), date_pattern)
        akhir = (mulai + datetime.timedelta(days=1)).replace(hour=6, minute=59)
        ret = dict()
        hours = [mulai + datetime.timedelta(hours=i) for i in range(24)]
        for device in self.devices:
            if device.tipe == 'arr':
                rst = device.periodik.filter(
                    Periodik.sampling.between(
                        mulai, akhir)).order_by(Periodik.sampling)
                data = dict([(h, []) for h in hours])
                for r in rst:
                    data[r.sampling.replace(minute=0, second=0,
                                            microsecond=0)].append(r.rain or 0)
                ret[device.sn] = {'count': rst.count(),
                                  'hourly': data}

        return ret


class Raw(db.Model):
    __tablename__ = 'raw'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(JSONB, unique=True)
    received = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Periodik(db.Model):
    __tablename__ = 'periodik'

    id = db.Column(db.Integer, primary_key=True)
    sampling = db.Column(db.DateTime, index=True)
    device_sn = db.Column(db.String(8), db.ForeignKey('device.sn'))
    lokasi_id = db.Column(db.Integer, db.ForeignKey('lokasi.id'), nullable=True)
    mdpl = db.Column(db.Float)
    apre = db.Column(db.Float)
    sq = db.Column(db.Integer)
    temp = db.Column(db.Float)
    humi = db.Column(db.Float)
    batt = db.Column(db.Float)
    rain = db.Column(db.Float)  # hujan dalam mm
    wlev = db.Column(db.Float)  # TMA dalam centi
    up_s = db.Column(db.DateTime)  # Up Since
    ts_a = db.Column(db.DateTime)  # Time Set at
    received = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    device = relationship("Device", back_populates="periodik")
    lokasi = relationship("Lokasi", back_populates="periodik")
    __table_args__ = (db.UniqueConstraint('device_sn', 'sampling',
                                          name='_device_sampling'),)

    def __repr__(self):
        return '<Periodik {} Device {}>'.format(self.sampling, self.device_sn)
    @classmethod
    def temukan_hujan(self, sejak=None):
        '''return periodik yang rain > 0'''
        dari = 30 # hari lalu
        if not sejak:
            sejak = datetime.datetime.now() - datetime.timedelta(days=dari)
            sejak = sejak.replace(minute=0, hour=7)
        data = [d for d in self.query.filter(self.sampling >=
                                             sejak).order_by(self.sampling)]
        lokasi_hari_hujan = [d.lokasi_id for d in data if (d.rain or 0) > 0]
        print(lokasi_hujan)
