from flask import Blueprint
import psycopg2

data_api = Blueprint('data_api', __name__)

def get_db_connection():
    conn = psycopg2.connect(host='localhost',
                            database='db',
                            user='postgres',
                            password='postgres_pass',
                            port=5433)
    return conn

@data_api.route('/dataapi/read')
def test1():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM read_heavy;')
    books = cur.fetchall()
    cur.close()
    conn.close()
    return f"{len(books)}"