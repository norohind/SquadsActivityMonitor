from model.postgres_model import PostgresModel
from model.sqlite_model import Sqlite3Model
from model.abstract_model import AbstractModel

import utils
from EDMCLogging import get_main_logger
import os

logger = get_main_logger()

env_choose = os.getenv('DB_NAME')

model: AbstractModel

if env_choose == 'postgres':
    logger.info('Using postgres DB')
    model = PostgresModel()

elif env_choose == 'sqlite':
    logger.info('Using sqlite DB')
    model = Sqlite3Model()

else:
    logger.info('Using sqlite DB')
    model = Sqlite3Model()

model.open_model()

model.get_diff_action_id = utils.measure(model.get_diff_action_id)
model.get_activity_changes = utils.measure(model.get_activity_changes)
