import os
import shutil
import tempfile

import pytest
from flask import session, request, template_rendered
import coverage

from app import app, get_db, session, get_seats, DATABASE, log_payment, log_purchase


# cov = coverage.Coverage()
# cov.start()


# !! Tests may change as the backend is developed.

@pytest.fixture(scope='session')
def temp_db():
    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, 'test.db')

    shutil.copy(DATABASE, temp_db)

    app.config['DATABASE'] = temp_db
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    yield temp_db

    shutil.rmtree(temp_dir)


@pytest.fixture
def client(temp_db):
    with app.test_client() as client:
        print()
        yield client


@pytest.fixture
def logged_in_client(client):
    client.post("/login", data={
        "email":    "test1@email.com",
        "password": "1234"
    })

    assert 'account' in session, "Account was not found in session cookies."

    return client


@pytest.fixture
def logged_in_client_with_seat(logged_in_client, available_flight):
    cursor = get_db().cursor()
    cursor.execute('''
            SELECT * FROM SEATS WHERE FLIGHT_ID = ? AND AVAILABILITY = 1
        ''', (available_flight[0],))
    result = cursor.fetchone()
    cursor.close()
    logged_in_client.post(f"/seats/{available_flight[0]}", data={"seat": result[1]})
    confirm_data = {"flight_id": result[0], "seat_designation": result[1]}
    logged_in_client.post(f"/seats/confirm", data=confirm_data)

    assert 'seat' in session, "Seat could not be stored in session cookies."

    return logged_in_client


@pytest.fixture
def available_flight(client):
    cursor = get_db().cursor()
    cursor.execute('''
            SELECT * FROM SEATS WHERE AVAILABILITY = 1
        ''')
    seat = cursor.fetchone()
    cursor.execute('''
            SELECT * FROM FLIGHTS WHERE ID = ?
        ''', (seat[0],))
    flight = cursor.fetchone()
    cursor.close()

    assert flight is not None, "No available flights for the test"

    return flight


def test_can_unsuccessfully_register_password_mismatch(client):
    print(" - Running unsuccessful register due to password mismatch test")
    email = "test1@email.com"
    response = client.post("/register", follow_redirects=True, data={
        "email":            email,
        "password":         "1234",
        "password-confirm": "4321",
        "country":          "Canada"
    })
    assert response.status_code == 200
    assert response.request.path == "/register"

    cursor = get_db().cursor()
    result = cursor.execute('''
        SELECT * FROM ACCOUNTS WHERE EMAIL = ?
    ''', (email,)).fetchone()
    assert result is None, f"Account was found in database as {result}"
    cursor.close()
    print("PASSED")


def test_can_successfully_register(client):
    print(" - Running successful register test")
    email = "test1@email.com"
    response = client.post("/register", follow_redirects=True, data={
        "email":            email,
        "password":         "1234",
        "password-confirm": "1234",
        "country":          "Canada"
    })
    assert response.status_code == 200
    assert response.request.path == "/login"

    # Check new account was added:
    cursor = get_db().cursor()
    result = cursor.execute('''
        SELECT * FROM ACCOUNTS WHERE EMAIL = ?
    ''', (email,)).fetchone()
    assert result is not None
    assert result[1] == email
    cursor.close()
    print("PASSED")


def test_can_unsuccessfully_register_existing_email(client):
    print(" - Running unsuccessful register due to existing email test")
    response = client.post("/register", follow_redirects=True, data={
        "email":            "test1@email.com",
        "password":         "1234",
        "password-confirm": "1234",
        "country":          "Canada"
    })
    assert response.status_code == 200
    assert response.request.path == "/register"
    print("PASSED")


def test_can_unsuccessfully_login_wrong_password(client):
    print(" - Running unsuccessful login due to wrong password test")
    email = "test1@email.com"
    response = client.post("/login", follow_redirects=True, data={
        "email":    email,
        "password": "4321"
    })
    assert response.status_code == 200
    assert response.request.path == "/login"
    assert 'email' not in session
    print("PASSED")


def test_can_unsuccessfully_login_wrong_email(client):
    print(" - Running unsuccessful login due to wrong email test")
    response = client.post("/login", follow_redirects=True, data={
        "email":    "test2@email.com",
        "password": "1234"
    })
    assert response.status_code == 200
    assert response.request.path == "/login"
    assert 'email' not in session
    print("PASSED")


