import functools
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.auth import login_required_staff
from flaskr.db import get_db

as_bp = Blueprint('airline_staff', __name__, url_prefix='/airline_staff')


@as_bp.route('/view_my_flights', methods=('GET', 'POST'))
@login_required_staff
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
@login_required_staff
def home():
    return render_template('./airline_staff/airline_staff.html')


@as_bp.route('/view_booking_agents', methods=('GET', 'POST'))
@login_required_staff
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
@login_required_staff
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


@as_bp.route('/add_airplane', methods=('POST', 'GET'))
@login_required_staff
def add_airplane():
    airline_name = request.form['airline_name']
    airplane_id = request.form['airplane_id']
    seats = request.form['seats']
    db = get_db()
    error = None
    message = None
    if not airplane_id:
        error = "Plane ID Required!"
    elif not seats:
        error = "Seat Amount Required."
    elif db.execute('SELECT * FROM airplane WHERE airplane_id = ?', (airplane_id, )).fetchone() is not None:
        error = "The plane already exists."
    else:
        message = "You have successfully added the airplane"
    if error is None:
        db.execute("INSERT INTO Airplane(airline_name, airplane_id, seats) VALUES (?,?,?)", (airline_name, airplane_id, seats))
        db.commit()
    if error:
        flash(error)

    return redirect(url_for("airline_staff.home"))
@as_bp.route('/add_flight', methods=('POST', 'GET'))
@login_required_staff
def add_flight():
    airline_name = request.form['airline_name_flight']
    airplane_id = request.form['airplane_id_flight']
    flight_number = request.form['flight_number_flight']
    dtime = request.form['departure_time_flight'].split("T")
    atime = request.form['arrival_time_flight'].split("T")
    departure_time = dtime[0] + " " + dtime[1]
    departure_airport = request.form['departure_airport_flight']
    arrival_time = atime[0] + " " + atime[1]
    arrival_airport = request.form['arrival_airport_flight']
    price = request.form['price_flight']
    status = request.form['status_flight']
    db = get_db()
    if not airline_name:
        error = "Airline name is required"
    elif not flight_number:
        error = "Flight number is required"
    elif not airplane_id:
        error = "Plane ID is required"
    elif not dtime:
        error = "Departure time is required"
    elif not atime:
        error = "Arrival time is required"
    elif not departure_airport:
        error = "Departure airport is required"
    elif not arrival_airport:
        error = "Arrival airport is required"
    elif not price:
        error = "Price is required"
    elif not status:
        error = "Delay status is required"
    elif db.execute('SELECT * FROM Flight WHERE flight_num=? and airline_name=? and departure_time=?',
                    (flight_number, airline_name, departure_time)).fetchone() is not None:
        error = "The flight exists"
    elif db.execute('select * from Airplane where airline_name=? and  airplane_id=?',
                    (airline_name, airplane_id)).fetchone() is None:
        error = "The airplane does not exist"
    elif db.execute('select * from Airport where airport_name=?', (departure_airport,)).fetchone() is None:
        error = "The departure airport does not exist"
    elif db.execute('select * from Airport where airport_name=?', (arrival_airport,)).fetchone() is None:
        error = "The arrive airport does not exist"
    else:
        error = "You have successfully added the flight"
    if error == "You have successfully added the flight":
        db.execute("INSERT INTO "
                   "Flight(airplane_id, flight_num, airline_name, departure_time, arrival_time,"
                   " departure_airport, arrival_airport, price, status)"
                   "VALUES (?,?,?,?,?,?,?,?,?)",
                   (airplane_id, flight_number, airline_name, departure_time, arrival_time,
                    departure_airport, arrival_airport, price, status))
        db.commit()
    flash(error)
    return redirect(url_for("airline_staff.home"))

@as_bp.route('/add_airport', methods=('POST', 'GET'))
@login_required_staff
def add_airport():
    airport_name = request.form['airport_name']
    airport_city = request.form['airport_city']
    db = get_db()
    if db.execute('SELECT * FROM Airport WHERE airport_name=? ', (airport_name,)).fetchone() is not None:
        error = "The airport exists"
    else:
        error = "You have successfully added the airport"
    if error == "You have successfully added the airport":
        db.execute("INSERT INTO "
                   "airport(airport_name, airport_city)"
                   "VALUES (?,?)",
                   (airport_name, airport_city))
        db.commit()
    flash("Add Airport Status: " + error)
    return redirect(url_for('airline_staff.home'))

@as_bp.route('/change_status', methods=('POST', 'GET'))
@login_required_staff
def change_status():
    airline_name = request.form['airline_name_status']
    flight_num = request.form['flight_number_status']
    status = request.form['status']
    time = request.form['departure_time_status'].split("T")
    departure_time = time[0] + " " + time[1]
    db = get_db()
    if not flight_num:
        message = "Flight number is required"
    elif not departure_time:
        message = "Departure time is required"
    elif not status:
        message = "Status is required"
    elif db.execute('SELECT * FROM Flight WHERE airline_name=? and flight_num=? and departure_time=?',
                    (airline_name, flight_num, departure_time,)).fetchone() is None:
        message = "The flight is not found"
    elif db.execute('SELECT status FROM Flight WHERE airline_name=? and flight_num=? and departure_time=?',
                    (airline_name, flight_num, departure_time,)).fetchone()[0] == status:
        message = "Nothing is changed"
    else:
        message = "You have successfully changed the status"
        db.execute("UPDATE Flight SET status=? where airline_name=? and flight_num=? and departure_time=?",
                   (status, airline_name, flight_num, departure_time,))
        db.commit()

    flash('Change Status Result: ' + message)

    return redirect(url_for("airline_staff.home"))

