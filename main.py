"""
Run by third side (i.e. cron)
Request all or specified combination of platform + activity
Write results to sqlite DB in journal like format


AP - appropriate field from json
DB structure
states:
action_id integer - id of insertion, all records from one request will have the same action_id
leaderboard_type string - (AP)
platform string - platform of data
squadron_id integer - (squadron field)
score integer - (AP)
percentile integer - (AP)
rank integer - (AP)
name string - (AP)
tag string - (AP)
timestamp - inserts by DB, default TIMESTAMP

"""

import requests
from model import model
# from EDMCLogging import get_main_logger
import utils


def request_leaderboard(platform_enum: utils.Platform, leaderboard_type_enum: utils.LeaderboardTypes) -> dict:
    """
    Requests specified leaderboard and returns list of squads in specified leaderboard

    :param platform_enum:  leaderboard platform
    :param leaderboard_type_enum: leaderboard type
    :return: list of squads from leaderboard
    """

    platform: str = platform_enum.value
    leaderboard_type = leaderboard_type_enum.value

    SAPIRequest: requests.Response = utils.proxied_request(
        'https://api.orerve.net/2.0/website/squadron/season/leaderboards',
        params={'leaderboardType': leaderboard_type, 'platform': platform})

    return {
        'leaderboard': SAPIRequest.json()['leaderboards'][leaderboard_type],  # list
        'platform': platform,  # str
        'type': leaderboard_type  # str
    }


def get_and_save_leaderboard(platform_enum: utils.Platform, leaderboard_type_enum: utils.LeaderboardTypes) -> None:
    """
    High logic function to get and save information about specified for type and platform leaderboard

    :param platform_enum:
    :param leaderboard_type_enum:
    :return:
    """

    req = request_leaderboard(platform_enum, leaderboard_type_enum)
    model.insert_leaderboard_db(req)


def main():
    """
    Run in specified mode from command line

    main.py update all
        - make all 21 requests (7 leaderboards * 3 platforms)

    main.py update <leaderboard: string>
        - update specified leaderboard for all platforms (3 requests)

    main.py update <leaderboard: string> <platform: string>
        - update specified leaderboard for specified platform

    :return:
    """

    from sys import argv

    help_msg: str = main.__doc__[46:-19]

    def failed_args(exit_code: int = 0):
        print(help_msg)
        exit(exit_code)

    if len(argv) == 3:  # update all
        if argv[1] == 'update' and argv[2] == 'all':
            # main.py update all
            for platform_enum in utils.Platform:
                for LB_type_enum in utils.LeaderboardTypes:
                    get_and_save_leaderboard(platform_enum, LB_type_enum)

            exit(0)

        elif argv[1] == 'update':
            # main.py update <leaderboard: string>
            leaderboard: str = argv[2].lower()
            try:
                leaderboard_enum: utils.LeaderboardTypes = utils.LeaderboardTypes(leaderboard)

                for platform_enum in utils.Platform:
                    get_and_save_leaderboard(platform_enum, leaderboard_enum)

                exit(0)

            except ValueError:
                print('leaderboard must be correct leaderboard type')
                exit(1)

        else:
            failed_args(1)

    elif len(argv) == 4:
        # main.py update <leaderboard: string> <platform: string>
        if argv[1] == 'update':
            leaderboard = argv[2].lower()
            platform = argv[3].upper()

            try:
                leaderboard_enum: utils.LeaderboardTypes = utils.LeaderboardTypes(leaderboard)
                platform_enum: utils.Platform = utils.Platform(platform)

                get_and_save_leaderboard(platform_enum, leaderboard_enum)
                exit(0)

            except ValueError:
                print('leaderboard must be correct leaderboard type, platform must be correct platform')
                exit(0)
    else:
        failed_args(1)


if __name__ == '__main__':
    main()
