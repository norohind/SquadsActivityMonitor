import json
import os
import time
import enum

import requests
import config
from EDMCLogging import get_main_logger

logger = get_main_logger()

TIME_BETWEEN_REQUESTS: float = 3.0
if config.time_between_requests is not None:
    try:
        TIME_BETWEEN_REQUESTS = float(config.time_between_requests)

    except TypeError:  # env doesn't contain a float
        pass

# logger.debug(f'TIME_BETWEEN_REQUESTS = {TIME_BETWEEN_REQUESTS} {type(TIME_BETWEEN_REQUESTS)}')

# proxy: last request time
# ssh -C2 -T -n -N -D 2081 <a server>
try:
    PROXIES_DICT: list[dict] = json.load(open('proxies.json', 'r'))

except FileNotFoundError:
    PROXIES_DICT: list[dict] = [{'url': None, 'last_try': 0}]


# ofc I could do it without enums, I just wanted to try them
class Platform(enum.Enum):
    PC = 'PC'
    PS4 = 'PS4'
    XBOX = 'XBOX'


class LeaderboardTypes(enum.Enum):
    EXPLORATION = 'exploration'
    CQC = 'cqc'
    COMBAT = 'combat'
    AEGIS = 'aegis'
    BGS = 'bgs'
    POWERPLAY = 'powerplay'
    TRADE = 'trade'


class FAPIDownForMaintenance(Exception):
    pass


def proxied_request(url: str, method: str = 'get', **kwargs) -> requests.Response:
    """Makes request through one of proxies in round robin manner, respects fdev request kd for every proxy

    :param url: url to request
    :param method: method to use in request
    :param kwargs: kwargs
    :return: requests.Response object

    detect oldest used proxy
    if selected proxy is banned, then switch to next
    detect how many we have to sleep to respect it 3 sec timeout for each proxy
    sleep it
    perform request with it
    if request failed -> write last_try for current proxy and try next proxy
    """

    global PROXIES_DICT

    while True:

        selected_proxy = min(PROXIES_DICT, key=lambda x: x['last_try'])
        logger.debug(f'Requesting {method.upper()} {url!r}, kwargs: {kwargs}; Using {selected_proxy["url"]} proxy')

        # let's detect how much we have to wait
        time_to_sleep: float = (selected_proxy['last_try'] + TIME_BETWEEN_REQUESTS) - time.time()

        if 0 < time_to_sleep <= TIME_BETWEEN_REQUESTS:
            logger.debug(f'Sleeping {time_to_sleep} s')
            time.sleep(time_to_sleep)

        if selected_proxy['url'] is None:
            proxies: dict = None  # noqa

        else:
            proxies: dict = {'https': selected_proxy['url']}

        try:
            proxiedFapiRequest: requests.Response = requests.request(
                method=method,
                url=url,
                proxies=proxies,
                headers={'Authorization': f'Bearer {_get_bearer()}'},
                timeout=30,
                **kwargs
            )

            logger.debug(f'Request complete, code {proxiedFapiRequest.status_code!r}, len '
                         f'{len(proxiedFapiRequest.content)}')

        except requests.exceptions.ConnectionError as e:
            logger.error(f'Proxy {selected_proxy["url"]} is invalid: {str(e.__class__.__name__)}')
            selected_proxy['last_try'] = time.time()  # because link, lol
            continue

        selected_proxy['last_try'] = time.time()  # because link, lol

        if proxiedFapiRequest.status_code == 418:  # FAPI is on maintenance
            logger.warning(f'{method.upper()} {proxiedFapiRequest.url} returned 418, content dump:\n'
                           f'{proxiedFapiRequest.content}')

            raise FAPIDownForMaintenance

        elif proxiedFapiRequest.status_code != 200:
            logger.warning(f"Request to {method.upper()} {url!r} with kwargs: {kwargs}, using {selected_proxy['url']} "
                           f"proxy ends with {proxiedFapiRequest.status_code} status code, content: "
                           f"{proxiedFapiRequest.content}")

        return proxiedFapiRequest


def _get_bearer() -> str:
    """Gets bearer token from capi.demb.uk (companion-api project, I will upload it on GH one day...)

    :return: bearer token as str
    """
    bearer_request: requests.Response = requests.get(
        url=config.capi_endpoint, headers={'auth': os.environ['DEMB_CAPI_AUTH']}, timeout=30
    )

    try:
        bearer: str = bearer_request.json()['access_token']

    except Exception as e:
        logger.exception(f'Unable to parse {config.capi_endpoint} answer\nrequested: {bearer_request.url!r}\n'
                         f'code: {bearer_request.status_code!r}\nresponse: {bearer_request.content!r}', exc_info=e)
        raise e

    return bearer


def measure(function: callable, name_to_display: str):
    """
    Decorator to measure function (method) execution time
    Use as easy as

    @utils.measure
    def im_function_to_measure():
        ....

    :param name_to_display:
    :param function:
    :return:
    """

    def decorated(*args, **kwargs):
        start = time.time()
        result = function(*args, **kwargs)
        end = time.time()
        print(f'{name_to_display}:{function.__name__}: {(end - start) * 100} ms')
        return result

    return decorated

