import sqlite3 as db
import random

# NOTE:
# Debug account is 'hello@email.com' with password '1234'.

conn = db.connect('app/db/flyoda.db')


def random_flight_number():
    airline_codes = ['WJA', 'NVC', 'VKN', 'TSC', 'ACA']

    return f"{random.choice(airline_codes)}{random.randint(100, 999)}"


flights = [
    ("ACA190", "Toronto", "London", "YYZ", "LHR", "2024-11-20", "2024-11-21", "06:30", "08:30"),
    ("DL105", "New York", "Paris", "JFK", "CDG", "2024-11-22", "2024-11-29", "19:45", "08:15"),
    ("UA450", "Chicago", "Tokyo", "ORD", "HND", "2024-12-01", "2024-12-15", "12:00", "16:30"),
    ("BA287", "San Francisco", "London", "SFO", "LHR", "2024-12-05", "2024-12-12", "15:50", "09:25"),
    ("LH431", "Chicago", "Frankfurt", "ORD", "FRA", "2024-11-18", "2024-11-28", "15:40", "06:55"),
    ("AF009", "New York", "Paris", "JFK", "CDG", "2024-12-08", "2024-12-15", "18:00", "07:35"),
    ("SQ025", "Los Angeles", "Singapore", "LAX", "SIN", "2024-12-10", "2024-12-24", "14:30", "01:00"),
    ("QF008", "Dallas", "Sydney", "DFW", "SYD", "2024-12-20", "2025-01-05", "21:15", "07:10"),
    ("EK202", "New York", "Dubai", "JFK", "DXB", "2024-11-25", "2024-12-10", "22:20", "19:40"),
    ("JL043", "San Francisco", "Tokyo", "SFO", "NRT", "2024-11-27", "2024-12-12", "14:50", "19:10"),
    ("CA986", "Los Angeles", "Beijing", "LAX", "PEK", "2024-12-03", "2024-12-18", "12:30", "18:50"),
    ("VA008", "Los Angeles", "Melbourne", "LAX", "MEL", "2024-11-28", "2024-12-13", "23:30", "10:30"),
    ("LH401", "New York", "Frankfurt", "JFK", "FRA", "2024-11-22", "2024-11-30", "16:20", "05:30"),
    ("AA108", "Dallas", "London", "DFW", "LHR", "2024-11-23", "2024-12-03", "20:15", "09:30"),
    ("NZ001", "San Francisco", "Auckland", "SFO", "AKL", "2024-12-02", "2024-12-18", "22:15", "07:00"),
    ("UA869", "San Francisco", "Singapore", "SFO", "SIN", "2024-12-04", "2024-12-20", "01:15", "12:05"),
    ("BR015", "Los Angeles", "Taipei", "LAX", "TPE", "2024-11-29", "2024-12-15", "11:20", "17:45"),
    ("MH091", "Los Angeles", "Kuala Lumpur", "LAX", "KUL", "2024-12-06", "2024-12-22", "12:30", "20:10"),
    ("QF010", "London", "Sydney", "LHR", "SYD", "2024-11-24", "2024-12-14", "22:05", "06:05"),
    ("AF065", "Los Angeles", "Paris", "LAX", "CDG", "2024-11-26", "2024-12-10", "15:30", "11:05"),
]

seats = [
    ("1A", 5000, "Business"), ("1B", 5000, "Business"),
    ("2A", 5000, "Business"), ("2B", 5000, "Business"),
    ("2C", 5000, "Business"), ("2D", 5000, "Business"),
    ("3A", 500, "Economy"), ("3B", 500, "Economy"), ("3C", 500, "Economy"), ("3D", 500, "Economy"),
    ("4A", 500, "Economy"), ("4B", 500, "Economy"), ("4C", 500, "Economy"), ("4D", 500, "Economy"),
    ("5A", 500, "Economy"), ("5B", 500, "Economy"), ("5C", 500, "Economy"), ("5D", 500, "Economy"),
    ("6A", 500, "Economy"), ("6B", 500, "Economy"), ("6C", 500, "Economy"), ("6D", 500, "Economy"),
    ("7A", 500, "Economy"), ("7B", 500, "Economy"), ("7C", 500, "Economy"), ("7D", 500, "Economy"),
    ("8A", 500, "Economy"), ("8B", 500, "Economy"), ("8C", 500, "Economy"), ("8D", 500, "Economy"),
    ("9A", 500, "Economy"), ("9B", 500, "Economy"), ("9C", 500, "Economy"), ("9D", 500, "Economy"),
    ("10A", 500, "Economy"), ("10B", 500, "Economy"), ("10C", 500, "Economy"), ("10D", 500, "Economy"),
    ("11A", 500, "Economy"), ("11B", 500, "Economy"), ("11C", 500, "Economy"), ("11D", 500, "Economy"),
    ("12A", 500, "Economy"), ("12B", 500, "Economy"), ("12C", 500, "Economy"), ("12D", 500, "Economy"),
    ("13A", 500, "Economy"), ("13B", 500, "Economy"), ("13C", 500, "Economy"), ("13D", 500, "Economy"),
]


