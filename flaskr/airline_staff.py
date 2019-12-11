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
                               "AND departure_time between ? and ?",
                               (airline_name, departure_airport, departure_city, arrival_airport, arrival_city, from_date, to_date))
        return render_template('airline_staff/view_my_flights.html', my_flight=my_flight)
    return render_template('airline_staff/airline_staff.html')


@as_bp.route('/staff_home', methods=('GET', 'POST'))
def home():
    return render_template('airline_staff/airline_staff.html')

@as_bp.route('/view_booking_agents', methods=('GET', 'POST'))
def view_booking_agents():
    db = get_db()
    from_date = str(datetime.now())
    to_date_month = str(datetime.now() - relativedelta(days=30))
    to_date_year = str(datetime.now() - relativedelta(year=1))
    ticket_num_month = db.execute("SELECT booking_agent_id, COUNT(*) as count FROM purchases "
                                  "where booking_agent_id is not null and purchase_date between ? and ?"
                                  "GROUP BY booking_agent_id ORDER BY count DESC LIMIT 5", (to_date_month, from_date))
    ticket_num_year = db.execute("SELECT booking_agent_id, COUNT(*) as count FROM purchases "
                                 "where booking_agent_id is not null and  purchase_date between ? and ?"
                                 "GROUP BY booking_agent_id ORDER BY count DESC LIMIT 5", (to_date_year, from_date))
    commission = db.execute("SELECT booking_agent_id, SUM(price * 0.1) as total_commission FROM purchases JOIN ticket JOIN flight "
                            "where booking_agent_id is not null and purchase_date between ? and ? and purchases.ticket_id == ticket.ticket_id and flight.flight_num == ticket.flight_num "
                            "GROUP BY booking_agent_id ORDER BY total_commission DESC LIMIT 5", (to_date_year, from_date))
    return render_template('airline_staff/view_booking_agents.html',
                           ticket_num_month=ticket_num_month, ticket_num_year=ticket_num_year, commission=commission)
@as_bp.route('/view_customers', methods=('GET', 'POST'))
def view_customers():
    airline_name = request.form['airline_name']
    try:
        cust_email = request.form['cust_email']
    except:
        cust_email = None
    from_date = str(datetime.now())
    to_date = str(datetime.now() - relativedelta(year=1))
    db = get_db()
    cust = db.execute("select email, name, count(ticket_id) as count1 from "
                      "Customer natural join purchases natural join Ticket "
                      "where airline_name=? and purchase_date between ? and ?"
                      "group by email "
                      "having count1 = "
                      "(select max(c) from "
                      "(select count(ticket_id) as c from "
                      "Customer natural join purchases natural join Ticket "
                      "where airline_name=? and purchase_date between ? and ?"
                      "group by email))",
                      (airline_name, to_date, from_date, airline_name, to_date, from_date))
    if cust_email:
        result = db.execute("select distinct Flight.flight_num, Flight.departure_time from "
                            "Customer natural join purchases natural join Ticket join Flight "
                            "on Ticket.flight_num=Flight.flight_num "
                            "and Ticket.airline_name=Flight.airline_name "
                            "where Flight.airline_name=? and email=?", (airline_name, cust_email))
    else:
        result = []

    return render_template('airline_staff/view_customers.html', cust=cust, result=result)





