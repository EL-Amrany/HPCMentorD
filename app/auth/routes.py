from flask import render_template, redirect, url_for, flash, request,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
import requests
from email_validator import validate_email, EmailNotValidError
from ..models import db, User
from ..main.routes import role_display_names

@auth.route('/validate_email', methods=['POST'])
def validate_email_route():
    email = request.json.get('email')
    # First: syntax & domain via email-validator
    try:
        valid = validate_email(email)
        email_norm = valid.email
    except EmailNotValidError as e:
        return jsonify({'valid': False, 'message': str(e)}), 200

    # Then: deliverability via AbstractAPI
    try:
        resp = requests.get(
            "https://emailvalidation.abstractapi.com/v1/",
            params={'api_key': "7f2076d9edb74a93a45d6abd0b6c7bb0", 'email': email_norm},
            timeout=5
        )
        data = resp.json()
    except requests.RequestException:
        # network / timeout / DNS issue
        return jsonify({'valid': False, 'message': 'Could not verify deliverability'}), 200

    # If AbstractAPI returned an error payload, show it:
    if data.get('error'):
        return jsonify({'valid': False, 'message': data['error']['message']}), 200

    # Finally check deliverability field
    if data.get('deliverability') == 'DELIVERABLE':
        return jsonify({'valid': True}), 200
    else:
        # you can also return the reason from data['is_disposable_email']['value'], etc.
        return jsonify({
            'valid': False,
            'message': '❌ Undeliverable — server said: ' + data.get('deliverability', 'unknown')
        }), 200


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name     = request.form['name']
        email_in = request.form['email']
        password = request.form['password']

        # 1) syntax + domain check
        try:
            valid = validate_email(email_in)
            email_norm = valid.email
        except EmailNotValidError as e:
            flash(str(e), 'error')
            return redirect(url_for('auth.signup'))

        # 2) optional: API deliverability check
        API_KEY = '7f2076d9edb74a93a45d6abd0b6c7bb0'
        r = requests.get(
            "https://emailvalidation.abstractapi.com/v1/",
            params={'api_key': API_KEY, 'email': email_norm}
        ).json()
        if r.get('deliverability') != 'DELIVERABLE':
            flash('Email address not deliverable.', 'danger')
            return redirect(url_for('auth.signup'))

        # 3) uniqueness
        if User.query.filter_by(email=email_norm).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('auth.signup'))

        # 4) finally create user
        u = User(name=name, email=email_norm, password=generate_password_hash(password))
        db.session.add(u)
        db.session.commit()
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/signup.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            # Role not yet selected? Send to role selection
            if not user.role:
                return redirect(url_for('main.role_select'))
            return redirect(url_for('main.dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
