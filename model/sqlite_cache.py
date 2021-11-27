import sqlite3
from EDMCLogging import get_main_logger

logger = get_main_logger()


class Cache:
    def __init__(self, disabled: bool = False):
        self.disabled = disabled

        if disabled:
            return

        try:
            self.db: sqlite3.Connection = sqlite3.connect('squads_stat_cache.sqlite3', check_same_thread=False)

        except Exception as e:
            logger.warning('Cannot create cache DB due to', exc_info=e)
            logger.warning('Cache is disabled')
            self.disabled = True
            return

        self.db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

        with self.db:
            self.db.execute("create table if not exists cache (key text unique, value text);")

    def set(self, key, value) -> None:
        if self.disabled:
            return

        with self.db:
            if self.db.execute('select count(key) as count from cache where key = ?;', [key]).fetchone()['count'] == 1:

                # key exists, just need to update value
                self.db.execute('update cache set value = ? where key = ?;', [value, key])
            else:

                # key doesn't exists, need to insert new row
                self.db.execute('insert into cache (key, value) values (?, ?);', [key, value])

    def get(self, key, default=None):
        if self.disabled:
            return

        res = self.db.execute('select value from cache where key = ?;', [key]).fetchone()
        if res is None:
            return default

        return res['value']

    def delete(self, key):
        self.db.execute('delete from cache where key = ?;', [key])

    def delete_all(self):
        logger.debug('Dropping cache')
        with self.db:
            self.db.execute('delete from cache;')


cache = Cache(True)
