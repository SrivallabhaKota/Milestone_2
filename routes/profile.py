import os
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, current_app)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User

profile_bp = Blueprint('profile', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── Profile ─────────────────────────────────────────────────────────────────
@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        currency = request.form.get('currency', '₹').strip()

        try:
            monthly_capacity = float(request.form.get('monthly_saving_capacity', 0) or 0)
        except ValueError:
            monthly_capacity = current_user.monthly_saving_capacity or 0

        errors = []
        if not name:
            errors.append('Name is required.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return redirect(url_for('profile.profile'))

        current_user.name = name
        current_user.phone = phone
        current_user.currency = currency or '₹'
        current_user.monthly_saving_capacity = monthly_capacity

        # Handle profile picture upload
        file = request.files.get('profile_image')
        if file and file.filename and _allowed_file(file.filename):
            filename = secure_filename(f"user_{current_user.id}_{file.filename}")
            upload_path = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, filename))
            current_user.profile_image = filename

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.profile'))

    return render_template('profile.html')


# ─── Change Password ─────────────────────────────────────────────────────────
@profile_bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    current_pw = request.form.get('current_password', '')
    new_pw = request.form.get('new_password', '')
    confirm_pw = request.form.get('confirm_password', '')

    if not current_user.check_password(current_pw):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('profile.profile'))
    if len(new_pw) < 6:
        flash('New password must be at least 6 characters.', 'danger')
        return redirect(url_for('profile.profile'))
    if new_pw != confirm_pw:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('profile.profile'))

    current_user.set_password(new_pw)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('profile.profile'))
