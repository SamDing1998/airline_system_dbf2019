import functools
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('airline_staff', __name__, url_prefix='/airline_staff')

@bp.route('/airline_staff', methods=('GET', 'POST'))

@bp.route('/view_my_flights', methods=('GET', 'POST'))
def view_my_flights():
    from_date = request.args["from_date"]
    to_date = request.args["to_date"]
    depart_airport = request.args["depart_airport"] + "%"
    arrive_airport = request.args["arrive_airport"] + "%"
    depart_city = request.args["depart_city"] + "%"
    arrive_city = request.args["arrive_city"] + "%"
    airline_name = request.args["airline_name"]

    db = get_db()
    if from_date == "" or to_date == "":
        from_date = str(datetime.now())
        to_date = str(datetime.now() + relativedelta(days=30))
    if from_date > to_date:
        flash("Invalid")
        return redirect(url_for("airline_staff.home"))
    my_flight = db.execute("select * from Flight JOIN "
                           "(SELECT airport_name, airport_city AS depart_city FROM airport) A "
                           "ON departure_airport=A.airport_name "
                           "JOIN (SELECT airport_name, airport_city as arrive_city FROM airport) A2 "
                           "ON arrival_airport=A2.airport_name where airline_name=? and departure_airport LIKE ? "
                           "AND depart_city LIKE ? AND arrival_airport LIKE ? AND arrive_city LIKE ? "
                           "AND departure_time between ? and  ?",
                           (airline_name, depart_airport, depart_city, arrive_airport, arrive_city, from_date, to_date))
    return render_template('view_future_flights.html', my_flight=my_flight)

def home():
    return render_template('airline_staff.html')





