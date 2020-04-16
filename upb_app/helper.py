import datetime


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