def add_flight(origin, destination, origin_code, destination_code, departure_date, return_date, departure_time, arrival_time):
    cursor = conn.cursor()
    flight_number = random.randint(111111, 999999)
    cursor.execute('''
        INSERT INTO FLIGHTS (FLIGHT_NUMBER, ORIGIN, DESTINATION, ORIGIN_CODE, DESTINATION_CODE, DEPARTURE_DATE, RETURN_DATE, DEPARTURE_TIME, ARRIVAL_TIME)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (flight_number, origin, destination, origin_code, destination_code, departure_date, return_date, departure_time, arrival_time))
    conn.commit()
    cursor.close()


def add_many_flights(flight_list, seat_list=None):
    cursor = conn.cursor()
    for flight in flight_list:
        cursor.execute('''
            INSERT INTO FLIGHTS (FLIGHT_NUMBER, ORIGIN, DESTINATION, ORIGIN_CODE, DESTINATION_CODE, DEPARTURE_DATE, RETURN_DATE, DEPARTURE_TIME, ARRIVAL_TIME)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (flight[0], flight[1], flight[2], flight[3], flight[4], flight[5], flight[6], flight[7], flight[8]))
        if seat_list: add_seats_to_flight(cursor.lastrowid, seat_list)
    conn.commit()
    cursor.close()


def add_seats_to_flight(flight_id, seat_list):
    cursor = conn.cursor()
    insert_query = '''
        INSERT INTO SEATS (FLIGHT_ID, SEAT_DESIGNATION, PRICE, CLASS, AVAILABILITY)
        VALUES (?, ?, ?, ?, ?)
    '''
    is_empty = random.randint(0, 1) == 1
    for seat in seat_list:
        cursor.execute(insert_query, (flight_id, seat[0], seat[1], seat[2], 1 if is_empty else random.randint(0, 1)))

    conn.commit()
    cursor.close()


def delete_account_by_email(email):
    cursor = conn.cursor()
    cursor.execute('''
    DELETE FROM ACCOUNTS WHERE EMAIL = ?
    ''', (email,))
    conn.commit()
    cursor.close()


def create_history(email, flight_id, seat_designation):
    cursor = conn.cursor()
    cursor.execute('''
    SELECT 1 FROM ACCOUNTS WHERE EMAIL = ?
    ''', (email,))
    account = cursor.fetchone()

    cursor.execute('''
    INSERT INTO PURCHASE_HISTORY(USER_ID, PURCHASE_NUMBER, FLIGHT_ID, SEAT_DESIGNATION, PURCHASE_PRICE, PURCHASE_DATE, PAYMENT_ID, PAYMENT_STATUS) 
    VALUES (?,?,?,?,?,?,?,?)
    ''', (account[0], -1, flight_id, seat_designation, 5000, "2024-11-03", -1, "Completed"))
    conn.commit()
    cursor.close()


# -- CODE TO EXECUTE:
# cursor = conn.cursor()
# cursor.execute('''
#     DROP TABLE PURCHASE_HISTORY
# ''')
# cursor.execute('''
#     DROP TABLE PAYMENTS
# ''')
# cursor.execute('''
#     UPDATE SEATS SET AVAILABILITY = 1, ACCOUNT_ID = null WHERE FLIGHT_ID = 1 AND SEAT_DESIGNATION = "2D"
#
# ''')
# conn.commit()

# --

conn.close()
