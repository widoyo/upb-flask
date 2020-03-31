from flask import Blueprint, jsonify, request
from app.models import Bendungan
from sqlalchemy import or_


bp = Blueprint('api', __name__)
