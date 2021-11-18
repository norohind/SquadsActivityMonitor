import sqlite3
import sql_requests
import utils


db: sqlite3.Connection = sqlite3.connect('squads_stat.sqlite3', check_same_thread=False)

# thx https://stackoverflow.com/a/48789604
db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

cur = db.cursor()


def get_activity_changes(platform: str, leaderboard_type: str, limit: int, low_timestamp, high_timestamp) -> list:
    sql_req: sqlite3.Cursor = db.execute(sql_requests.select_activity, {
        'LB_type': utils.LeaderboardTypes(leaderboard_type.lower()).value,
        'platform': utils.Platform(platform.upper()).value,
        'limit': limit,
        'high_timestamp': high_timestamp,
        'low_timestamp': low_timestamp
    })

    return sql_req.fetchall()
