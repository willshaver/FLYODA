import sqlite3 as db

conn = db.connect('app/db/flyoda.db')

create_accounts_table_query = '''CREATE TABLE IF NOT EXISTS ACCOUNTS 
                                (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                                 EMAIL          TEXT NOT NULL, 
                                 PASSWORD_HASH  TEXT NOT NULL, 
                                 COUNTRY        TEXT NOT NULL
                                 );'''

conn.execute(create_accounts_table_query)

create_flights_table_query = '''CREATE TABLE IF NOT EXISTS FLIGHTS 
                                (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                                 FLIGHT_NUMBER      TEXT NOT NULL,
                                 ORIGIN             TEXT NOT NULL, 
                                 DESTINATION        TEXT NOT NULL, 
                                 ORIGIN_CODE        CHAR(3) NOT NULL, 
                                 DESTINATION_CODE   CHAR(3) NOT NULL, 
                                 DEPARTURE_DATE     DATE NOT NULL,  
                                 RETURN_DATE        DATE NOT NULL, 
                                 DEPARTURE_TIME     TIME NOT NULL, 
                                 ARRIVAL_TIME       TIME NOT NULL
                                 );'''

conn.execute(create_flights_table_query)

create_seats_table_query = '''CREATE TABLE IF NOT EXISTS SEATS
                                (FLIGHT_ID          INTEGER NOT NULL,
                                 SEAT_DESIGNATION   TEXT NOT NULL, -- A1, A2, A3, B1, etc
                                 PRICE              REAL NOT NULL,
                                 CLASS              TEXT NOT NULL,
                                 AVAILABILITY       BOOLEAN NOT NULL,
                                 ACCOUNT_ID         INTEGER,
                                 PRIMARY KEY (FLIGHT_ID, SEAT_DESIGNATION),
                                 FOREIGN KEY (ACCOUNT_ID) REFERENCES ACCOUNTS(ID),
                                 FOREIGN KEY (FLIGHT_ID) REFERENCES FLIGHTS(ID)
                                 );'''

conn.execute(create_seats_table_query)

create_payments_table_query = '''CREATE TABLE IF NOT EXISTS PAYMENTS
                                (ID             INTEGER PRIMARY KEY AUTOINCREMENT,
                                 ACCOUNT_ID     INTEGER NOT NULL,
                                 AMOUNT         REAL NOT NULL,
                                 PAYMENT_DATE   DATE NOT NULL, 
                                 PAYMENT_STATUS TEXT NOT NULL, -- Confirmed, Cancelled, Failed
                                 FOREIGN KEY (ACCOUNT_ID) REFERENCES ACCOUNTS(ID)
                                );'''

conn.execute(create_payments_table_query)

create_purchase_history_table_query = '''CREATE TABLE IF NOT EXISTS PURCHASE_HISTORY
                                (ACCOUNT_ID         INTEGER NOT NULL,
                                 PURCHASE_NUMBER    INTEGER NOT NULL,
                                 FLIGHT_ID          INTEGER NOT NULL,
                                 SEAT_DESIGNATION   TEXT NOT NULL,
                                 PURCHASE_PRICE     REAL NOT NULL,
                                 PURCHASE_DATE      DATE NOT NULL,
                                 PAYMENT_ID         INTEGER NOT NULL,
                                 PRIMARY KEY (ACCOUNT_ID, PURCHASE_NUMBER),
                                 FOREIGN KEY (ACCOUNT_ID) REFERENCES ACCOUNTS(ID),
                                 FOREIGN KEY (FLIGHT_ID, SEAT_DESIGNATION) REFERENCES SEATS(FLIGHT_ID, SEAT_DESIGNATION),
                                 FOREIGN KEY (PAYMENT_ID) REFERENCES PAYMENTS(ID)
                                 );'''

conn.execute(create_purchase_history_table_query)

conn.close()
