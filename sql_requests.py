schema_create = """create table if not exists squads_stats_states (
action_id integer,
leaderboard_type string,
platform string,
squadron_id integer,
score integer,
percentile integer,
rank integer,
name string,
tag string,
timestamp default current_timestamp);

create view if not exists current_cqc_pc as
select * from squads_stats_states where action_id in 
(select distinct action_id 
from squads_stats_states 
where leaderboard_type = 'cqc' and platform = 'PC' 
order by action_id desc limit 1) and platform = 'PC';

create view if not exists prev_cqc_pc as
select * 
from squads_stats_states 
where action_id in 
(select distinct action_id 
from squads_stats_states 
where leaderboard_type = 'cqc' and platform = 'PC' order by action_id desc limit 1, 1) and platform = 'PC';

create index if not exists idx_action_id_0 on squads_stats_states (action_id);
create index if not exists idx_platform_leaderboard_type_1 on squads_stats_states(platform, leaderboard_type);

create view if not exists diff_pc_cqc as 
select current_cqc_pc.name, current_cqc_pc.score, prev_cqc_pc.score, current_cqc_pc.score - prev_cqc_pc.score as diff 
from current_cqc_pc left outer join prev_cqc_pc on prev_cqc_pc.squadron_id = current_cqc_pc.squadron_id;"""

select_last_action_id = """select action_id 
from squads_stats_states
order by action_id desc
limit 1;"""

insert_leader_board = """insert into squads_stats_states (action_id, leaderboard_type, platform, squadron_id, score, 
percentile, rank, name, tag) 
values (:action_id, :LB_type, :platform, :squadron, :score, :percentile, :rank, :name, :tag);"""

select_activity = """select *, sum_score - sum_score_old as diff from 
(select sum_score, min(timestamp) as timestamp, action_id, lag (sum_score, 1, 0) over (order by sum_score) sum_score_old 
from (
    select sum(score) as sum_score, timestamp, action_id 
    from squads_stats_states 
    where 
        leaderboard_type = :LB_type and 
        platform = :platform and
        :high_timestamp >=  timestamp and 
        timestamp >= :low_timestamp 
    group by action_id
    ) 
group by sum_score 
order by timestamp desc 
limit :limit);"""

select_activity_pretty_names = """select 
sum_score as TotalExperience, 
timestamp as Timestamp, 
action_id as ActionId, 
sum_score_old as TotalExperienceOld, 
sum_score - sum_score_old as Diff 
from 
(select sum_score, min(timestamp) as timestamp, action_id, lag (sum_score, 1, 0) over (order by sum_score) sum_score_old 
from (
    select sum(score) as sum_score, timestamp, action_id 
    from squads_stats_states 
    where 
        leaderboard_type = :LB_type and 
        platform = :platform and
        :high_timestamp >=  timestamp and 
        timestamp >= :low_timestamp 
    group by action_id
    ) 
group by sum_score 
order by timestamp desc 
limit :limit);"""

select_diff_by_action_id = """select 
    new_stats.tag, 
    new_stats.score as TotalExperience, 
    old_stats.score as TotalExperienceOld, 
    new_stats.score - old_stats.score as TotalExperienceDiff, 
    new_stats.leaderboard_type as LeaderBoardType, 
    new_stats.platform as Platform
from (
    select * 
    from squads_stats_states 
    where action_id = :action_id) new_stats 
inner join 
    (
        select * 
        from squads_stats_states 
        where action_id in (
                            select distinct squads_stats_states.action_id 
                            from squads_stats_states, (
                                                        select timestamp, platform, leaderboard_type, action_id 
                                                        from squads_stats_states 
                                                        where action_id = :action_id limit 1) sub1 
                            where 
                                squads_stats_states.platform = sub1.platform and 
                                squads_stats_states.leaderboard_type = sub1.leaderboard_type and 
                                squads_stats_states.action_id < sub1.action_id 
                            order by squads_stats_states.action_id desc 
                            limit 1)) old_stats 
on new_stats.squadron_id = old_stats.squadron_id 
where TotalExperienceDiff > 0;"""