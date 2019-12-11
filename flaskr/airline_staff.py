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
    print(request.form)
    if request.method == "POST":
        from_date = request.form["from_date"]
        to_date = request.form["to_date"]
        departure_airport = request.form["departure_airport"] + "%"
        arrival_airport = request.form["arrival_airport"] + "%"
        departure_city = request.form["departure_city"] + "%"
        arrival_city = request.form["arrival_city"] + "%"
        airline_name = request.form["airline_name"]

        db = get_db()
        if from_date == "" or to_date == "":
            from_date = str(datetime.now())
            to_date = str(datetime.now() + relativedelta(days=30))
        print(from_date, to_date)
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
                               (airline_name, departure_airport, departure_city, arrival_airport, arrival_city, from_date, to_date))
        return render_template('airline_staff/view_my_flights.html', my_flight=my_flight)
    return render_template('airline_staff/airline_staff.html')


@as_bp.route('/staff_home', methods=('GET', 'POST'))
def home():
    return render_template('airline_staff/airline_staff.html')






