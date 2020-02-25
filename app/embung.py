from flask import Blueprint, render_template
from app.models import Embung

bp = Blueprint('embung', __name__)


@bp.route('/')
def index():
    ''' Home Embung '''
    return render_template('embung/index.html')
