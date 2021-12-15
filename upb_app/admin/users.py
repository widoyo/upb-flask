from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from upb_app.models import Users, Bendungan
from upb_app.forms import AddUser
from upb_app import db
from upb_app import admin_only

from upb_app.admin import bp
# bp = Blueprint('users', __name__)


@bp.route('/users')
@login_required
@admin_only
def users():
    users = Users.query.order_by(Users.role).all()
    bends = Bendungan.query.all()
    return render_template('users/index.html',
                            users=users,
                            bends=bends,
                            csrf=generate_csrf())


@bp.route('/user/add', methods=['POST'])
@login_required
@admin_only
def user_add():
    form = AddUser()
    if form.validate_on_submit():
        username = request.values.get('username')
        password = request.values.get('password')
        bendungan_id = request.values.get('bendungan')
        role = request.values.get('role')

        # check if username is available
        if Users.query.filter_by(username=username).first():
            flash('Username sudah terdaftar !', 'danger')
            return redirect(url_for('admin.users'))

        # save new user data
        new_user = Users(
            username=username,
            role=role
        )
        # hash password as md5
        new_user.set_password(password)

        if bendungan_id:
            new_user.bendungan_id = bendungan_id

        db.session.add(new_user)
        db.session.flush()
        db.session.commit()

        flash('Tambah User berhasil !', 'success')

    return redirect(url_for('admin.users'))


@bp.route('/user/<user_id>/password', methods=['GET', 'POST'])
@login_required
@admin_only
def user_password(user_id):
    user = Users.query.get(user_id)
    if request.method == 'POST':
        password = request.values.get('password')
        user.set_password(password)
        db.session.commit()

        flash('Password {user.username} telah diubah !', 'success')
        return redirect(url_for('admin.users'))
    return render_template('users/password.html', user_target=user)


@bp.route('/user/password', methods=['POST'])
@login_required
def user_password_self():
    password = request.values.get('password')
    current_user.set_password(password)
    db.session.commit()

    flash('Password berhasil diubah !', 'success')

    if current_user.role == '3':
        return redirect(url_for('admin.kegiatan_embung', embung_id=current_user.embung_id))
    return redirect(url_for('admin.operasi'))


@bp.route('/user/<user_id>/delete', methods=['GET', 'POST'])
@login_required
@admin_only
def user_delete(user_id):
    user = Users.query.get(user_id)
    if request.method == 'POST':
        db.session.delete(user)
        db.session.commit()

        flash('User dihapus !', 'success')
        return redirect(url_for('admin.users'))
    return render_template('users/hapus.html', user=user)
