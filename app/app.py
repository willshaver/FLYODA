# Allow users to purchase flight tickets from a database of flights.
# Users can register, log-in, search for flight, select their seat and pay, as well as check their history of bought tickets with the app.
# View readme-first.md in Assignment-3 folder for instructions on running.

import datetime
import os

from flask import Flask, render_template, request, redirect, url_for, g, session
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
import sqlite3

import db
from project.models import PaymentInformation

# import test_app

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'gEdNsh1k@Bc@d9!@'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'db', 'flyoda.db')
app.config['DATABASE'] = DATABASE


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'public, max-age=86400'
    return response


def check_logged_in():
    return 'account' in session


def log_in(account):
    session['account'] = account


def create_account(email, password, country):
    password_hash = generate_password_hash(password)
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO ACCOUNTS(EMAIL, PASSWORD_HASH, COUNTRY)
        VALUES (?, ?, ?)''', (email, password_hash, country))
    cursor.close()
    db.commit()


def get_account(email):
    cursor = get_db().cursor()
    cursor.execute('''
        SELECT * FROM ACCOUNTS WHERE EMAIL = ?
    ''', (email,))
    result = cursor.fetchone()
    cursor.close()
    return result


def get_current_account():
    return session['account']


def check_existing_account(email):
    cursor = get_db().cursor()
    cursor.execute('''
        SELECT TRUE FROM ACCOUNTS WHERE EMAIL = ?
    ''', (email,))
    result = cursor.fetchone()
    cursor.close()
    return result


def check_correct_password(email, password):
    cursor = get_db().cursor()
    cursor.execute('''
        SELECT PASSWORD_HASH FROM ACCOUNTS WHERE EMAIL = ?
    ''', (email,))
    result = cursor.fetchone()
    cursor.close()
    return check_password_hash(result[0], password) if result else False


def get_flight(flight_id):
    cursor = get_db().cursor()
    cursor.execute('''
        SELECT * FROM FLIGHTS WHERE ID = ?
    ''', (flight_id,))
    result = cursor.fetchone()
    cursor.close()
    return result


def get_flights_search(origin, destination, departure_date, return_date):
    cursor = get_db().cursor()
    cursor.execute('''
        SELECT * FROM FLIGHTS WHERE ORIGIN = ? AND DESTINATION = ? AND DEPARTURE_DATE = ? AND RETURN_DATE = ?
    ''', (origin, destination, departure_date, return_date))
    result = cursor.fetchall()
    cursor.close()
    return result


def get_seats(flight_id):
    cursor = get_db().cursor()
    cursor.execute('''
        SELECT * FROM SEATS WHERE FLIGHT_ID = ? AND AVAILABILITY = 1
        ORDER BY 
            CAST(SUBSTR(SEAT_DESIGNATION, 1, LENGTH(SEAT_DESIGNATION) - 1) AS INTEGER),
            SUBSTR(SEAT_DESIGNATION, LENGTH(SEAT_DESIGNATION), 1)
    ''', (flight_id,))
    result = cursor.fetchall()
    cursor.close()
    return result


def get_seat(flight_id, seat_designation):
    cursor = get_db().cursor()
    cursor.execute('''
        SELECT * FROM SEATS WHERE FLIGHT_ID = ? AND SEAT_DESIGNATION = ?
    ''', (flight_id, seat_designation))
    result = cursor.fetchone()
    cursor.close()
    return result


def check_seat_availability(flight_id, seat_designation):
    cursor = get_db().cursor()
    cursor.execute('''
        SELECT AVAILABILITY FROM SEATS WHERE FLIGHT_ID = ? AND SEAT_DESIGNATION = ?
    ''', (flight_id, seat_designation))
    result = cursor.fetchone()
    cursor.close()
    return result[0] == 1


def check_payment(information: PaymentInformation, seat):
    # Check seat is still available:
    if not check_seat_availability(seat[0], seat[1]):
        print("Seat not available.")
        return False

    # Check length of card number:
    if not 15 <= len(information.card_number) <= 16:
        print(information.card_number)
        return False

    # Check length of cvv:
    if not len(information.cvv) == 3:
        print(information.cvv)
        return False

    # Check valid expiration:
    exp_year, exp_month = (int(x) for x in information.expiration.split('-'))
    today = datetime.date.today()
    if (exp_year == today.year and exp_month <= today.month) or exp_year < today.year:
        print(f"Exp: {exp_year}-{exp_month} < Today: {today.year}-{today.month}")
        return False

    return True


def log_payment(amount, status):
    # Make sure user is logged in:
    if not check_logged_in():
        return -1

    account = get_current_account()

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO PAYMENTS(ACCOUNT_ID, AMOUNT, PAYMENT_STATUS, PAYMENT_DATE)
        VALUES (?, ?, ?, DATETIME('now'))
    ''', (account[0], amount, status))
    new_payment = cursor.lastrowid
    cursor.close()
    db.commit()
    return new_payment


