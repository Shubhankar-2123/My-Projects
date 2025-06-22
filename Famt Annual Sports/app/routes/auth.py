from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash
from app.models import User, get_user_by_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        user_data = get_user_by_email(email)
        if user_data and check_password_hash(user_data['password'], request.form.get('password')):
            user = User(user_data)
            login_user(user)
            return redirect(url_for('dashboard.player'))
        flash('Invalid credentials!')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    db.users.insert_one({
        "email": request.form.get('email'),
        "password": generate_password_hash(request.form.get('password')),
        "role": "player",
        "registered_at": datetime.utcnow()
    })
    return redirect(url_for('auth.login'))