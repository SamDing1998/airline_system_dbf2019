from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from flaskr.authentication import login_required

from flaskr.database import get_db

import random
from datetime import datetime
from dateutil.relativedelta import relativedelta

public_bp = Blueprint("public", __name__, url_prefix="/search")

@public_bp.route('/search', methods=('POST', 'GET'))
def search():
    return render_template('./auth/search_for_flights.html')


@public_bp.route('/search_results', methods=('POST', 'GET'))
def search_result():
    if request.method == "POST":
        # retrive values
        begin_date = request.form["begin_date"]
        end_date = request.form["end_date"]
        departure_city = request.form["departure_city"] + "%"
        departure_airport = request.form["departure_airport"] + "%"
        arrival_airport = request.form["departure_city"] + "%"
        arrival_city = request.form["arrival_city"] + "%"

        # get reference to database
        db = get_db()

        if begin_date == "" and end_date == "":
            begin_date = str(datetime.now())
            end_date = str(datetime.now() + relativedelta(days=7))
        elif begin_date == "":
            begin_date = str(datetime.now() - relativedelta(days=7))
        elif end_date == "":
            end_date = str(datetime.now() + relativedelta(days=7))

        if begin_date > end_date:
            flash("Invalid Date: Begin date > End date")
            return redirect(url_for(public.search))
        
        result_flights = db.execute("select * from Flight JOIN "
                               "(SELECT airport_name, airport_city AS departure_city FROM airport) A1 "
                               "ON departure_airport=A1.airport_name "
                               "JOIN (SELECT airport_name, airport_city as arrival_city FROM airport) A2 "
                               "ON arrival_airport=A2.airport_name where departure_airport LIKE ? "
                               "AND departure_city LIKE ? AND arrival_airport LIKE ? AND arrival_city LIKE ? "
                               "AND departure_time between ? and ?",
                               (departure_airport, departure_city, arrival_airport, arrival_city, begin_date, end_date)).fetchall()

        return render_template('customer/search_result.html', result_flights=result_flights)
    return render_template('auth/login.html')


@public_bp.route('/purchase', methods=('POST', 'GET'))
@login_required
def purchase():
    flight_num = request.args["flight_number"]
    airline_name = request.args["airline_name"]
    
    db = get_db()
    target_flight = db.execute(
        'SELECT * FROM flight '
        'WHERE flight_num=? AND airline_name=?',
        (flight_num, airline_name)).fetchone()


    # GET
    if request.method == 'GET':
        return render_template('./auth/make_purchase.html', target_flight=target_flight)

    # POST
    if request.method == "POST":
        error = None

        # necessary info
        ticket_id = random.randint(1, 1e7)
        customer_email = g.user["email"] if g.type == "customer" else request.form["customer_email"]
        purchase_date = datetime.date.today()

        if error:
            print("error:", error)
            flash(error)
            return render_template('./auth/purchase.html', target_flight=target_flight)
        
        if not db.execute("SELECT * FROM customer WHERE email=?", (customer_email)).fetchone():
            error = "Customer does not exist."
        
        if g.type != "booking_agent":
            booking_agent_id = None
        else:
            booking_agent_id = g.user["booking_agent_id"]

        db.execute('INSERT INTO Ticket (ticket_id, airline_name, flight_num) VALUES '
                   '(?, ?, ?)', (ticket_id, airline_name, flight_num))
        db.execute('INSERT INTO Purchase (ticket_id, customer_email, booking_agent_id, purchase_date) VALUES '
                   '(?, ?, ?, ?)', (ticket_id, customer_email, booking_agent_email, purchase_date))
        db.commit()

        print("Purchase POST finished")
        return redirect(url_for('public.search'))