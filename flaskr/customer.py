from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from flaskr.auth import login_required_customer
from flaskr.database import get_db

from dateutil.relativedelta import relativedelta
from datetime import datetime

customer_bp = Blueprint("customer", __name__, url_prefix="/customer")


@customer_bp.route('/customer_home', methods=('POST', 'GET'))
@login_required_customer
def home():
    return render_template('./customerHome.html')


