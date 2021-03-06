from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required
from upb_app.models import Users, Bendungan
from upb_app.forms import AddUser
from upb_app import db

from upb_app.admin import bp
# bp = Blueprint('users', __name__)


@bp.route('/users')
@login_required
def users():
    users = Users.query.all()
    bends = Bendungan.query.all()
    return render_template('users/index.html',
                            users=users,
                            bends=bends)


@bp.route('/users/add', methods=['GET', 'POST'])
@login_required
def users_add():
    form = AddUser()
    if form.validate_on_submit():
        username = request.values.get('username')
        password = request.values.get('password')
        bendungan_id = request.values.get('bendungan')
        role = request.values.get('role')

        # check if username is available
        if Users.query.filter_by(username=username).first():
            flash('Username tidak tersedia !', 'danger')
            return render_template('users/tambah.html', form=form)

        # save new user data
        new_user = Users(
            username=username,
            bendungan_id=bendungan_id,
            role=role
        )
        # hash password as md5
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.flush()
        db.session.commit()

        flash('Tambah User berhasil !', 'success')
        return redirect(url_for('admin.users'))

    return render_template('users/index.html',
                            form=form)


@bp.route('/users/password', methods=['GET', 'POST'])
@login_required
def users_password(user_id):
    user = Users.query.get(user_id)
    if request.method == 'POST':
        password = request.values.get('password')
        user.set_password(password)
        db.session.commit()

        flash('Password berhasil diubah !', 'success')
        return redirect(url_for('admin.users'))
    return render_template('users/password.html', user=user)


@bp.route('/users/delete', methods=['GET', 'POST'])
@login_required
def users_delete(user_id):
    user = Users.query.get(user_id)
    if request.method == 'POST':
        db.session.delete(user)
        db.session.commit()

        flash('User dihapus !', 'success')
        return redirect(url_for('admin.users'))
    return render_template('users/hapus.html', user=user)
