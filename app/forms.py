from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DecimalField
from wtforms import BooleanField, SubmitField, SelectField, RadioField
from wtforms.validators import DataRequired

from app.models import Lokasi


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Ingat saya')
    submit = SubmitField('Login')