def log_purchase(seat, price, payment_id):
    # Make sure user is logged in:
    if not check_logged_in():
        return -1

    account = get_current_account()  # Get account.

    db = get_db()
    cursor = db.cursor()

    # Get next purchase ID for the current user:
    cursor.execute('''
        SELECT COALESCE(MAX(PURCHASE_NUMBER), 0) + 1 FROM PURCHASE_HISTORY WHERE ACCOUNT_ID = ? 
    ''', (account[0],))
    next_purchase_number = cursor.fetchone()[0]

    # Add purchase to history:
    cursor.execute('''
        INSERT INTO PURCHASE_HISTORY(ACCOUNT_ID, PURCHASE_NUMBER, FLIGHT_ID, SEAT_DESIGNATION, PURCHASE_PRICE, PURCHASE_DATE, PAYMENT_ID)
        VALUES (?, ?, ?, ?, ?, DATETIME('now'), ?)
    ''', (account[0], next_purchase_number, seat[0], seat[1], price, payment_id))

    # Add user to seat:
    cursor.execute('''
        UPDATE SEATS SET AVAILABILITY = 0, ACCOUNT_ID = ? WHERE FLIGHT_ID = ? AND SEAT_DESIGNATION = ?
    ''', (account[0], seat[0], seat[1]))

    cursor.close()
    db.commit()


def get_history(account_id):
    cursor = get_db().cursor()

    cursor.execute('''
        SELECT FLIGHTS.*, SEATS.CLASS, PURCHASE_HISTORY.PURCHASE_NUMBER, PURCHASE_HISTORY.PURCHASE_PRICE, PAYMENTS.PAYMENT_STATUS
        FROM PURCHASE_HISTORY
        JOIN SEATS ON PURCHASE_HISTORY.FLIGHT_ID = SEATS.FLIGHT_ID AND PURCHASE_HISTORY.SEAT_DESIGNATION = SEATS.SEAT_DESIGNATION
        JOIN FLIGHTS ON PURCHASE_HISTORY.FLIGHT_ID = FLIGHTS.ID
        JOIN PAYMENTS ON PURCHASE_HISTORY.PAYMENT_ID = PAYMENTS.ID
        WHERE PURCHASE_HISTORY.ACCOUNT_ID = ?
        ORDER BY FLIGHTS.DEPARTURE_DATE ASC
    ''', (account_id,))
    result = cursor.fetchall()
    cursor.close()

    return result


def get_purchase(account_id, purchase_number):
    cursor = get_db().cursor()

    cursor.execute('''
        SELECT PURCHASE_HISTORY.*, FLIGHTS.DEPARTURE_DATE, SEATS.CLASS, PAYMENTS.PAYMENT_STATUS
        FROM PURCHASE_HISTORY
        JOIN FLIGHTS ON PURCHASE_HISTORY.FLIGHT_ID = FLIGHTS.ID
        JOIN SEATS ON PURCHASE_HISTORY.FLIGHT_ID = SEATS.FLIGHT_ID AND PURCHASE_HISTORY.SEAT_DESIGNATION = SEATS.SEAT_DESIGNATION
        JOIN PAYMENTS ON PURCHASE_HISTORY.PAYMENT_ID = PAYMENTS.ID
        WHERE PURCHASE_HISTORY.ACCOUNT_ID = ? AND PURCHASE_HISTORY.PURCHASE_NUMBER = ?
    ''', (account_id, purchase_number))
    result = cursor.fetchone()
    cursor.close()

    return result


