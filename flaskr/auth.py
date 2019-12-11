import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        type = request.form['type']
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        date_of_birth = request.form['date_of_birth']
        airline_name = request.form['airline_name']
        booking_agent_id = request.form['booking_agent_id']
        name = request.form['name']
        building_number = request.form['building_number']
        street = request.form['street']
        city = request.form['city']
        state = request.form['state']
        phone_number = request.form['phone_number']
        passport_number = request.form['passport_number']
        passport_expiration = request.form['passport_expiration']
        passport_country = request.form['passport_country']
        db = get_db()
        error = None
        if type == 'Airline Staff':
            if not username:
                error = 'Username is required.'
            elif not password:
                error = 'Password is required.'
            elif db.execute(
                    'SELECT username FROM airline_staff WHERE username = ?', (username,)
            ).fetchone() is not None:
                error = 'User {} is already registered.'.format(username)
            if error is None:
                db.execute(
                    'INSERT INTO airline_staff (username, password, first_name, last_name, date_of_birth, airline_name) VALUES (?, ?, ?, ?, ?, ?)',
                    (username, generate_password_hash(password), first_name, last_name, date_of_birth, airline_name)
                )
                db.commit()
                return redirect(url_for('auth.login'))
        elif type == 'Customer':
            if not username:
                error = 'Username is required.'
            elif not password:
                error = 'Password is required.'
            elif db.execute(
                    'SELECT email FROM customer WHERE email = ?', (username,)
            ).fetchone() is not None:
                error = 'User {} is already registered.'.format(username)
            if error is None:
                db.execute(
                    'INSERT INTO customer (email, password, name, building_number, date_of_birth, street, city, state, passport_number, passport_expiration, passport_country, phone_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (username, generate_password_hash(password), name, building_number, date_of_birth, street, city, state, passport_number, passport_expiration, passport_country, phone_number)
                )
                db.commit()
                return redirect(url_for('auth.login'))
        else:
            if not username:
                error = 'Username is required.'
            elif not password:
                error = 'Password is required.'
            elif db.execute(
                    'SELECT email FROM booking_agent WHERE email = ?', (username,)
            ).fetchone() is not None:
                error = 'User {} is already registered.'.format(username)
            if error is None:
                db.execute(
                    'INSERT INTO booking_agent (email, password, booking_agent_id) VALUES (?, ?, ?)',
                    (username, generate_password_hash(password), booking_agent_id)
                )
                db.commit()
                return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        type = request.form['type']
        db = get_db()
        error = None
        if type == 'Airline Staff':
            user = db.execute(
                'SELECT * FROM airline_staff WHERE username = ?', (username,)
            ).fetchone()

            if user is None:
                error = 'Incorrect username.'
            elif not check_password_hash(user['password'], password):
                error = 'Incorrect password.'

            if error is None:
                session.clear()
                session['type'] = type
                g.user = user
                session['key'] = user['username']
                return render_template('airline_stuff')
        elif type == 'Customer':
            user = db.execute(
                'SELECT * FROM customer WHERE email = ?', (username,)
            ).fetchone()

            if user is None:
                error = 'Incorrect username.'
            elif not check_password_hash(user['password'], password):
                error = 'Incorrect password.'

            if error is None:
                session.clear()
                session['type'] = type
                g.user = user
                session['key'] = user['email']
                return redirect(url_for('index'))  # change
        else:
            user = db.execute(
                'SELECT * FROM booking_agent WHERE email = ?', (username,)
            ).fetchone()

            if user is None:
                error = 'Incorrect username.'
            elif not check_password_hash(user['password'], password):
                error = 'Incorrect password.'

            if error is None:
                session.clear()
                session['type'] = type
                g.user = user
                session['key'] = user['email']
                print(g.user['email'])
                return render_template('airline_staff.html')

        flash(error)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM airline_staff WHERE username = ?', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view