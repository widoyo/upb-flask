import datetime
import calendar
from zoneinfo import ZoneInfo
from sqlalchemy import and_

weekday_name = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jum'at", "Sabtu"]
month_name = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
                "Agustus", "September", "Oktober", "November", "Desember"]


def query_with_sampling_range(model, start, end):
    return model.query.filter(and_(model.sampling >= start, model.sampling <= end)).all()


def to_date(datestring):
    """datestring harus berformat yyyy/mm/dd"""
    _date = None
    try:
        (t, b, g) = datestring.split('/')
    except ValueError:
        (t, b, g) = datestring.split('-')
    try:
        _date = datetime.date(int(t), int(b), int(g))
    except ValueError:
        _date = datetime.date(int(g), int(b), int(t))
    return _date


def month_range(date=None):
    ''' input str format (%Y-%m-%d)
    return start of the month, todays date or end of the month, and number of days '''
    now = datetime.datetime.now(tz=ZoneInfo('Asia/Jakarta'))
    date = datetime.datetime.strptime(date, "%Y-%m-%d") if date else now
    start = datetime.datetime.strptime(f"{date.year}-{date.month}-01", "%Y-%m-%d")
    if start.year == now.year and start.month == now.month:
        day = now.day
    else:
        day = calendar.monthrange(start.year, start.month)[1]
    end = start + datetime.timedelta(days=(day-1), hours=23)
    
    if end.day > 15:
        start = start.replace(day=15)

    return start, end, day


def week_range(date=None):
    ''' input str format (%Y-%m-%d)
    return current date, monday of the week and saturday of the week '''
    now = datetime.datetime.now(tz=ZoneInfo('Asia/Jakarta'))
    def_date = date if date else now.strftime("%Y-%m-%d")
    date = datetime.datetime.strptime(def_date, "%Y-%m-%d")

    weekday = int(date.strftime('%w'))
    start = date if weekday == 1 else date - datetime.timedelta(days=weekday-1)
    end = start + datetime.timedelta(days=5)

    return date, start, end


def day_range(date=None):
    ''' input str format (%Y-%m-%d)
    return start of the day and end of the day '''
    now = datetime.datetime.now(tz=ZoneInfo('Asia/Jakarta'))
    def_date = date if date else now.strftime("%Y-%m-%d")
    start = datetime.datetime.strptime(def_date, "%Y-%m-%d")
    end = start + datetime.timedelta(hours=23, minutes=55)

    return start, end


def utc2wib(date):
    ''' date : python datetime object '''
    return date + datetime.timedelta(hours=7)


def wib2utc(date):
    ''' date : python datetime object '''
    return date - datetime.timedelta(hours=7)


def get_current_or_latest(date):
    '''
    date : python datetime object (utc)
    return : the same datetime or current datetime if input is in future
    '''
    now = datetime.datetime.utcnow()
    if date > now:
        return now
    else:
        return date


def get_hari_tanggal(date):
    '''
    date : python datetime object
    return : hari/tanggal bahasa indonesia
    '''
    hari = weekday_name[int(date.strftime("%w"))]
    tanggal = date.strftime("%d")
    bulan = month_name[int(date.strftime("%m")) - 1]
    tahun = date.strftime("%Y")
    return f"{hari}/{tanggal} {bulan} {tahun}"

row2dict = lambda r: {c.name: str(getattr(r, c.name)) for c in r.__table__.columns}