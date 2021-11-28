from model.postgres_model import PostgresModel
from model.sqlite_model import Sqlite3Model
from model.abstract_model import AbstractModel
import config
import utils
from EDMCLogging import get_main_logger

logger = get_main_logger()

env_choose = config.DBMS_name

model: AbstractModel

if env_choose == 'postgres':
    logger.info('Using postgres DB')
    model = PostgresModel()

elif env_choose == 'sqlite':
    logger.info('Using sqlite DB')
    model = Sqlite3Model()

else:
    logger.error(f'Unknown DB {env_choose!r}')

    assert False, 'env variable DB_NAME must be "postgres" or "sqlite"'

if config.log_level == 'DEBUG':
    model.get_diff_action_id = utils.measure(model.get_diff_action_id)
    model.get_activity_changes = utils.measure(model.get_activity_changes)
