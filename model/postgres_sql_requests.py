schema_create = """create table if not exists squads_stats_states (
action_id integer,
leaderboard_type text,
platform text,
squadron_id integer,
score bigint,
percentile integer,
rank integer,
name text,
tag text,
timestamp timestamp default timezone('utc', now()));

create index if not exists idx_action_id_0 on squads_stats_states (action_id);
create index if not exists idx_platform_leaderboard_type_1 on squads_stats_states(platform, leaderboard_type);
"""

select_last_action_id = """select action_id 
from squads_stats_states
order by action_id desc
limit 1;"""

insert_leader_board = """insert into squads_stats_states (action_id, leaderboard_type, platform, squadron_id, score, 
percentile, rank, name, tag) 
values 
(%(action_id)s, %(LB_type)s, %(platform)s, %(squadron)s, %(score)s, %(percentile)s, %(rank)s, %(name)s, %(tag)s);"""

select_activity_pretty_names = """select 
sum_score::bigint as "TotalExperience", 
to_char(timestamp, 'YYYY-MM-DD HH24:MI:SS') as "Timestamp UTC",
action_id::bigint as "ActionId", 
sum_score_old::bigint as "TotalExperienceOld", 
(sum_score - sum_score_old)::bigint as "Diff" 
from 
    (
        select 
            sum_score, 
            min(timestamp) as timestamp, 
            action_id, 
            lag (sum_score, 1) over (order by sum_score) sum_score_old 
        from (
                select sum(score) as sum_score, min(timestamp) as timestamp, action_id 
                from squads_stats_states 
                where 
                    leaderboard_type = %(LB_type)s and 
                    platform = %(platform)s and
                    %(high_timestamp)s::timestamp >=  timestamp and 
                    timestamp >= %(low_timestamp)s::timestamp 
                group by action_id
             ) as foo
    group by sum_score, action_id 
    order by timestamp desc 
    
    ) as foo1
where (sum_score - sum_score_old) <> 0 
limit %(limit)s;"""

select_diff_by_action_id = """select 
    new_stats.name as "SquadronName",
    new_stats.tag, 
    coalesce(new_stats.score, 0) as "TotalExperience", 
    coalesce(old_stats.score, 0) as "TotalExperienceOld", 
    coalesce(new_stats.score, 0) - coalesce(old_stats.score, 0) as "TotalExperienceDiff", 
    new_stats.leaderboard_type as "LeaderBoardType", 
    new_stats.platform as "Platform"
from (
    select * 
    from squads_stats_states 
    where action_id = %(action_id)s) new_stats 
full join 
    (
        select * 
        from squads_stats_states 
        where action_id in (
                            select distinct squads_stats_states.action_id 
                            from squads_stats_states, (
                                                        select timestamp, platform, leaderboard_type, action_id 
                                                        from squads_stats_states 
                                                        where action_id = %(action_id)s limit 1) sub1 
                            where 
                                squads_stats_states.platform = sub1.platform and 
                                squads_stats_states.leaderboard_type = sub1.leaderboard_type and 
                                squads_stats_states.action_id < sub1.action_id 
                            order by squads_stats_states.action_id desc 
                            limit 1)) old_stats 
on new_stats.squadron_id = old_stats.squadron_id 
where coalesce(new_stats.score, 0) - coalesce(old_stats.score, 0) <> 0
order by new_stats.score - old_stats.score desc;"""