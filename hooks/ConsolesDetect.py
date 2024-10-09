from typing import TYPE_CHECKING
from Hook import Hook

if TYPE_CHECKING:
    import HookSystem


class ConsolesDetect(Hook):
    def update(self, action_id: int, diff: list[dict]) -> None:
        for squad in diff:
            if squad['platform'] != 'PC':
                print(f'Detected non PC actions: {action_id}')


def setup(hs: 'HookSystem'):
    hs.add_update_hook(ConsolesDetect())