def test_can_successfully_login(client):
    print(" - Running successful login test")
    email = "test1@email.com"
    response = client.post("/login", follow_redirects=True, data={
        "email":    email,
        "password": "1234"
    })
    assert response.status_code == 200
    assert response.request.path == "/search"
    assert 'account' in session, "Logged in cookie not saved."
    assert session['account'][1] == email, f"Logged in cookie 'email' is not correctly {email}. session['email'] = {session['email']}."
    print("PASSED")


def test_can_unsuccessfully_view_history(logged_in_client):
    print(" - Running unsuccessful view history test")
    response = logged_in_client.get("/history")

    assert response.status_code == 200
    assert b'<div class="flight-history-result">' not in response.data
    assert b'No flight history' in response.data
    print("PASSED")


def test_can_unsuccessfully_search(logged_in_client):
    print(" - Running unsuccessful search test")
    response = logged_in_client.post("/search", data={
        "from":           "Not a city",
        "to":             "Still not a city",
        "departure-date": "1856-13-0",
        "return-date":    "1856-13-31",
    })

    assert response.status_code == 200
    assert b'<div class="flight-result">' not in response.data
    assert b'No flights found' in response.data
    print("PASSED")


def test_can_successfully_search(logged_in_client, available_flight):
    print(" - Running successful search test")

    response = logged_in_client.post("/search", data={
        "from":           available_flight[2],
        "to":             available_flight[3],
        "departure-date": available_flight[6],
        "return-date":    available_flight[7],
    })

    assert response.status_code == 200
    assert b'<div class="flight-result">' in response.data
    assert b'No flights found' not in response.data
    print("PASSED")


def test_can_successfully_select_seat(logged_in_client, available_flight):
    print(" - Running successful seat selection test")

    response = logged_in_client.get(f"/seats/{available_flight[0]}")
    assert response.status_code == 200, f"URL: /seats/{available_flight[0]} could not be found."

    cursor = get_db().cursor()
    cursor.execute('''
        SELECT * FROM SEATS WHERE FLIGHT_ID = ? AND AVAILABILITY = 1
    ''', (available_flight[0],))
    result = cursor.fetchone()
    cursor.close()

    response = logged_in_client.post(f"/seats/{available_flight[0]}", data={"seat": result[1]})

    assert response.status_code == 200, f"URL: /seats/{available_flight[0]} could not be found."
    assert f'<p class="seat-information-box-text">Seat {result[1]}</p>'.encode() in response.data, \
        f'"<p class="seat-information-box-text">Seat {result[1]}</p>" not found in data.'

    confirm_data = {"flight_id": result[0], "seat_designation": result[1]}
    response = logged_in_client.post(f"/seats/confirm", data=confirm_data, follow_redirects=True)

    assert response.status_code == 200, "URL: /seat/confirm could not be found."

    assert response.request.path == "/checkout", \
        f"URL is not /checkout. URL = {response.request.path}"

    assert 'seat' in session, "Seat could not be stored in session cookies."
    assert session['seat'] == result, \
        f'Seat stored in cookie is not the same as the selected seat. Cookie: "{session["seat"]}" Selected: "{result}"'

    assert f'Seat {result[1]} - {result[3]}'.encode() in response.data, \
        f'"Seat {result[1]} - {result[3]}" not found in data.'

    assert f'Ticket: ${result[2]}'.encode() in response.data, \
        f'"Ticket: ${result[2]}" not found in data.'
    print("PASSED")


def test_can_unsuccessfully_make_payment(logged_in_client_with_seat, available_flight):
    print(" - Running unsuccessful make payment test")
    seat = session['seat']

    checkout_data = {
        "card-number":     "1234567890123456",
        "cvv":             "123",
        "expiration":      "1984-01",
        "name":            "Test",
        "billing-address": "14 Road Street",
        "province":        "Ontario",
        "postal-code":     "A1B 2C3",
        "total-price":     "590.0"
    }
    response = logged_in_client_with_seat.post("/checkout", data=checkout_data, follow_redirects=True)
    assert response.status_code == 200, f"URL: {response.request.path} could not be found."
    assert response.request.path == "/checkout", f"URL is not /payment. URL = {response.request.path}"
    print("PASSED")


