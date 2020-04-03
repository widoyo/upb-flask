from flask import Blueprint, jsonify, request
from upb_app.models import Bendungan
from sqlalchemy import or_


bp = Blueprint('api', __name__)
