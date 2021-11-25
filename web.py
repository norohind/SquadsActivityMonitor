import model
import json
import falcon

import utils

"""
Request /activity/cqc?platform=pc[&limit=50&after=&before]

"""


class Activity:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, leaderboard: str, platform: str)\
            -> None:
        resp.content_type = falcon.MEDIA_JSON

        args_activity_changes = {
            'platform': platform,
            'leaderboard_type': leaderboard,
            'limit': req.params.get('limit', 10),
            'high_timestamp': req.params.get('before', 'a'),
            'low_timestamp': req.params.get('after', 0)
        }

        try:
            resp.text = json.dumps(model.get_activity_changes(**args_activity_changes))

        except Exception as e:
            raise falcon.HTTPInternalServerError(description=str(e))


class ActivityHtml:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, leaderboard: str, platform: str)\
            -> None:
        Activity().on_get(req, resp, leaderboard, platform)
        table_in_json: str = resp.text
        resp.content_type = falcon.MEDIA_HTML
        resp.text = utils.activity_table_html_template.replace('{items}', json.dumps(table_in_json))
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
            '{items}', json.dumps(json.dumps(model.get_diff_action_id(action_id)))
        )


class JS:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, file: str) -> None:
        if file == 'json2htmltable.js':
            resp.content_type = falcon.MEDIA_JS
            resp.text = utils.html_table_generator

        elif file == 'table_styles.css':
            resp.content_type = 'text/css'
            resp.text = utils.activity_table_html_styles

        else:
            raise falcon.HTTPNotFound


class MainPage:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, var: str) -> None:
        raise falcon.HTTPFound(f'/leaderboard/{var}')


class Cache:
    def on_post(self, req: falcon.request.Request, resp: falcon.response.Response, action: str) -> None:
        if action.lower() == 'drop':
            model.cache.delete_all()
            resp.status = falcon.HTTP_204
            return

        raise falcon.HTTPNotFound


app = falcon.App()
app.add_route('/api/leaderboard/{leaderboard}/platform/{platform}', Activity())
app.add_route('/api/diff/{action_id}', ActivityDiff())

app.add_route('/leaderboard/{leaderboard}/platform/{platform}', ActivityHtml())
app.add_route('/diff/{action_id}', ActivityDiffHtml())

app.add_route('/{var}', MainPage())

app.add_route('/api/cache/{action}', Cache())

application = app  # for uwsgi

if __name__ == '__main__':
    import waitress
    import os
    app.add_static_route('/js', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'js'))
    waitress.serve(app, host='127.0.0.1', port=9485)
