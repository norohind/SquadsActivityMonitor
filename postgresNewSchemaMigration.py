"""
Script to migrate data from old flat schema to new one
"""

import psycopg2.extensions
import psycopg2.extras
import config
import signal
import time

exiting = False


def exit_handler(_, __):
    global exiting
    exiting = True


signal.signal(signal.SIGTERM, exit_handler)
signal.signal(signal.SIGINT, exit_handler)

db: psycopg2.extensions.connection = psycopg2.connect(
    user=config.postgres_username,
    password=config.postgres_password,
    host=config.postgres_hostname,
    port=config.postgres_port,
    database=config.postgres_database_name,
    cursor_factory=psycopg2.extras.DictCursor)

old_table = 'squads_stats_states'
action_info_table = 'squads_stats_states_action_info'
data_table = 'squads_stats_states_data'

schema_create = """create table if not exists squads_stats_states_action_info (
action_id serial primary key,
leaderboard_type text,
platform text,
timestamp timestamp default timezone('utc', now())
);

create table if not exists squads_stats_states_data (
action_id integer,
squadron_id integer,
score bigint,
percentile integer,
rank integer,
name text,
tag text,
foreign key (action_id) references squads_stats_states_action_info(action_id)
);

create table if not exists squads_stats_states_metainfo (
property text primary key,
int_value integer,
text_value text
);
insert into squads_stats_states_metainfo (property, int_value) values ('origin_offset', 0) on conflict do nothing;
"""
last_new_action_id_q = f"select max(action_id) - (select int_value from squads_stats_states_metainfo where property = 'origin_offset') from {action_info_table};"
select_under_action_id = f'select distinct action_id, leaderboard_type, platform from {old_table} where action_id > %(action_id)s order by action_id;'
select_unique_leaderboard = f'select * from {old_table} where action_id = %(action_id)s and leaderboard_type = %(LB_type)s and platform = %(platform)s order by rank limit 1;'

db_side_insert_unique_leaderboard = """
insert into squads_stats_states_data (action_id, squadron_id, score, percentile, rank, name, tag)
    select action_id + (select int_value from squads_stats_states_metainfo where property = 'origin_offset') as action_id, squadron_id, score, percentile, rank, name, tag
    from squads_stats_states 
    where 
          action_id = %(action_id)s and 
          leaderboard_type = %(LB_type)s and 
          platform = %(platform)s 
    order by rank"""

insert_new_action_id = """
insert into squads_stats_states_action_info (action_id, leaderboard_type, platform, timestamp) values (%(action_id)s, %(LB_type)s, %(platform)s, %(timestamp)s);
"""

insert_new_leaderboard = """
insert into squads_stats_states_data (action_id, squadron_id, score, percentile, rank, name, tag) 
values 
(%(action_id)s, %(squadron_id)s, %(score)s, %(percentile)s, %(rank)s, %(name)s, %(tag)s);"""

cursor: psycopg2.extras.DictCursor = db.cursor()
cursor.execute(schema_create)

cursor.execute(last_new_action_id_q)
last_new_action_id = cursor.fetchall()

if last_new_action_id[0][0] is None:
    last_action_id = 0

else:
    last_action_id = last_new_action_id[0][0]


print(f'{last_action_id=}')

initial_q_timer = time.time()
cursor.execute(select_under_action_id, {'action_id': last_action_id})
print(f'select_under_action_id took: {time.time() - initial_q_timer}')

prev_action_id = None
records_counter = 0
timer = time.time()
for unique_lb_platform in cursor.fetchall():
    action_id: int = unique_lb_platform['action_id']
    if prev_action_id == action_id:
        # increment offset
        cursor.execute("update squads_stats_states_metainfo set int_value = int_value + 1 where property = 'origin_offset';")
        db.commit()

    LB_type = unique_lb_platform['leaderboard_type']
    platform = unique_lb_platform['platform']

    if exiting:
        break

    # get all items under action_id
    # perform sanity check
    # insert to new tables

    first_q_timer = time.time()
    cursor.execute(select_unique_leaderboard,
                   {
                       'action_id': action_id,
                       'LB_type': LB_type,
                       'platform': platform
                   })

    old_leaderboard = cursor.fetchall()

    timestamp = old_leaderboard[0]['timestamp']
    cursor.execute("select int_value from squads_stats_states_metainfo where property = 'origin_offset';")
    offseted_action_id = cursor.fetchone()[0]

    cursor.execute(insert_new_action_id, {
        'action_id': action_id + offseted_action_id,
        'LB_type': LB_type,
        'platform': platform,
        'timestamp': timestamp
    })

    cursor.execute(db_side_insert_unique_leaderboard,
                   {
                       'action_id': action_id,
                       'LB_type': LB_type,
                       'platform': platform
                   })

    if records_counter % 10 == 0:
        db.commit()

    prev_action_id = action_id
    records_counter += 1

db.commit()

db.close()
timed = time.time() - timer
print(f'Inserted: {records_counter} for {timed} s, avg rate {records_counter / timed} records/s')
