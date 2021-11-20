import json
import os
import time
import enum

import requests

from EDMCLogging import get_main_logger

logger = get_main_logger()

BASE_URL = 'https://api.orerve.net/2.0/website/squadron/'
INFO_ENDPOINT = 'info'
NEWS_ENDPOINT = 'news/list'

TIME_BETWEEN_REQUESTS: float = 3.0
if os.getenv("JUBILANT_TIME_BETWEEN_REQUESTS") is not None:
    try:
        TIME_BETWEEN_REQUESTS = float(os.getenv("JUBILANT_TIME_BETWEEN_REQUESTS"))

    except TypeError:  # env doesn't contain a float
        pass

logger.debug(f'TIME_BETWEEN_REQUESTS = {TIME_BETWEEN_REQUESTS} {type(TIME_BETWEEN_REQUESTS)}')

# proxy: last request time
# ssh -C2 -T -n -N -D 2081 <a server>
try:
    PROXIES_DICT: list[dict] = json.load(open('proxies.json', 'r'))

except FileNotFoundError:
    PROXIES_DICT: list[dict] = [{'url': None, 'last_try': 0}]


# ofc I could do it without enums, I just wanted to try them
class Platform(enum.Enum):
    """
    Enumeration for platforms
    """
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
    """Gets bearer token from capi.demb.design (companion-api project, I will upload it on GH one day...)

    :return: bearer token as str
    """
    bearer_request: requests.Response = requests.get(
        url='https://capi.demb.design/random_token', headers={'auth': os.environ['DEMB_CAPI_AUTH']})

    try:
        bearer: str = bearer_request.json()['access_token']

    except Exception as e:
        logger.exception(f'Unable to parse capi.demb.design answer\nrequested: {bearer_request.url!r}\n'
                         f'code: {bearer_request.status_code!r}\nresponse: {bearer_request.content!r}', exc_info=e)
        raise e

    return bearer


html_table_generator = """
// Thanks to https://stackoverflow.com/a/21065846
var _table_ = document.createElement('table'),
  _tr_ = document.createElement('tr'),
  _th_ = document.createElement('th'),
  _td_ = document.createElement('td');

// Builds the HTML Table out of myList json data from Ivy restful service.
function buildHtmlTable(arr) {
  var table = _table_.cloneNode(false),
    columns = addAllColumnHeaders(arr, table);
  for (var i = 0, maxi = arr.length; i < maxi; ++i) {
    var tr = _tr_.cloneNode(false);
    for (var j = 0, maxj = columns.length; j < maxj; ++j) {
      var td = _td_.cloneNode(false);
      cellValue = arr[i][columns[j]];
      td.appendChild(document.createTextNode(arr[i][columns[j]] || ''));
      tr.appendChild(td);
    }
    table.appendChild(tr);
  }
  return table;
}

// Adds a header row to the table and returns the set of columns.
// Need to do union of keys from all records as some records may not contain
// all records
function addAllColumnHeaders(arr, table) {
  var columnSet = [],
    tr = _tr_.cloneNode(false);
  for (var i = 0, l = arr.length; i < l; i++) {
    for (var key in arr[i]) {
      if (arr[i].hasOwnProperty(key) && columnSet.indexOf(key) === -1) {
        columnSet.push(key);
        var th = _th_.cloneNode(false);
        th.appendChild(document.createTextNode(key));
        tr.appendChild(th);
      }
    }
  }
  table.appendChild(tr);
  return columnSet;
}
"""

activity_table_html_template = """ 
    <!DOCTYPE HTML>
<html lang="en-US">
    <head>
        <meta charset="UTF-8">
        <script src="js/json2htmltable.js"></script>
         <script type="text/javascript">
            window.onload = () => {
                document.body.appendChild(buildHtmlTable(JSON.parse({items})));
            }
        </script>
    </head>
    <body>
    </body>
</html>"""

activity_table_html_styles = """
.table {
    width: 100%;
    margin-bottom: 20px;
    border: 1px solid #dddddd;
    border-collapse: collapse; 
}
.table th {
    font-weight: bold;
    padding: 5px;
    background: #efefef;
    border: 1px solid #dddddd;
}
.table td {
    border: 1px solid #dddddd;
    padding: 5px;
}"""  # TODO: fix css for table
