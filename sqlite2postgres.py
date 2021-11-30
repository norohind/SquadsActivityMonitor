"""
Script to transfer data from sqlite DB to postgres DB
"""

import psycopg2.extensions
import psycopg2.extras
import sqlite3
from model import postgres_sql_requests
import config
import sys

insert_pg = """insert into squads_stats_states (action_id, leaderboard_type, platform, squadron_id, score, 
percentile, rank, name, tag, timestamp) 
values 
(%(action_id)s, %(leaderboard_type)s, %(platform)s, %(squadron_id)s, %(score)s, 
%(percentile)s, %(rank)s, %(name)s, %(tag)s, %(timestamp)s);"""

insert_sqlite = """insert into squads_stats_states (action_id, leaderboard_type, platform, squadron_id, score, 
percentile, rank, name, tag, timestamp) 
values 
(:action_id, :leaderboard_type, :platform, :squadron_id, :score, 
:percentile, :rank, :name, :tag, :timestamp);"""

sqlite_conn: sqlite3.Connection = sqlite3.connect(config.sqlite2postgres_sqlite_location, check_same_thread=False)
sqlite_conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

pg_conn: psycopg2.extensions.connection = psycopg2.connect(
        user=config.postgres_username,
        password=config.postgres_password,
        host=config.postgres_hostname,
        port=config.postgres_port,
        database=config.postgres_database_name,
    )

with pg_conn:
    with pg_conn.cursor() as cursor:
        cursor.execute(postgres_sql_requests.schema_create)


def initial_pull_sqlite_to_postgres() -> None:
    """
    Function for initial transferring data from sqlite to postgres

    :return:
    """

    with pg_conn:
        with pg_conn.cursor() as cursor:

            sqlite_content = sqlite_conn.execute('select * from squads_stats_states;').fetchall()
            cursor.executemany(insert_pg, sqlite_content)


def continues_pull_sqlite_to_postgres() -> None:
    """
    Function to synchronize data from sqlite to postgres table

    :return:
    """

    with pg_conn:
        with pg_conn.cursor() as cursor:
            cursor: psycopg2.extensions.cursor
            cursor.execute('select action_id from squads_stats_states order by action_id desc limit 1;')
            last_action_id_postgres: int = cursor.fetchone()[0]

            new_records = sqlite_conn.execute('select * from squads_stats_states where action_id > :action_id;',
                                              {'action_id': last_action_id_postgres}).fetchall()

            cursor.executemany(insert_pg, new_records)


def continues_pull_postgres_to_sqlite() -> None:
    with pg_conn:
        with pg_conn.cursor() as cursor:
            cursor: psycopg2.extensions.cursor
            l_act_id = sqlite_conn.execute('select action_id from squads_stats_states order by action_id desc limit 1;')
            last_action_id_sqlite: int = l_act_id.fetchone()['action_id']

            cursor.execute('select * from squads_stats_states where action_id > %(action_id)s;',
                           {'action_id': last_action_id_sqlite})
            new_records = cursor.fetchall()

            with sqlite_conn:
                sqlite_conn.executemany(insert_sqlite, new_records)


cli_error = 'argument must be "initial" or "continues"'

if len(sys.argv) != 2:
    print(cli_error)
    pg_conn.close()
    sqlite_conn.close()
    exit(1)

if sys.argv[1] == 'initial':
    initial_pull_sqlite_to_postgres()
    pg_conn.close()
    sqlite_conn.close()

elif sys.argv[1] == 'continues':
    continues_pull_sqlite_to_postgres()
    pg_conn.close()
    sqlite_conn.close()

elif sys.argv[1] == 'continues_to_sqlite':
    continues_pull_postgres_to_sqlite()
    pg_conn.close()
    sqlite_conn.close()

else:
    print(cli_error)


pg_conn.close()
sqlite_conn.close()

