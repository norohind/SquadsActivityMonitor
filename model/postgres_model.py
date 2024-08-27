import json
import typing
import datetime

import psycopg2.extensions
import psycopg2.extras
from psycopg2 import pool
import config

from .sqlite_cache import cache
from . import postgres_sql_requests
from .abstract_model import AbstractModel
import utils
from EDMCLogging import get_main_logger

logger = get_main_logger()
logger.propagate = False


class PostgresModel(AbstractModel):
    db_pool: psycopg2.extensions.connection

    def open_model(self):
        self.db_pool: pool.ThreadedConnectionPool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            user=config.postgres_username,
            password=config.postgres_password,
            host=config.postgres_hostname,
            port=config.postgres_port,
            database=config.postgres_database_name,
            cursor_factory=psycopg2.extras.DictCursor)

        conn: psycopg2.extensions.connection = self.db_pool.getconn()
        logger.info(f'Connected to {conn.dsn}')

        with conn:
            with conn.cursor() as cursor:
                cursor.execute(postgres_sql_requests.schema_create)  # schema creation

    def close_model(self):
        self.db_pool.closeall()
        logger.info(f'Connection to db closed successfully')

    def get_activity_changes(self, platform: str, leaderboard_type: str, limit: int, low_timestamp, high_timestamp)\
            -> list:
        cache_key: str = f'{platform}_{leaderboard_type}_{limit}_{low_timestamp}_{high_timestamp}'
        cached_result: typing.Union[str, None] = cache.get(cache_key)

        if cached_result is not None:
            logger.debug(f'Cached result for {cache_key}')
            return json.loads(cached_result)

        logger.debug(f'Not cached result for {cache_key}')

        if low_timestamp is None and high_timestamp is None and limit is None:
            # let's apply an optimization: use yesterday's date as minimal date
            high_timestamp = '3307-12-12'
            low_timestamp = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        if low_timestamp is None:
            low_timestamp = '0001-01-01'

        if high_timestamp is None:
            high_timestamp = '3307-12-12'

        if limit is None:
            limit = 10

        conn = self.db_pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(postgres_sql_requests.select_activity_pretty_names, {
                    'LB_type': utils.LeaderboardTypes(leaderboard_type.lower()).value,
                    'platform': utils.Platform(platform.upper()).value,
                    'limit': limit,
                    'high_timestamp': high_timestamp,
                    'low_timestamp': low_timestamp
                })

                result: list = cursor.fetchall()

            if not cache.disabled:
                cache.set(cache_key, json.dumps(result))

            return result

        finally:
            self.db_pool.putconn(conn)

    def insert_leaderboard_db(self, leaderboard_list: dict) -> int:
        """
        Takes leaderboard as list, it platform, type, db connection and insert leaderboard to DB

        :param leaderboard_list: list from request_leaderboard
        :return:
        """

        platform: str = leaderboard_list['platform']
        LB_type: str = leaderboard_list['type']
        leaderboard: list = leaderboard_list['leaderboard']

        action_id: int  # not last, current that we will use

        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(postgres_sql_requests.create_new_action_id, {'LB_type': LB_type, 'platform': platform})
                action_id: int = cursor.fetchone()[0]

                # Patch for additional values
                for squad in leaderboard:
                    squad.update({'action_id': action_id})

                cursor.executemany(postgres_sql_requests.insert_leaderboard, leaderboard)

            conn.commit()

            cache.delete_all()  # drop cache
            return action_id

        finally:
            self.db_pool.putconn(conn)

    def get_diff_action_id(self, action_id: int) -> list:
        """
        Takes action_id and returns which squadrons has been changed in leaderboard as in action_id and
        experience they got in compassion to action_id - 1 for the same leaderboard and platform

        :param action_id:
        :return:
        """
        cache_key: str = f'{action_id}'
        cached_result: typing.Union[str, None] = cache.get(cache_key)

        if cached_result is not None:
            logger.debug(f'Cached result for {cache_key}')
            return json.loads(cached_result)

        logger.debug(f'Not cached result for {cache_key}')

        conn = self.db_pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(postgres_sql_requests.select_diff_by_action_id, {'action_id': action_id})
                result: list = cursor.fetchall()

            if not cache.disabled:
                cache.set(cache_key, json.dumps(result))

            return result

        finally:
            self.db_pool.putconn(conn)

    def get_leaderboard_sum_history(self, platform: str, leaderboard_type: str) -> list[dict]:
        cache_key = f'sum_history_{platform}_{leaderboard_type}'
        cached_result: typing.Union[str, None] = cache.get(cache_key)

        if cached_result is not None:
            logger.debug(f'Cached result for {cache_key}')
            return json.loads(cached_result)

        conn = self.db_pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    postgres_sql_requests.select_leaderboard_sum_history,
                    {
                        'LB_type': utils.LeaderboardTypes(leaderboard_type.lower()).value,
                        'platform': utils.Platform(platform.upper()).value}
                )
                result: list = cursor.fetchall()

            if not cache.disabled:
                cache.set(cache_key, json.dumps(result))

            return result

        finally:
            self.db_pool.putconn(conn)

    def get_leaderboard_by_action_id(self, action_id: int) -> list[dict]:
        cache_key = f'leaderboard_by_action_id_{action_id}'

        cached_result: typing.Union[str, None] = cache.get(cache_key)

        if cached_result is not None:
            logger.debug(f'Cached result for {cache_key}')
            return json.loads(cached_result)

        conn = self.db_pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    postgres_sql_requests.select_leaderboard_by_action_id,
                    {
                        'action_id': action_id
                    }
                )

                result: list[dict] = cursor.fetchall()

            if not cache.disabled:
                cache.set(cache_key, json.dumps(result))

            return result

        finally:
            self.db_pool.putconn(conn)

    def get_latest_leaderboard(self, platform: str, leaderboard_type: str) -> list[dict]:
        cache_key = f'latest_leaderboard_{platform}_{leaderboard_type}'
        cached_result: typing.Union[str, None] = cache.get(cache_key)

        if cached_result is not None:
            logger.debug(f'Cached result for {cache_key}')
            return json.loads(cached_result)

        logger.debug(f'Not cached result for {cache_key}')

        conn = self.db_pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    postgres_sql_requests.select_latest_leaderboard,
                    {
                        'platform': platform.upper(),
                        'LB_type': leaderboard_type.lower()
                    }
                )
                result: list[dict] = cursor.fetchall()

            if not cache.disabled:
                cache.set(cache_key, json.dumps(result))

            return result

        finally:
            self.db_pool.putconn(conn)
