import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('airline_staff', __name__, url_prefix='/airline_staff')

@bp.route('/airline_staff', methods=('GET', 'POST'))

@bp.route('/view_my_flights', methods=('GET', 'POST'))
def view_my_flights():
    db = get_db()