@as_bp.route('/view_report', methods=('POST', 'GET'))
@login_required_staff
def view_report():
    if request.form["type"] == 'other':
        from_date = request.form["from_date"]
        to_date = request.form["to_date"]
        from_date = from_date + " 00:00:00"
        to_date = to_date + " 23:59:59"
    elif request.form["type"] == 'month':
        from_date = str(datetime.now() - relativedelta(months=1))
        to_date = str(datetime.now())
    else:
        from_date = str(datetime.now() - relativedelta(years=1))
        to_date = str(datetime.now())
    from_year = int(from_date[:4])
    from_month = int(from_date[5:7])
    to_year = int(to_date[:4])
    to_month = int(to_date[5:7])
    db = get_db()
    select = db.execute("SELECT strftime('%Y', purchase_date) AS year, strftime('%m', purchase_date) AS month, count(*) AS count "
                          "FROM (SELECT * FROM purchases WHERE purchase_date BETWEEN ? AND ?) as P "
                          "GROUP BY strftime('%Y', P.purchase_date), strftime('%m', P.purchase_date)",
                          (from_date, to_date))
    exist_count = {}
    for r in select:
        exist_count[(int(r["year"]), int(r["month"]))] = int(r["count"])
    spending = []
    index = 1
    for i in range(from_year, to_year + 1):

        if i == from_year:
            start = from_month
        else:
            start = 1
        if i == to_year:
            end = to_month
        else:
            end = 12

        for j in range(start, end + 1):
            d = {}
            d["year"] = i
            d["month"] = j
            if (i, j) in exist_count.keys():
                d["count"] = exist_count[(i, j)]
            else:
                d["count"] = 0
            d["index"] = index
            index += 1
            spending.append(d)
    return render_template('report.html', spending=spending)

@as_bp.route('/compare_revenue', methods=('POST', 'GET'))
@login_required_staff
def compare_revenue():
    db = get_db()
    cur = str(datetime.now())
    from_year = str(datetime.now() - relativedelta(years=1))
    from_month = str(datetime.now() - relativedelta(months=1))
    last_year_direct = db.execute("SELECT SUM(price) as s FROM purchases NATURAL JOIN Ticket NATURAL JOIN flight "
                                  "WHERE purchase_date between ? and ? AND airline_name=? AND booking_agent_id is NULL",
                                  (from_year, cur, g.user['airline_name'])).fetchone()["s"]
    last_year_indirect = db.execute("SELECT SUM(price) as s FROM purchases NATURAL JOIN Ticket NATURAL JOIN flight "
                                  "WHERE purchase_date between ? and ? AND airline_name=? AND booking_agent_id is not NULL",
                                  (from_year, cur, g.user['airline_name'])).fetchone()["s"]
    last_month_direct = db.execute("SELECT SUM(price) as s FROM purchases NATURAL JOIN Ticket NATURAL JOIN flight "
                                  "WHERE purchase_date between ? and ? AND airline_name=? AND booking_agent_id is NULL",
                                  (from_month, cur, g.user['airline_name'])).fetchone()["s"]
    last_month_indirect = db.execute("SELECT SUM(price) as s FROM purchases NATURAL JOIN Ticket NATURAL JOIN flight "
                                  "WHERE purchase_date between ? and ? AND airline_name=? AND booking_agent_id is not NULL",
                                  (from_month, cur, g.user['airline_name'])).fetchone()["s"]

    return render_template('./airline_staff/compare_revenue.html', last_year_direct=last_year_direct, last_year_indirect=last_year_indirect, last_month_direct=last_month_direct, last_month_indirect=last_month_indirect)

@as_bp.route('/logout', methods=('POST', 'GET'))
@login_required_staff
def logout():
    return render_template('auth/login.html')

@as_bp.route('/top_d', methods=('POST', 'GET'))
@login_required_staff
def top_d():
    from_date = str(datetime.now())
    to_date_month = str(datetime.now() - relativedelta(month=3))
    to_date_year = str(datetime.now() - relativedelta(year=1))
    db = get_db()
    month = db.execute("select airport_city from airport join flight on "
                       "Airport.airport_name=Flight.arrival_airport "
                       "inner join Ticket T on Flight.airline_name = T.airline_name and "
                       "Flight.flight_num = T.flight_num "
                       "inner  join purchases on purchases.ticket_id=T.ticket_id "
                       "where purchases.purchase_date between ? and ?"
                       "group by airport_city order by count(airport_city) desc limit 3", (to_date_month, from_date)).fetchall()
    year = db.execute("select airport_city from Airport inner join Flight on Airport.airport_name=Flight.arrival_airport "
                      "inner join Ticket T on Flight.airline_name = T.airline_name and "
                      "Flight.flight_num = T.flight_num "
                      "inner  join purchases on purchases.ticket_id=T.ticket_id "
                      "where purchases.purchase_date between ? and ?"
                      "group by airport_city order by count(airport_city) desc limit 3", (to_date_year, from_date)).fetchall()
    y = []
    for i in year:
        y.append(i['airport_city'])
    m = []
    for j in month:
        m.append(j['airport_city'])
    return render_template('./airline_staff/airline_staff.html', value1=m, value2=y)



