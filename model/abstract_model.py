import abc


class AbstractModel(abc.ABC):

    @abc.abstractmethod
    def open_model(self) -> None:
        raise NotImplemented

    @abc.abstractmethod
    def close_model(self) -> None:
        raise NotImplemented

    @abc.abstractmethod
    def get_activity_changes(self, platform: str, leaderboard_type: str, limit: int, low_timestamp, high_timestamp)\
            -> list:
        raise NotImplemented

    @abc.abstractmethod
    def insert_leaderboard_db(self, leaderboard_list: dict) -> None:
        raise NotImplemented

    @abc.abstractmethod
    def get_diff_action_id(self, action_id: int) -> list:
        raise NotImplemented

    @abc.abstractmethod
    def get_leaderboard_sum_history(self, platform: str, leaderboard_type: str) -> list[dict]:
        raise NotImplemented
