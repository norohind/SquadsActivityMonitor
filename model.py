import sqlite3
import typing

import sql_requests
import utils


db: sqlite3.Connection = sqlite3.connect('squads_stat.sqlite3', check_same_thread=False)

db.executescript(sql_requests.schema_create)  # schema creation

# thx https://stackoverflow.com/a/48789604
db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))


def get_activity_changes(platform: str, leaderboard_type: str, limit: int, low_timestamp, high_timestamp) -> list:
    sql_req: sqlite3.Cursor = db.execute(sql_requests.select_activity, {
        'LB_type': utils.LeaderboardTypes(leaderboard_type.lower()).value,
        'platform': utils.Platform(platform.upper()).value,
        'limit': limit,
        'high_timestamp': high_timestamp,
        'low_timestamp': low_timestamp
    })

    return sql_req.fetchall()


def insert_leaderboard_db(leaderboard_list: dict) -> None:
    """
    Takes leaderboard as list, it platform, type, db connection and insert leaderboard to DB

    :param leaderboard_list: list from request_leaderboard
    :return:
    """

    platform: str = leaderboard_list['platform']
    LB_type: str = leaderboard_list['type']
    leaderboard: list = leaderboard_list['leaderboard']

    action_id: int  # not last, current that we will use

    sql_req_action_id: sqlite3.Cursor = db.execute(sql_requests.select_last_action_id)
    action_id_fetch_one: typing.Union[None, dict[str, int]] = sql_req_action_id.fetchone()
    if action_id_fetch_one is None:
        # i.e. first launch
        action_id = 1  # yep, not 0

    else:
        action_id = action_id_fetch_one['action_id'] + 1

    # Patch for additional values
    for squad in leaderboard:
        squad.update({'action_id': action_id, 'LB_type': LB_type, 'platform': platform})

    with db:
        db.executemany(
            sql_requests.insert_leader_board,
            leaderboard)
