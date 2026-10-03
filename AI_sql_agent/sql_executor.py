import psycopg2
from config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

def run(sql):

    try:
        cur.execute(sql)
        return cur.fetchall()

    except Exception as e:
        return str(e)