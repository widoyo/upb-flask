from flask import Blueprint
from app.models import Bendungan

bp = Blueprint('bendungan', __name__)


@bp.route('/')
def index():
    ''' Home Bendungan '''
    return
