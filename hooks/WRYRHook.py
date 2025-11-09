import copy

import requests
import config
from HookSystem import HookSystem
from Hook import Hook
from EDMCLogging import get_main_logger

logger = get_main_logger()

EMBED_TEMPLATE = {
    "embeds": [
        {
            "type": "rich",
            "title": "",
            "description": "",
            "color": 65535,
            "fields": [
                {
                    "name": "XP diff",
                    "value": "",
                    "inline": True
                },
                {
                    'name': "Involved count",
                    'value': '',
                    'inline': True
                }
            ],
            "url": "https://sapi.demb.uk/diff/{action_id}"
        }
    ]
}
# as an idea: notifications as a service
TRACKED_TAGS = ['COFF', 'PLCN', 'CQCD', 'RMLK', 'AXIN', '7725', 'MYCF', 'GXIN', 'L4ND', 'NEWP', 'CCLS', 'BAAS', 'MAXA', 'EGPU', 'LLPC', 'DAOS', 'J3DI', 'ENEX', 'G911', 'IHCF', 'EDXN', 'HLLN', 'NTNS', 'VAT9', 'R0SD', 'RXLA', 'CZ88', 'ECH0', 'GTBE', 'ROEL', 'GOB5', 'MAKH', 'UKRS', 'ASOG', 'STFR', 'BS13', 'RDTK', 'HIDB', 'IBAS']


def notify_discord(message: dict) -> None:
    """Just sends message to discord, without rate limits respect"""
    logger.debug('Sending discord message')

    hookURL: str = config.discord_hook_url_1

    discord_request: requests.Response = requests.post(
        url=hookURL,
        json=message,
        timeout=60,
        proxies=config.discord_proxy_dict
    )

    try:
        discord_request.raise_for_status()

    except Exception as e:
        logger.exception(f'Fail on sending message to discord ({"/".join(hookURL.split("/")[-2:])})'
                         f'\n{discord_request.content}', exc_info=e)
        return

    logger.debug('Sending successful')
    return


class WRYRHook(Hook):
    def update(self, action_id: int, diff: list[dict]) -> None:
        for squad in diff:
            if (
                    squad['tag'] in TRACKED_TAGS and
                    squad['platform'] == 'PC' and
                    squad['leaderboard_type'] == 'cqc'
            ):
                embed = copy.deepcopy(EMBED_TEMPLATE)
                embed['embeds'][0]['url'] = EMBED_TEMPLATE['embeds'][0]['url'].format(action_id=action_id)
                embed['embeds'][0]['title'] = squad['tag']
                embed['embeds'][0]['fields'][0]['value'] = squad['total_experience_diff']
                embed['embeds'][0]['fields'][1]['value'] = str(len(diff))
                notify_discord(embed)
                return


def setup(hs: HookSystem):
    hs.add_update_hook(WRYRHook())



