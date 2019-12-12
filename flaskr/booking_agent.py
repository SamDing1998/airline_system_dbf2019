from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from flaskr.auth import login_required_agent
from flaskr.db import get_db

from dateutil.relativedelta import relativedelta
from datetime import datetime

agent_bp = Blueprint("agent", __name__, url_prefix="/booking_agent")


@agent_bp.route('/booking_agent_home', methods=('POST', 'GET'))
@login_required_agent
def home():
    return render_template('./booking_agent/booking_agent.html')



@agent_bp.route('/view_my_flights', methods=('POST', 'GET'))
@login_required_agent
def view_my_flights():
    if request.method == "POST":
        # retrive values
        begin_date = request.form["begin_date"]
        end_date = request.form["end_date"]
        departure_city = request.form["departure_city"] + "%"
        departure_airport = request.form["departure_airport"] + "%"
        arrival_airport = request.form["departure_city"] + "%"
        arrival_city = request.form["arrival_city"] + "%"
        airline_name = request.form["airline_name"] + "%"

        # get reference to database
        db = get_db()

        if begin_date == "" or end_date == "":
            begin_date = str(datetime.now())
            end_date = str(datetime.now() + relativedelta(days=30))

        print(begin_date, end_date)
        if begin_date > end_date:
            flash("Invalid Date: Begin date > End date")
            return redirect(url_for("agent.home"))
        db.execute("SELECT * FROM purchases ")
        my_flights = db.execute('SELECT * FROM purchases NATURAL JOIN Ticket NATURAL JOIN flight '
                       'JOIN (SELECT airport_name, airport_city as depart_city FROM Airport) A ON departure_airport=A.airport_name '
                       'JOIN (SELECT airport_name, airport_city as arrive_city FROM Airport) A2 ON arrival_airport=A2.airport_name '
                       'WHERE booking_agent_id=? AND departure_airport LIKE ? AND depart_city LIKE ? AND arrival_airport LIKE ? AND arrive_city LIKE ?'
                       'AND departure_time BETWEEN ? AND ? AND airline_name LIKE ?',
                       (g.user['booking_agent_id'], departure_airport, departure_city, arrival_airport, arrival_city, begin_date, end_date, airline_name)).fetchall()
        print(my_flights)
        for r in my_flights:
            print(r['airline_name'])
        return render_template('./booking_agent/view_my_flights.html', my_flights=my_flights)
    return render_template('./booking_agent/booking_agent.html')



@agent_bp.route("/view_top_customers", methods=('POST', 'GET'))
@login_required_agent
def view_top_customers():
    if request.method == "POST":
        # values
        booking_agent_id= g.user['booking_agent_id']
        now = str(datetime.now())
        num_top_begin = str(datetime.now() - relativedelta(months=6))
        sum_top_begin = str(datetime.now() - relativedelta(years=1))

        print(1)
        print(1)
        print(now)
        print(num_top_begin)
        print(sum_top_begin)
        print(agent_email)

        # get reference to database
        db = get_db()

        num_tops = db.execute("SELECT customer_email, COUNT(*) as num FROM purchases WHERE booking_agent_id= ? "
                                "AND purchase_date BETWEEN ? AND ?"
                                "GROUP BY customer_email ORDER BY num DESC LIMIT 5",
                                (booking_agent_id, num_top_begin, now)).fetchall()
        print(g.user['booking_agent_id'], num_tops)

        sum_tops = db.execute("SELECT customer_email, SUM( price * 0.1) as comm_sum " 
                                "FROM (purchases NATURAL JOIN ticket) as P, flight as F "
                                "WHERE booking_agent_id = ? "
                                "AND P.flight_num = F.flight_num "
                                "AND purchase_date BETWEEN ? AND ? "
                                "GROUP BY customer_email ORDER BY comm_sum DESC LIMIT 5",
                                (booking_agent_id, sum_top_begin, now)).fetchall()

        num_tops_list = []
        sum_tops_list = []

        print(1)
        print(1)
        print(num_tops)
        print(1)        
        print(1)

        idx = 1
        for row in num_tops:
            d = {}

            d["email"] = row["customer_email"]
            print(d['email'])
            d["count"] = row["num"]
            d["index"] = idx
            num_tops_list.append(d)
            idx += 1

        idx = 1
        for row in sum_tops:
            d = {}
            d["email"] = row["customer_email"]
            d["sum"] = row["comm_sum"]
            d["index"] = idx
            sum_tops_list.append(d)
            idx += 1
        print(num_tops_list, sum_tops_list)

        return render_template("./booking_agent/view_top_customers.html", num_tops_list=num_tops_list, sum_tops_list=sum_tops_list)
    return render_template('./booking_agent/booking_agent.html')



@agent_bp.route("/view_my_commissions", methods=('GET', 'POST'))
@login_required_agent
def view_my_commissions():
    if request.method == "POST":
        # retrive values
        begin_date = request.form["begin_date"]
        end_date = request.form["end_date"]

        # get reference to database
        db = get_db()

        if begin_date == "" or end_date == "":
            begin_date = str(datetime.now() - relativedelta(days=30))
            end_date = str(datetime.now())
        else:
            begin_date = begin_date + " 00:00:00"
            end_date = end_date + " 23:59:59"

        print(begin_date, end_date)

        if begin_date > end_date:
            flash("Invalid Date: Begin date > End date")
            return redirect(url_for("agent.home"))

        # SQL queries

        total_commission = db.execute("SELECT SUM(price * 0.1) as s "
                                    "FROM ticket NATURAL JOIN purchases NATURAL JOIN flight "
                                    "WHERE booking_agent_id = ? AND purchase_date BETWEEN ? AND ? ",
                                    (g.user["booking_agent_id"], begin_date, end_date)).fetchone()['s']

        average_commission = db.execute("SELECT AVG(price * 0.1) as a "
                                    "FROM ticket NATURAL JOIN purchases NATURAL JOIN flight "
                                    "WHERE booking_agent_id = ? AND purchase_date BETWEEN ? AND ? ",
                                    (g.user["booking_agent_id"], begin_date, end_date)).fetchone()['a']
        
        sold_ticket_num = db.execute("SELECT COUNT(*) as c "
                                    "FROM ticket NATURAL JOIN purchases NATURAL JOIN flight "
                                    "WHERE booking_agent_id = ? AND purchase_date BETWEEN ? AND ? ",
                                    (g.user["booking_agent_id"], begin_date, end_date)).fetchone()['c']
        

        return render_template('./booking_agent/view_my_commissions.html', total_commission=total_commission, average_commission=average_commission, sold_ticket_num=sold_ticket_num)
    return render_template('./booking_agent/booking_agent.html')
    
