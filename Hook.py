from abc import ABC, abstractmethod


class Hook(ABC):  # See at Hook class as to observer in observer pattern
    """
    In order to implement hook, subclass this class and pass instance to HookSystem.add_update_hook
    """

    @abstractmethod
    def update(self, action_id: int, diff: list[dict]) -> None:
        """

        :param action_id: action id of diff
        :param diff: the diff like from /diff/123 endpoint
        :return:
        """

        raise NotImplemented
