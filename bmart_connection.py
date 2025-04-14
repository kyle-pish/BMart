'''
BMart Database Connection Helper Function
CS314 Spring 2025
Kyle Pish, Joel Madrigal, Gnandeep Chintala, Tom Komatsu
'''

import mysql.connector
from mysql.connector import Error


def connect_to_bmart_db(host, user, password, database):
    """
    BMart connection helper function
    Connects to the BMart MySQL database and returns connection and cursor.

    Params:
        host (str): Hostname of the MySQL server.
        user (str): Username to connect.
        password (str): Password to connect.
        database (str): Database name.

    Returns:
        conn, cursor: MySQL connection and cursor if successful, if unsuccessful then None is returned

    * To use helper function in other function files include: 'from bmart_connection import connect_to_bmart_db' *
    * To call function: conn, cursor = connect_to_bmart_db('cs314.iwu.edu', 'gjkt', 'H*aNjFho9q', 'gjkt') *
    """
    try:
        # Try starting a connection with the given info/credentials
        conn = mysql.connector.connect(host=host, user=user, password=password, database=database)

        # If the connection is successful
        if conn.is_connected():
            print("Connected to the BMart database.")
            # Create a cursor that will return the results of queries as dictionaries
            cursor = conn.cursor(dictionary=True)  # dictionary=True for column-name access
            return conn, cursor
    
    # If connection is not successful, display an error msg and return None for the connection and cursor
    except Error as e:
        print(f"Error: {e}")
        return None, None
    