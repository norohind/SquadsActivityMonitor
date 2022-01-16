import json
import typing
import datetime

import psycopg2.extensions
import psycopg2.extras
import config

from .sqlite_cache import cache
from . import postgres_sql_requests
from .abstract_model import AbstractModel
import utils
from EDMCLogging import get_main_logger

logger = get_main_logger()
logger.propagate = False


def errors_catcher(func: callable) -> callable:
    def decorated(*args, **kwargs):
        try:
            result = func(*args, **kwargs)

        except psycopg2.InterfaceError:
            args[0].open_model()
            result = func(*args, **kwargs)

        return result

    return decorated


class PostgresModel(AbstractModel):
    db: psycopg2.extensions.connection

    def open_model(self):
        self.db: psycopg2.extensions.connection = psycopg2.connect(
            user=config.postgres_username,
            password=config.postgres_password,
            host=config.postgres_hostname,
            port=config.postgres_port,
            database=config.postgres_database_name,
            cursor_factory=psycopg2.extras.DictCursor)

        logger.info(f'Connected to {self.db.dsn}')

        with self.db:
            with self.db.cursor() as cursor:
                cursor.execute(postgres_sql_requests.schema_create)  # schema creation

    def close_model(self):
        self.db.close()
        logger.info(f'Connection to {self.db.dsn} closed successfully')

    @errors_catcher
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

    @errors_catcher
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

    @errors_catcher
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

    @errors_catcher
    def get_leaderboard_sum_history(self, platform: str, leaderboard_type: str) -> list[dict]:
        cache_key = f'sum_history_{platform}_{leaderboard_type}'
        cached_result: typing.Union[str, None] = cache.get(cache_key)

        if cached_result is not None:
            logger.debug(f'Cached result for {cache_key}')
            return json.loads(cached_result)

        with self.db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
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

    @errors_catcher
    def get_leaderboard_by_action_id(self, action_id: int) -> list[dict]:
        cache_key = f'leaderboard_by_action_id_{action_id}'

        cached_result: typing.Union[str, None] = cache.get(cache_key)

        if cached_result is not None:
            logger.debug(f'Cached result for {cache_key}')
            return json.loads(cached_result)

        with self.db.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
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
