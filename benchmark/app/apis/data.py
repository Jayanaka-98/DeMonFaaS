from flask import Blueprint
import psycopg2
import random

data_api = Blueprint('data_api', __name__)

def get_db_connection():
    conn = psycopg2.connect(host='localhost',
                            database='db',
                            user='postgres',
                            password='postgres_pass',
                            port=5433)
    return conn

@data_api.route('/dataapi/read')
def test_read():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM read_heavy;')
    books = cur.fetchall()
    cur.close()
    conn.close()
    return f"{len(books)}"

@data_api.route('/dataapi/write')
def test_write():
    conn = get_db_connection()
    cur = conn.cursor()
    random_num = random.randint(1, 1000000)
    changes = 0
    for i in range(2000):
        cur.execute(f"INSERT INTO write_heavy (write_id, write_name) VALUES ({random_num}, '{i}')")
        changes += 1
    for i in range(2000):
        cur.execute(f"DELETE FROM write_heavy WHERE write_id={random_num} and write_name='{i}'")
        changes += 1
    cur.close()
    conn.close()
    return f"Changes: {changes}"