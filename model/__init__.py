import model.postgres_model
import utils
from EDMCLogging import get_main_logger
import os

logger = get_main_logger()

env_choose = os.getenv('DB_NAME')

env_choose = 'sqlite'  # TODO: remove

if env_choose == 'postgres':
    logger.info('Using postgres DB')
    from .import postgres_model as model

elif env_choose == 'sqlite':
    logger.info('Using sqlite DB')
    from .import sqlite_model as model

else:
    logger.info('Using sqlite DB')
    from . import sqlite_model as model

model.get_diff_action_id = utils.measure(model.get_diff_action_id)
model.get_activity_changes = utils.measure(model.get_activity_changes)
