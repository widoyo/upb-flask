from flask import Blueprint, render_template
from app.models import Bendungan

bp = Blueprint('bendungan', __name__)


@bp.route('/')
def index():
    ''' Home Bendungan '''
    return render_template('bendungan/index.html')