def test_can_successfully_make_payment(logged_in_client_with_seat, available_flight):
    print(" - Running successful make payment test")
    seat = session['seat']

    checkout_data = {
        "card-number":     "1234567890123456",
        "cvv":             "123",
        "expiration":      "2025-01",
        "name":            "Test",
        "billing-address": "14 Road Street",
        "province":        "Ontario",
        "postal-code":     "A1B 2C3",
        "total-price":     "590.0"
    }
    response = logged_in_client_with_seat.post("/checkout", data=checkout_data, follow_redirects=True)
    assert response.status_code == 200, f"URL: {response.request.path} could not be found."
    assert response.request.path == "/thank-you", f"URL is not /thank-you. URL = {response.request.path}"

    cursor = get_db().cursor()
    cursor.execute('''
        SELECT * FROM SEATS WHERE FLIGHT_ID = ? AND SEAT_DESIGNATION = ?
    ''', (seat[0], seat[1]))
    result = cursor.fetchone()

    assert result[4] == 0, "Seat was not set as unavailable."
    assert result[5] == session['account'][0], f"Seat's ACCOUNT_ID was not set to {session['account'][0]}."
    print("PASSED")


def test_can_successfully_view_history(logged_in_client):
    print(" - Running successful view history test")
    response = logged_in_client.get("/history")

    assert response.status_code == 200
    assert b'flight-history-result' in response.data
    assert b'No flights found' not in response.data
    print("PASSED")


def test_can_successfully_cancel_ticket(logged_in_client):
    print(" - Running successful cancel ticket test")

    purchase_number = 1
    response = logged_in_client.post("/cancel", data={
        "purchase-number": purchase_number
    }, follow_redirects=True)

    assert response.status_code == 200

    cursor = get_db().cursor()
    cursor.execute('''
            SELECT PAYMENTS.PAYMENT_STATUS, PURCHASE_HISTORY.FLIGHT_ID, PURCHASE_HISTORY.SEAT_DESIGNATION
            FROM PAYMENTS
            JOIN PURCHASE_HISTORY ON PAYMENTS.ID = PURCHASE_HISTORY.PAYMENT_ID
            WHERE PURCHASE_HISTORY.PURCHASE_NUMBER = ? AND PURCHASE_HISTORY.ACCOUNT_ID = ?
        ''', (purchase_number, session['account'][0]))
    result = cursor.fetchone()
    assert result[0] == "Cancelled"
    cursor.execute('''
            SELECT * FROM SEATS WHERE FLIGHT_ID = ? AND SEAT_DESIGNATION = ?
        ''', (result[1], result[2]))
    seat_result = cursor.fetchone()

    assert seat_result[4] == 1
    assert seat_result[5] is None

    cursor.close()
    print("PASSED")


def test_can_unsuccessfully_cancel_ticket(logged_in_client):
    print(" - Running unsuccessful cancel ticket test")

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO FLIGHTS (FLIGHT_NUMBER, ORIGIN, DESTINATION, ORIGIN_CODE, DESTINATION_CODE, DEPARTURE_DATE, RETURN_DATE, DEPARTURE_TIME, ARRIVAL_TIME)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', ("TEST001", "Toronto", "London", "YYZ", "LHR", "2023-04-11", "2023-04-21", "6:30", "8:30"))
    seat = [cursor.lastrowid, "A1", 500.0, "Economy", 0, session['account'][0]]
    cursor.execute('''
        INSERT INTO SEATS (FLIGHT_ID, SEAT_DESIGNATION, PRICE, CLASS, AVAILABILITY, ACCOUNT_ID)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', seat)
    cursor.close()
    db.commit()

    log_purchase(seat, 590.0, log_payment(590.0, "Success"))

    purchase_number = 2
    response = logged_in_client.post("/cancel", data={
        "purchase-number": purchase_number
    }, follow_redirects=True)

    assert response.status_code == 200

    cursor = get_db().cursor()

    cursor.execute('''
            SELECT PAYMENTS.PAYMENT_STATUS, PURCHASE_HISTORY.FLIGHT_ID, PURCHASE_HISTORY.SEAT_DESIGNATION
            FROM PAYMENTS
            JOIN PURCHASE_HISTORY ON PAYMENTS.ID = PURCHASE_HISTORY.PAYMENT_ID
            WHERE PURCHASE_HISTORY.PURCHASE_NUMBER = ? AND PURCHASE_HISTORY.ACCOUNT_ID = ?
        ''', (purchase_number, session['account'][0]))
    result = cursor.fetchone()
    assert result[0] == "Success"

    cursor.execute('''
            SELECT * FROM SEATS WHERE FLIGHT_ID = ? AND SEAT_DESIGNATION = ?
        ''', (result[1], result[2]))
    seat_result = cursor.fetchone()

    assert seat_result[4] == 0
    assert seat_result[5] is session['account'][0]

    cursor.close()
    print("PASSED")


# cov.stop()
# cov.save()
# cov.html_report()
