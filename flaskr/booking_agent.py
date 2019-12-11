from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from flaskr.auth import login_required_
from flaskr.database import get_db

from dateutil.relativedelta import relativedelta
from datetime import datetime

agent_bp = Blueprint("agent", __name__, url_prefix="/booking_agent")


@agent.route('/booking_agent_home', methods=('POST', 'GET'))
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
        airline_name = request.form["airline_name"]

        # get reference to database
        db = get_db()

        if begin_date == "" or end_date == "":
            begin_date = str(datetime.now())
            end_date = str(datetime.now() + relativedelta(days=30))

        print(begin_date, end_date)
        if begin_date > end_date:
            flash("Invalid Date: Begin date > End date")
            return redirect(url_for(agent.home))

        cust_flights = db.execute("select * from flight JOIN "
                               "(SELECT airport_name, airport_city AS departure_city FROM airport) A1 "
                               "ON departure_airport=A1.airport_name "
                               "JOIN (SELECT airport_name, airport_city as arrival_city FROM airport) A2 "
                               "ON arrival_airport=A2.airport_name where airline_name=? and departure_airport LIKE ? "
                               "AND departure_city LIKE ? AND arrival_airport LIKE ? AND arrival_city LIKE ? "
                               "AND departure_time between ? and  ?",
                               (airline_name, departure_airport, departure_city, arrival_airport, arrival_city, from_date, to_date)) # fetch all?

        return render_template('./booking_agent/view_my_flights.html', cust_flights=cust_flights)
    return render_template('./booking_agent/booking_agent.html')



@agent.route("/view_top_customers")
@login_required_agent
def view_top_customers():
    if request.method == "POST":
        # values
        agent_email = g.user['email']
        now = str(datetime.now())
        num_top_begin = str(datetime.now() - relativedelta(months=6))
        sum_top_begin = str(datetime.now() - relativedelta(years=1))

        # get reference to database
        db = get_db()

        num_tops = db.execute("SELECT email, COUNT(*) as num FROM purchase WHERE booking_agent=? "
                                "AND purchase_date_time BETWEEN ? AND ?"
                                "GROUP BY cust_email ORDER BY num DESC LIMIT 5",
                                (agent_email, npm_top_begin, now))
        
        sum_tops = db.execute("SELECT email, SUM( price * 0.1) as comm_sum " 
                                "FROM (purchase NATURAL JOIN ticket) as P, flight as F "
                                "WHERE booking_agent=? "
                                "AND P.flight_num = F.flight_num"
                                "AND purchase_date_time BETWEEN ? AND ? "
                                "GROUP BY email ORDER BY comm_sum DESC LIMIT 5",
                                (agent_email, npm_top_begin, now))


        num_tops_list = []
        sum_tops_list = []

        idx = 1
        for row in num_tops:
            d = {}
            d["email"] = row["email"]
            d["count"] = row["num"]
            d["index"] = idx
            num_tops_list.append(d)
            idx += 1

        idx = 1
        for row in sum_tops:
            d = {}
            d["email"] = row["email"]
            d["sum"] = row["comm_sum"]
            d["index"] = index
            sum_tops_list.append(d)
            index += 1

        return render_template("view_top_customers.html", num_tops_list=num_tops_list, sum_tops_list=sum_tops_list)



@agent.route("/view_my_commissions")
@require_login_agent
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
            return redirect(url_for(agent.home))

        # SQL queries

        total_commission = db.execute("SELECT SUM(price * 0.1) as s "
                                    "FROM ticket NATURAL JOIN purchases NATURAL JOIN flight "
                                    "WHERE booking_agent_id = ? AND purchase_time BETWEEN ? AND ? ",
                                    (g.user["booking_agent_id"], begin_date, end_date)).fetchone()['s']

        average_commission = db.execute("SELECT AVG(price * 0.1) as a "
                                    "FROM ticket NATURAL JOIN purchases NATURAL JOIN flight "
                                    "WHERE booking_agent_id = ? AND purchase_time BETWEEN ? AND ? ",
                                    (g.user["booking_agent_id"], begin_date, end_date)).fetchone()['a']
        
        sold_ticket_num = db.execute("SELECT COUNT(*) as c "
                                    "FROM ticket NATURAL JOIN purchases NATURAL JOIN flight "
                                    "WHERE booking_agent_id = ? AND purchase_time BETWEEN ? AND ? ",
                                    (g.user["booking_agent_id"], begin_date, end_date)).fetchone()['c']
        

        return render_template('./booking_agent/view_my_commission.html', total_commission=total_commission, average_commission=average_commission, sold_ticket_num=sold_ticket_num)
    return render_template('./booking_agent/booking_agent.html')
    