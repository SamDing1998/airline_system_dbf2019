import functools
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

as_bp = Blueprint('airline_staff', __name__, url_prefix='/airline_staff')

@as_bp.route('/view_my_flights', methods=('GET', 'POST'))
def view_my_flights():
    from_date = request.args["from_date"]
    to_date = request.args["to_date"]
    departure_airport = request.args["departure_airport"] + "%"
    arrival_airport = request.args["arrival_airport"] + "%"
    departure_city = request.args["departure_city"] + "%"
    arrival_city = request.args["arrival_city"] + "%"
    airline_name = request.args["airline_name"]

    db = get_db()
    if from_date == "" or to_date == "":
        from_date = str(datetime.now())
        to_date = str(datetime.now() + relativedelta(days=30))
    if from_date > to_date:
        flash("Invalid")
        return redirect(url_for("airline_staff.home"))
    my_flight = db.execute("select * from Flight JOIN "
                           "(SELECT airport_name, airport_city AS departure_city FROM airport) A1 "
                           "ON departure_airport=A1.airport_name "
                           "JOIN (SELECT airport_name, airport_city as arrival_city FROM airport) A2 "
                           "ON arrival_airport=A2.airport_name where airline_name=? and departure_airport LIKE ? "
                           "AND departure_city LIKE ? AND arrival_airport LIKE ? AND arrival_city LIKE ? "
                           "AND departure_time between ? and  ?",
                           (airline_name, depart_airport, depart_city, arrive_airport, arrive_city, from_date, to_date))
    return render_template('view_my_flights.html', my_flight=my_flight)

@as_bp.route('/staff_home', methods=('GET', 'POST'))
def home():
    return render_template('airline_staff/airline_staff.html')






