from model import model
import json
import falcon
import os
from EDMCLogging import get_main_logger
import utils
from model.sqlite_cache import cache

"""
/leaderboard/{leaderboard_type}/platform/{platform}?[limit=<int>
    &after=<timestamp (as "Timestamp UTC" column format)>&after=<timestamp (as "Timestamp UTC" column format)>]
    
leaderboard_type - one of
    powerplay
    cqc
    trade
    exploration
    aegis
    bgs
    combat

platform - one of
    XBOX
    PS4
    PC
"""

logger = get_main_logger()

model.open_model()


class Activity:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, leaderboard: str, platform: str)\
            -> None:
        resp.content_type = falcon.MEDIA_JSON

        args_activity_changes = {
            'platform': platform,
            'leaderboard_type': leaderboard,
            'limit': req.params.get('limit', 10),
            'high_timestamp': req.params.get('before', '3307-12-12'),
            'low_timestamp': req.params.get('after', '0001-01-01')
        }

        try:
            resp.text = json.dumps(model.get_activity_changes(**args_activity_changes))

        except Exception as e:
            logger.warning(
                f'Exception occurred during executing Activity request, args:\n{args_activity_changes}',
                exc_info=e
            )
            raise falcon.HTTPInternalServerError(description=str(e))


class ActivityHtml:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, leaderboard: str, platform: str)\
            -> None:
        Activity().on_get(req, resp, leaderboard, platform)
        table_in_json: str = resp.text
        resp.content_type = falcon.MEDIA_HTML

        resp.text = utils.activity_table_html_template.replace('{items}', table_in_json)
        # what? f-strings? .format? never heard about them


class ActivityDiff:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, action_id: int) -> None:
        """
        Give squads tags and diff in their experience for specified action_id - 1 (smart -1)

        :param action_id:
        :param req:
        :param resp:
        :return:
        """

        resp.content_type = falcon.MEDIA_JSON
        resp.text = json.dumps(model.get_diff_action_id(action_id))


class ActivityDiffHtml:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, action_id: int) -> None:
        resp.content_type = falcon.MEDIA_HTML
        # table: str = json.dumps(model.get_diff_action_id(action_id))
        resp.text = utils.activity_table_html_template.replace(
            '{items}', json.dumps(model.get_diff_action_id(action_id))
        )


class MainPage:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response) -> None:
        raise falcon.HTTPMovedPermanently('/index.html')


class Cache:
    def on_post(self, req: falcon.request.Request, resp: falcon.response.Response, action: str) -> None:
        if action.lower() == 'drop':
            cache.delete_all()
            resp.status = falcon.HTTP_204
            return

        raise falcon.HTTPNotFound


app = falcon.App()
app.add_route('/api/leaderboard/{leaderboard}/platform/{platform}', Activity())
app.add_route('/api/diff/{action_id}', ActivityDiff())

app.add_route('/leaderboard/{leaderboard}/platform/{platform}', ActivityHtml())
app.add_route('/diff/{action_id}', ActivityDiffHtml())

app.add_route('/api/cache/{action}', Cache())

app.add_route('/', MainPage())

application = app  # for uwsgi

index_file = os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'), 'index.html')

utils.build_index_page(app, index_file)

if __name__ == '__main__':
    import waitress

    app.add_static_route('/js', os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'), 'js'))
    app.add_static_route('/', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))
    waitress.serve(app, host='127.0.0.1', port=9485)
