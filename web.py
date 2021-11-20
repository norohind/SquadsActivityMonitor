import waitress

import model
import json
import falcon

import utils

"""
Request /activity/cqc?platform=pc[&limit=50&after=&before]

"""


class Activity:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, leaderboard: str) -> None:
        resp.content_type = falcon.MEDIA_JSON

        args_activity_changes = {
            'platform': req.params.get('platform', 'pc'),
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
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, leaderboard: str) -> None:
        Activity().on_get(req, resp, leaderboard)
        table_in_json: str = resp.text
        resp.content_type = falcon.MEDIA_HTML
        resp.text = utils.activity_table_html_template.replace('{items}', json.dumps(table_in_json))
        # what? f-strings? .format? never heard about them


class JS:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, file: str) -> None:
        resp.content_type = falcon.MEDIA_JS
        if file == 'json2htmltable.js':
            resp.text = utils.html_table_generator

        elif file == 'table_styles.css':
            resp.text = utils.activity_table_html_styles

        else:
            raise falcon.HTTPNotFound


app = falcon.App()
app.add_route('/activity/{leaderboard}', Activity())
app.add_route('/js/{file}', JS())
app.add_route('/{leaderboard}', ActivityHtml())

if __name__ == '__main__':
    waitress.serve(app, host='127.0.0.1', port=9485)
