"""
Script to transfer data from sqlite DB to postgres DB
"""

import psycopg2.extensions
import psycopg2.extras
import sqlite3
from model import postgres_sql_requests
import time

insert_pg = """insert into squads_stats_states (action_id, leaderboard_type, platform, squadron_id, score, 
percentile, rank, name, tag, timestamp) 
values 
(%(action_id)s, %(leaderboard_type)s, %(platform)s, %(squadron_id)s, %(score)s, 
%(percentile)s, %(rank)s, %(name)s, %(tag)s, %(timestamp)s);"""

sqlite_conn: sqlite3.Connection = sqlite3.connect('squads_stat.sqlite3', check_same_thread=False)
sqlite_conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

pg_conn: psycopg2.extensions.connection = psycopg2.connect(
    user='user2',
    password='1',
    host='192.168.1.68',
    port='5432',
    database='test0'
    )

with pg_conn:
    with pg_conn.cursor() as cursor:
        cursor.execute(postgres_sql_requests.schema_create)

with pg_conn:
    with pg_conn.cursor() as cursor:
        start = time.time()

        insert_statement = ''
        sqlite_content = sqlite_conn.execute('select * from squads_stats_states;').fetchall()
        # for row in sqlite_content:
        #     # cursor.execute(insert_pg, row)
        #     insert_statement += cursor.mogrify(insert_pg, row).decode('utf-8')

        # print((time.time() - start) * 100, 'ms for creating insert_statement')
        # print('inserting')
        cursor.executemany(insert_pg, sqlite_content)
        # 149619.26856040955 ms total
        print((time.time() - start) * 100, 'ms total')

pg_conn.close()
sqlite_conn.close()

