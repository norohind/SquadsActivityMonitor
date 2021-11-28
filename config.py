import os

cache_disabled: bool = bool(os.getenv('CACHE_DISABLED', True))

DBMS_name = os.getenv('DB_NAME')

postgres_username = os.getenv('DB_USERNAME')
postgres_password = os.getenv('DB_PASSWORD')
postgres_hostname = os.getenv('DB_HOSTNAME')
postgres_port = os.getenv('DB_PORT')
postgres_database_name = os.getenv('DB_DATABASE')

model_cache_db_path = os.getenv('CACHE_PATH', 'squads_stat_cache.sqlite3')

sqlite_db_path = os.getenv('SQLITE_DB_PATH', 'squads_stat.sqlite3')

log_level = os.getenv('LOG_LEVEL', 'DEBUG').upper()

time_between_requests = os.getenv("TIME_BETWEEN_REQUESTS")

sqlite2postgres_sqlite_location = os.getenv('SQLITE2POSTGRES_SQLITE_LOCATION')
