from model import model
import json
import falcon
import os
from EDMCLogging import get_main_logger
from model.sqlite_cache import cache
from templates_engine import render

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

keys_mapping = {
    'sum_score': 'TotalExperience',
    'timestamp': 'Timestamp UTC',
    'action_id': 'Action ID',
    'sum_score_old': 'Total Experience Old',
    'diff': 'Diff',
    'squadron_name': 'Squadron Name',
    'tag': 'Tag',
    'total_experience': 'Total Experience',
    'total_experience_old': 'Total Experience Old',
    'total_experience_diff': 'Total Experience Diff',
    'leaderboard_type': 'Leaderboard Type',
    'platform': 'Platform'
}


def prettify_keys(rows: list[dict]) -> list[dict]:
    for row in rows:
        for key in list(row.keys()):
            pretty_key = keys_mapping.get(key)
            if pretty_key is not None:
                row[pretty_key] = row.pop(key)

    return rows


logger = get_main_logger()

model.open_model()


class Activity:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, leaderboard: str, platform: str)\
            -> None:
        resp.content_type = falcon.MEDIA_JSON

        args_activity_changes = {
            'platform': platform,
            'leaderboard_type': leaderboard,
            'limit': req.params.get('limit', None),
            'high_timestamp': req.params.get('before', None),
            'low_timestamp': req.params.get('after', None)
        }

        pretty_keys: bool = req.params.get('pretty_keys', 'false').lower() == 'true'

        try:
            model_response: list[dict] = model.get_activity_changes(**args_activity_changes)
            if pretty_keys:
                model_response = prettify_keys(model_response)

            resp.text = json.dumps(model_response)

        except Exception as e:
            logger.warning(
                f'Exception occurred during executing Activity request, args:\n{args_activity_changes}',
                exc_info=e
            )
            raise falcon.HTTPInternalServerError(description=str(e))


class ActivityHtml:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, leaderboard: str, platform: str)\
            -> None:
        resp.content_type = falcon.MEDIA_HTML

        resp.text = render(
            'table_template.html',
            {
                'target_column_name': keys_mapping['action_id'],
                'target_new_url': '/diff/',
             })


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
        pretty_keys: bool = req.params.get('pretty_keys', 'false').lower() == 'true'
        model_response = model.get_diff_action_id(action_id)
        if pretty_keys:
            model_response = prettify_keys(model_response)

        resp.text = json.dumps(model_response)


class ActivityDiffHtml:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, action_id: int) -> None:
        resp.content_type = falcon.MEDIA_HTML
        resp.text = render(
            'table_diff_template.html',
            {
                'target_column_name': keys_mapping['tag'],
                'target_new_url': '/squads/now/by-tag/short/',
                'action_id': action_id
            }
        )


class SumLeaderboardHistory:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, leaderboard: str, platform: str)\
            -> None:
        resp.content_type = falcon.MEDIA_JSON

        try:
            resp.text = json.dumps(model.get_leaderboard_sum_history(platform, leaderboard))

        except Exception as e:
            logger.warning(
                f'Exception occurred during executing history request, LB: {leaderboard!r}; platform: {platform!r}',
                exc_info=e
            )
            raise falcon.HTTPInternalServerError(description=str(e))


class SumLeaderboardHistoryHtml:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, leaderboard: str, platform: str)\
            -> None:
        resp.content_type = falcon.MEDIA_HTML
        resp.text = render(
            'graph_template.html',
            {
                'dataset_title': f'{leaderboard} {platform} points sum'
            }
        )


class LatestLeaderboard:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, leaderboard: str, platform: str)\
            -> None:
        resp.content_type = falcon.MEDIA_JSON
        resp.text = json.dumps(model.get_latest_leaderboard(platform, leaderboard))


class LatestLeaderboardHtml:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, leaderboard: str, platform: str)\
            -> None:
        resp.content_type = falcon.MEDIA_HTML
        resp.text = render(
            'table_template.html',
            {
                'target_column_name': 'tag',
                'target_new_url': '/squads/now/by-tag/short/'
            }
        )


class LeaderboardByActionID:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, action_id: int) -> None:
        resp.content_type = falcon.MEDIA_JSON
        resp.text = json.dumps(model.get_leaderboard_by_action_id(action_id))


class LeaderboardByActionIDHTML:
    def on_get(self, req: falcon.request.Request, resp: falcon.response.Response, action_id: int) -> None:
        resp.content_type = falcon.MEDIA_HTML
        resp.text = render(
            'table_template.html',
            {
                'target_column_name': 'tag',
                'target_new_url': '/squads/now/by-tag/short/'
            }
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
app.add_route('/api/leaderboard-history/leaderboard/{leaderboard}/platform/{platform}', SumLeaderboardHistory())
app.add_route('/api/leaderboard-state/by-action-id/{action_id}', LeaderboardByActionID())
app.add_route('/api/leaderboard-state/now/{leaderboard}/platform/{platform}', LatestLeaderboard())

app.add_route('/leaderboard/{leaderboard}/platform/{platform}', ActivityHtml())
app.add_route('/diff/{action_id}', ActivityDiffHtml())
app.add_route('/leaderboard-history/leaderboard/{leaderboard}/platform/{platform}', SumLeaderboardHistoryHtml())
app.add_route('/leaderboard-state/by-action-id/{action_id}', LeaderboardByActionIDHTML())
app.add_route('/leaderboard-state/now/{leaderboard}/platform/{platform}', LatestLeaderboardHtml())


app.add_route('/api/cache/{action}', Cache())

app.add_route('/', MainPage())

application = app  # for uwsgi


if __name__ == '__main__':
    import waitress

    app.add_static_route('/js', os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'), 'js'))
    app.add_static_route('/', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))
    waitress.serve(app, host='127.0.0.1', port=9485)
