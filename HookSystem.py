import os
from Hook import Hook
from model import model
import importlib.machinery


class HookSystem:
    hooks_updated: list[Hook] = list()

    def __init__(self):
        # hooks load
        for file_name in sorted(os.listdir('hooks')):
            if file_name.endswith('.py') and not file_name[0] in ['.', '_']:
                path = os.path.join('hooks', file_name)
                hook_name = file_name[:-3]
                module = importlib.machinery.SourceFileLoader(hook_name, path).load_module()
                setup_func = getattr(module, 'setup', None)
                if setup_func is not None:
                    setup_func(self)

                else:
                    raise AttributeError(f'No setup method in {file_name} hook')

    def add_update_hook(self, hook: Hook) -> None:
        self.hooks_updated.append(hook)

    def remove_update_hook(self, hook: Hook) -> None:
        self.hooks_updated.remove(hook)

    def notify_updated(self, action_id: int) -> None:
        diff_record = model.get_diff_action_id(action_id)
        for hook in self.hooks_updated:
            hook.update(action_id, diff_record)
