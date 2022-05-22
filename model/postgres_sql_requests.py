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
"""

"""
In order to sync action_id with appropriate serial sequence, execute 
SELECT 
    setval(
            'squads_stats_states_action_info_action_id_seq', 
            (SELECT MAX(action_id) FROM squads_stats_states_action_info)+1
            );
"""

create_new_action_id = """
insert into squads_stats_states_action_info (leaderboard_type, platform) values (%(LB_type)s, %(platform)s);

select action_id 
from squads_stats_states_action_info
order by action_id desc
limit 1;"""


insert_leaderboard = """
insert into squads_stats_states_data (action_id, squadron_id, score, percentile, rank, name, tag) 
values 
(%(action_id)s, %(squadron)s, %(score)s, %(percentile)s, %(rank)s, %(name)s, %(tag)s);"""


select_activity_pretty_names = """
with action_ids as (
    select action_id, timestamp
    from squads_stats_states_action_info
    where
        leaderboard_type = %(LB_type)s and
        platform = %(platform)s and
        %(high_timestamp)s::timestamp >= timestamp
        and timestamp >= %(low_timestamp)s::timestamp
    order by action_id desc
    ),

    sum_history as (
        select sum(score) as sum_score, squads_stats_states_data.action_id as action_id, action_ids.timestamp as timestamp
        from squads_stats_states_data, action_ids
        where squads_stats_states_data.action_id = action_ids.action_id
        group by squads_stats_states_data.action_id, action_ids.timestamp
    ),

    sum_history_old_calculated as (select
        sum_score,
        min(timestamp) as timestamp,
        action_id,
        lag (sum_score, 1) over (order by action_id) sum_score_old
    from sum_history
    group by sum_score, action_id
    order by timestamp desc
    )

select
    sum_score::bigint as "sum_score",
    to_char(timestamp, 'YYYY-MM-DD HH24:MI:SS') as "timestamp",
    action_id::bigint as "action_id",
    sum_score_old::bigint as "sum_score_old",
    (sum_score - sum_score_old)::bigint as "diff"
from sum_history_old_calculated
where (sum_score - sum_score_old) <> 0
limit %(limit)s;"""

select_diff_by_action_id = """
with origin_record as (
    select action_id, timestamp, leaderboard_type, platform
    from squads_stats_states_action_info
    where action_id = %(action_id)s
    ),
    prev_records_lag as (
        select
               squads_stats_states_action_info.action_id,
               lag(squads_stats_states_action_info.action_id, 1) over (order by squads_stats_states_action_info.action_id) prev_action_id
        from squads_stats_states_action_info, origin_record
        where squads_stats_states_action_info.platform = origin_record.platform
            and squads_stats_states_action_info.leaderboard_type = origin_record.leaderboard_type
    ),

    prev_record as (
        select prev_action_id
        from prev_records_lag, origin_record
        where prev_records_lag.action_id = origin_record.action_id
    ),

    main as (
    select
        coalesce(new_stats.name, old_stats.name) as "squadron_name",
        coalesce(new_stats.tag, old_stats.tag) as "tag",
        coalesce(new_stats.score, 0) as "total_experience",
        coalesce(old_stats.score, 0) as "total_experience_old",
        coalesce(new_stats.score, 0) - coalesce(old_stats.score, 0) as "total_experience_diff",
        coalesce(new_stats.action_id, old_stats.action_id) as action_id
    from (
            select *
            from squads_stats_states_data
            where action_id = %(action_id)s
        ) new_stats
    full join (
        select *
        from squads_stats_states_data, prev_record
        where action_id = prev_record.prev_action_id
        ) old_stats
        on new_stats.squadron_id = old_stats.squadron_id
    where coalesce(new_stats.score, 0) - coalesce(old_stats.score, 0) <> 0
    order by coalesce(new_stats.score, 0) - coalesce(old_stats.score, 0) desc)

select
    "squadron_name",
    "tag",
    "total_experience",
    "total_experience_old",
    "total_experience_diff",
    squads_stats_states_action_info.leaderboard_type as "leaderboard_type",
    squads_stats_states_action_info.platform as "platform"
from main
    inner join squads_stats_states_action_info
        on main.action_id = squads_stats_states_action_info.action_id"""

select_leaderboard_sum_history = """
select
       sum(score)::bigint as "Score Sum",
       to_char(max(timestamp), 'YYYY-MM-DD HH24:MI:SS') as "Timestamp UTC"
from squads_stats_states_data
inner join squads_stats_states_action_info
    on squads_stats_states_action_info.action_id = squads_stats_states_data.action_id
where leaderboard_type = %(LB_type)s and platform = %(platform)s
group by squads_stats_states_data.action_id
order by "Timestamp UTC" desc
limit 1000;
"""

select_leaderboard_by_action_id = """
select
       name,
       rank,
       score,
       to_char(timestamp, 'YYYY-MM-DD HH24:MI:SS') as timestamp,
       leaderboard_type,
       platform,
       squadron_id
from squads_stats_states_data
inner join squads_stats_states_action_info
    on squads_stats_states_data.action_id = squads_stats_states_action_info.action_id
where squads_stats_states_action_info.action_id = %(action_id)s
order by score desc;
"""

select_latest_leaderboard = """
with max_action_id as (
    select
           max(action_id) as action_id
    from squads_stats_states_action_info
    where
          leaderboard_type = %(LB_type)s and
          platform = %(platform)s
    ),

    leaderboard as (
        select
            name as squadron_name,
            tag,
            rank,
            score,
            squadron_id,
            squads_stats_states_data.action_id as action_id
        from squads_stats_states_data, max_action_id
        where squads_stats_states_data.action_id = max_action_id.action_id
        )

select
       squadron_name,
       tag,
       rank,
       score,
       to_char(squads_stats_states_action_info.timestamp, 'YYYY-MM-DD HH24:MI:SS') as timestamp,
       squads_stats_states_action_info.leaderboard_type as leaderboard_type,
       squads_stats_states_action_info.platform as platform,
       squadron_id
from leaderboard
inner join squads_stats_states_action_info
    on squads_stats_states_action_info.action_id = leaderboard.action_id
order by score desc;
"""
