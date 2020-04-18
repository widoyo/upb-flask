import datetime
import calendar


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


def month_range(date):
    ''' input str format (%Y-%m-%d)
    return start of the month, todays date or end of the month, and number of days '''
    now = datetime.datetime.now() + datetime.timedelta(hours=7)
    date = datetime.datetime.strptime(date, "%Y-%m-%d") if date else now
    start = datetime.datetime.strptime(f"{date.year}-{date.month}-01", "%Y-%m-%d")
    if start.year == now.year and start.month == now.month:
        day = now.day
    else:
        day = calendar.monthrange(start.year, start.month)[1]
    end = start + datetime.timedelta(days=(day-1), hours=23)

    return start, end, day


def day_range(date):
    ''' input str format (%Y-%m-%d)
    return start of the day and end of the day '''
    now = datetime.datetime.now() + datetime.timedelta(hours=7)
    def_date = date if date else now.strftime("%Y-%m-%d")
    start = datetime.datetime.strptime(def_date, "%Y-%m-%d")
    end = start + datetime.timedelta(hours=23, minutes=55)

    return start, end
