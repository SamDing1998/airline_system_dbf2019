from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from flaskr.auth import login_required_customer
from flaskr.db import get_db

from dateutil.relativedelta import relativedelta
from datetime import datetime

from flaskr.db import get_db

customer_bp = Blueprint("customer", __name__, url_prefix="/customer")


@customer_bp.route('/customer_home', methods=('POST', 'GET'))
@login_required_customer
def home():
    return render_template('./customer/customer.html')



@customer_bp.route('/view_my_flights', methods=('POST', 'GET'))
@login_required_customer
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
            return redirect(url_for("customer.home"))

        cust_flights = db.execute("select * from flight JOIN "
                               "(SELECT airport_name, airport_city AS departure_city FROM airport) A1 "
                               "ON departure_airport=A1.airport_name "
                               "JOIN (SELECT airport_name, airport_city as arrival_city FROM airport) A2 "
                               "ON arrival_airport=A2.airport_name where airline_name=? and departure_airport LIKE ? "
                               "AND departure_city LIKE ? AND arrival_airport LIKE ? AND arrival_city LIKE ? "
                               "AND departure_time between ? and  ?",
                               (airline_name, departure_airport, departure_city, arrival_airport, arrival_city, begin_date, end_date)) # fetch all?

        return render_template('./customer/view_my_flights.html', cust_flights=cust_flights)
    return render_template('./customer/customer.html')



@customer_bp.route("/track_my_spending")
@login_required_customer
def track_my_spending():
    if request.method == "POST":
        # retrive values
        begin_date = request.form["begin_date"]
        end_date = request.form["end_date"]

        # get reference to database
        db = get_db()

        if begin_date == "" or end_date == "":
            begin_date = str(datetime.now() - relativedelta(months=6))
            end_date = str(datetime.now())
            sum_begin_date = str(datetime.now() - relativedelta(years=1))
        else:
            begin_date = begin_date + " 00:00:00"
            end_date = end_date + " 23:59:59"


            sum_begin_date = begin_date
        print(begin_date, end_date)
        if begin_date > end_date:
            flash("Invalid Date: Begin date > End date")
            return redirect(url_for("customer.home"))

        monthly_spending = db.execute("SELECT strftime('%Y', purchase_date) AS year, strftime('%m', purchase_date) AS month, SUM(price) AS sum ",
                                "FROM ( ticket NATURAL JOIN purchases NATURAL JOIN flight) as T ",
                                "WHERE customer_email = ? AND purchase_time BETWEEN ? AND ? ",
                                "GROUP BY year, month",
                               (g.user["email"], begin_date, end_date)).fetchall()

        total_spending = db.execute("SELECT SUM(price) as s "
                                    "FROM ticket NATURAL JOIN purchases NATURAL JOIN flight "
                                    "WHERE email = ? AND purchase_date BETWEEN ? AND ? ",
                                    (g.user["email"], sum_begin_date, end_date)).fetchone()['s']

        existing_spends = {}
        for row in monthly_spending:
            existing_spends[( int(row["year"]), int(row["month"]) )] = int(row["sum"])

        # spending data for ChartJS with complete timeline
        spending_chart_data = {}
        idx = 1

        # parse to int values
        start_year = int(begin_date[:4])
        start_month = int(begin_date[5:7])
        end_year = int(end_date[:4])
        end_month = int(end_date[5:7])

        for i in range(start_year, end_year + 1):
            # check year -> start/end month
            if i == start_year:
                startM = start_month
            else:
                startM = 1
            if i == end_year:
                endM = end_month
            else:
                endM = 12

            for j in range(startM, endM + 1):
                # create & append data point
                dp = {}
                dp["year"] = i
                dp["month"] = j
                if (i, j) in existing_spends.keys():
                    dp["sum"] = existing_spends[(i, j)]
                else:
                    dp["sum"] = 0
                dp["idx"] = idx
                #spending_chart_data.append(dp)
                spending_chart_data.update(dp)
                idx += 1

        return render_template('./customer/track_my_spending.html', spending_chart_data=spending_chart_data, dp_num=idx, total_spending=total_spending)
    return render_template('./customer/customer.html')

