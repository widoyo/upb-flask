from flask import Blueprint
from app.models import Embung

bp = Blueprint('embung', __name__)


@bp.route('/')
def index():
    ''' Home Embung '''
    return
