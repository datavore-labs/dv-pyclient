from dv_pyclient.grpc import dataSources_pb2 as api
from dv_pyclient.grpc import dataSources_pb2_grpc as rpc

from sqlite3 import dbapi2 as sqlite
import psycopg2 as postgres

sampleDb = 'example.db'
txns = [
    ('2006-01-01', 'BUY', 'RHAT', 100, 35.00, 'USD'),
    ('2006-02-01', 'BUY', 'RHAT', 200, 32.00, 'USD'),
    ('2006-03-01', 'BUY', 'RHAT', 300, 34.00, 'USD'),
    ('2006-04-01', 'BUY', 'RHAT', 400, 35.10, 'USD'),
    ('2006-05-01', 'BUY', 'RHAT', 500, 35.20, 'USD'),
    ('2006-06-01', 'BUY', 'RHAT', 600, 35.30, 'USD'),

    ('2006-01-02', 'SELL', 'RHAT', 100, 35.60, 'USD'),
    ('2006-02-02', 'SELL', 'RHAT', 200, 32.60, 'USD'),
    ('2006-03-02', 'SELL', 'RHAT', 300, 34.60, 'USD'),
    ('2006-04-02', 'SELL', 'RHAT', 400, 35.60, 'USD'),
    ('2006-05-02', 'SELL', 'RHAT', 500, 35.60, 'USD'),
    ('2006-06-02', 'SELL', 'RHAT', 600, 35.60, 'USD'),

    ('2006-01-01', 'BUY', 'MSFT', 1100, 135.00, 'USD'),
    ('2006-02-01', 'BUY', 'MSFT', 1200, 132.00, 'USD'),
    ('2006-03-01', 'BUY', 'MSFT', 1300, 134.00, 'USD'),
    ('2006-04-01', 'BUY', 'MSFT', 1400, 135.10, 'USD'),
    ('2006-05-01', 'BUY', 'MSFT', 1500, 135.20, 'USD'),
    ('2006-06-01', 'BUY', 'MSFT', 1600, 135.30, 'USD'),

    ('2006-01-02', 'SELL', 'MSFT', 1100, 135.60, 'USD'),
    ('2006-02-02', 'SELL', 'MSFT', 1200, 132.60, 'USD'),
    ('2006-03-02', 'SELL', 'MSFT', 1300, 134.60, 'USD'),
    ('2006-04-02', 'SELL', 'MSFT', 1400, 135.60, 'USD'),
    ('2006-05-02', 'SELL', 'MSFT', 1500, 135.60, 'USD'),
    ('2006-06-02', 'SELL', 'MSFT', 1600, 135.60, 'USD'),
]

def add_fake_data(conn, query_param_type):
    c = conn.cursor()
    c.execute('''DROP TABLE IF EXISTS stocks ''')
    c.execute('''CREATE TABLE stocks(
        date date, 
        trans text, 
        symbol text, 
        qty real, 
        price real,
        currency text
    )''')
    param = "?" if query_param_type == 'qmark' else "%s"
    c.executemany(f'INSERT INTO stocks VALUES ({param}, {param}, {param}, {param}, {param}, {param})', txns)
    c.close()
    conn.commit()


def generateConfig(sql, con):
    c = con.cursor()
    c.execute(sql)
    meta = [description for description in c.description]
    print(meta)
    batch = c.fetchmany(3)
    while True:
        if not batch:
            break
        for row in batch:
            print(row)
        batch = c.fetchmany(3)
    c.close()


if __name__ == '__main__':

    pg_conn = postgres.connect("dbname='postgres' user='postgres' host='localhost' "
                               "password='mysecretpassword'")
    pg_query_param_type = postgres.paramstyle
    add_fake_data(pg_conn, pg_query_param_type)
    generateConfig("select * from stocks", pg_conn, pg_query_param_type)

    sqlite_query_param_type = sqlite.paramstyle
    sqlite_conn = sqlite.connect(sampleDb)
    add_fake_data(sqlite_conn, sqlite_query_param_type)
    generateConfig("select * from stocks", sqlite_conn)


