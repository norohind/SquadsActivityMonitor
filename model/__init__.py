from model.postgres_model import PostgresModel
from model.abstract_model import AbstractModel
import config
import utils
from EDMCLogging import get_main_logger

logger = get_main_logger()

model: AbstractModel = PostgresModel()

if config.log_level == 'DEBUG':
    model.get_diff_action_id = utils.measure(model.get_diff_action_id)
    model.get_activity_changes = utils.measure(model.get_activity_changes)
