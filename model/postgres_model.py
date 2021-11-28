import json
import os
import typing

import psycopg2.extensions
import psycopg2.extras

from .sqlite_cache import cache
from . import postgres_sql_requests
from .abstract_model import AbstractModel
import utils
from EDMCLogging import get_main_logger

logger = get_main_logger()
logger.propagate = False


class PostgresModel(AbstractModel):
    db: psycopg2.extensions.connection

    def open_model(self):
        self.db: psycopg2.extensions.connection = psycopg2.connect(
            user=os.environ['DB_USERNAME'],  # user2
            password=os.environ['DB_PASSWORD'],  # 1
            host=os.environ['DB_HOSTNAME'],  # 192.168.1.68
            port=os.environ['DB_PORT'],  # 5432
            database=os.environ['DB_DATABASE'],  # test0
            cursor_factory=psycopg2.extras.DictCursor)

        with self.db:
            with self.db.cursor() as cursor:
                cursor.execute(postgres_sql_requests.schema_create)  # schema creation

    def close_model(self):
        self.db.close()

    def get_activity_changes(self, platform: str, leaderboard_type: str, limit: int, low_timestamp, high_timestamp)\
            -> list:
        cache_key: str = f'{platform}_{leaderboard_type}_{limit}_{low_timestamp}_{high_timestamp}'
        cached_result: typing.Union[str, None] = cache.get(cache_key)

        if cached_result is not None:
            logger.debug(f'Cached result for {cache_key}')
            return json.loads(cached_result)

        logger.debug(f'Not cached result for {cache_key}')

        with self.db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
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

    def insert_leaderboard_db(self, leaderboard_list: dict) -> None:
        """
        Takes leaderboard as list, it platform, type, db connection and insert leaderboard to DB

        :param leaderboard_list: list from request_leaderboard
        :return:
        """

        platform: str = leaderboard_list['platform']
        LB_type: str = leaderboard_list['type']
        leaderboard: list = leaderboard_list['leaderboard']

        action_id: int  # not last, current that we will use

        with self.db.cursor() as cursor:
            cursor.execute(postgres_sql_requests.select_last_action_id)
            action_id_fetch_one: typing.Union[None, dict[str, int]] = cursor.fetchone()

        if action_id_fetch_one is None:
            # i.e. first launch
            action_id = 1  # yep, not 0

        else:
            action_id = action_id_fetch_one['action_id'] + 1

        # Patch for additional values
        for squad in leaderboard:
            squad.update({'action_id': action_id, 'LB_type': LB_type, 'platform': platform})

        with self.db:
            with self.db.cursor() as cursor:
                cursor.executemany(
                    postgres_sql_requests.insert_leader_board,
                    leaderboard)

        cache.delete_all()  # drop cache

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

        with self.db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(postgres_sql_requests.select_diff_by_action_id, {'action_id': action_id})
            result: list = cursor.fetchall()

        if not cache.disabled:
            cache.set(cache_key, json.dumps(result))

        return result
