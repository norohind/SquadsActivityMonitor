import waitress

import model
import json
import falcon

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
            resp.text = json.dumps({'status': 'error', 'msg': str(e)})


app = falcon.App()
app.add_route('/activity/{leaderboard}', Activity())

if __name__ == '__main__':
    waitress.serve(app, host='127.0.0.1', port=9485)