def remove_purchase(account_id, purchase_number):
    purchase = get_purchase(account_id, purchase_number)

    if purchase[9] != "Success":
        return -1

    today = datetime.date.today()
    dep_year, dep_month, dep_day = (int(x) for x in purchase[7].split('-'))

    # If the flight is too soon to cancel:
    if (dep_year == today.year and dep_month == today.month and dep_day <= today.day) or \
            (dep_year == today.year and dep_month < today.month) or dep_year < today.year:
        print("Flight is departing too soon/already happened. Unable to cancel.")
        return -1

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        UPDATE PAYMENTS SET PAYMENT_STATUS = "Cancelled"
        WHERE PAYMENTS.ID = ?
    ''', (purchase[6],))
    cursor.execute('''
        UPDATE SEATS SET AVAILABILITY = 1, ACCOUNT_ID = null WHERE FLIGHT_ID = ? AND SEAT_DESIGNATION = ?
    ''', (purchase[2], purchase[3]))
    cursor.close()
    db.commit()


@app.route('/')
def index():
    # If already logged in, redirect to search page:
    if check_logged_in():
        return redirect(url_for('search'))
    # Go to login page:
    return redirect(url_for('login'))


# For testing purposes, ignore.
@app.route('/test', methods=['GET', 'POST'])
def test():
    if request.method == 'POST':
        user_input = request.form['user_input']
        return render_template('index.html', user_input=user_input)
    return render_template('index.html', user_input=None)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Check account credentials:
        if check_correct_password(email, password):
            log_in(get_account(email))
            return redirect(url_for('search'))
        # If the email/password is incorrect:
        else:
            return render_template('login.html', password_incorrect=True)

    # If the user is logged in, redirect to the index and handle from there:
    if check_logged_in():
        return redirect(url_for('index'))
    # If the user is not logged in, render the login page:
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        password_confirm = request.form['password-confirm']
        country = request.form['country']
        # --Temporary account register mockup:
        # If the password and the password confirmation are not the same, display an error:
        if password != password_confirm:
            return render_template('register.html', password_mismatch=True)
        # If an account with the specified email already exists, display an error:
        if check_existing_account(email):
            return render_template('register.html', email_exists=True)

        # Add the account to the account db:
        create_account(email, password, country)

        # Redirect to the login page:
        return redirect(url_for('login'))

    # If the user is logged in, redirect to the index and handle from there:
    if check_logged_in():
        return redirect(url_for('index'))
    # If the user is not logged in, render the register page:
    return render_template('register.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        origin = request.form["from"]
        destination = request.form["to"]
        departure_date = request.form["departure-date"]
        return_date = request.form["return-date"]

        # Get the flights that match the specified details:
        flights = get_flights_search(origin, destination, departure_date, return_date)
        # Render the search page with the search results:
        return render_template("flight_search.html", flights=flights, origin=origin, destination=destination, departure_date=departure_date, return_date=return_date)
    # Render the search page:
    return render_template("flight_search.html")


@app.route('/seats')
def seats_invalid():
    return redirect(url_for('index'))


@app.route('/seats/<int:flight_id>', methods=['GET', 'POST'])
def seats(flight_id):
    # Redirect if the flight_id does not correspond to an existing flight in the database:
    if not get_flight(flight_id):
        return redirect(url_for('seats_invalid'))

    selected_seat = None

    # Get all the seats that are available:
    available_seats = get_seats(flight_id)

    if request.method == 'POST':
        selected_seat_id = request.form['seat']
        # Get the seat object for the selected seat id:
        for seat in available_seats:
            if seat[1] == selected_seat_id:
                selected_seat = seat
                break

    # Render the seat map with the selection form using the available seats as options and show the selected seat if one is selected:
    return render_template('seatmap.html', flight_id=flight_id, available_seats=available_seats, selected_seat=selected_seat)


@app.route('/seats/confirm', methods=['GET', 'POST'])
def seat_confirm():
    if request.method != 'POST':
        return redirect(url_for('index'))

    flight_id = request.form['flight_id']
    seat_designation = request.form['seat_designation']

    session['seat'] = get_seat(flight_id, seat_designation)

    return redirect(url_for('checkout'))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'seat' not in session or not check_logged_in():
        return redirect(url_for('index'))

    seat = session['seat']

    if request.method == 'POST':
        # Get card information:
        card_number = request.form['card-number']
        cvv = request.form['cvv']
        expiration = request.form['expiration']
        name = request.form['name']
        billing_address = request.form['billing-address']
        province = request.form['province']
        postal_code = request.form['postal-code']
        payment_information = PaymentInformation(card_number, cvv, expiration, name, billing_address, province, postal_code)

        # Get purchase information:
        total_price = request.form['total-price']

        # Check if payment is not valid and log:
        if not check_payment(payment_information, seat):
            log_payment(total_price, "Failed")
            return render_template('payment.html', seat=seat, payment_information=PaymentInformation, payment_failed=True)

        # If payment is valid, log successful payment and add purchase to the purchase history:
        payment_id = log_payment(total_price, "Success")
        log_purchase(seat, total_price, payment_id)

        return redirect(url_for('payment_success'))

    return render_template('payment.html', seat=seat)


@app.route('/thank-you')
def payment_success():
    if not 'seat' in session:
        return redirect(url_for('index'))

    seat = session.pop('seat')

    flight = get_flight(seat[0])
    departure_date = datetime.date(*(int(x) for x in flight[6].split("-")))
    departure_day = departure_date.day
    departure_month = departure_date.strftime("%B")

    return render_template('payment_success.html', origin=flight[2], destination=flight[3], departure_day=departure_day, departure_month=departure_month)


@app.route('/history', methods=['GET', 'POST'])
def history():
    if not check_logged_in():
        return redirect(url_for('index'))

    user_history = get_history(get_current_account()[0])

    # If cancelling flight:
    if request.method == 'POST':
        purchase_number = request.form['purchase-number']
        cancel_purchase = get_purchase(get_current_account()[0], purchase_number)
        return render_template("flight_history.html", history=user_history, cancel_purchase=cancel_purchase)

    return render_template("flight_history.html", history=user_history)


@app.route('/cancel', methods=['GET', 'POST'])
def cancel_purchase():
    if request.method != 'POST' or not check_logged_in():
        return redirect(url_for('index'))

    # Perform flight cancellation:
    purchase_number = request.form['purchase-number']
    remove_purchase(get_current_account()[0], purchase_number)

    return redirect(url_for('history'))


if __name__ == '__main__':
    app.run(debug=True, port=8090)
