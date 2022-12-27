from espn_api.football import League
import CommonFunctions
# gui here
import schedule
import time
import pandas as pd
from tkinter import filedialog
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.pylab as pl
import tkinter as tk
from tkinter import *
from tkinter import ttk
import matplotlib.cm as cm
from colour import Color
import matplotlib.ticker as ticker
import seaborn as sns
import os
import glob
from ast import literal_eval
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)

pd.options.mode.chained_assignment = None  # default='warn'


def deEmojify(text):
    regrex_pattern = re.compile(pattern = "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642"
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
        "]+", flags=re.UNICODE)
    return regrex_pattern.sub(r'',text)


def side_points(box_scores, week, df_og, year):

    team_dic = {}
    #df = pd.DataFrame(data, columns=['Team','Week','Matchup','home/away'])

    for i in range(6):
        # get names and format as oppropriate

        name_trim_home = deEmojify(box_scores[i].home_team.team_name)
        name_trim_away = deEmojify(box_scores[i].away_team.team_name)
        # get weekly point totals for each team
        home_weeklyscore = box_scores[i].home_score
        away_weeklyscore = box_scores[i].away_score
        # get wins and losses as a function of time (i.e. these represent values thru the season)
        if week == 1:
            if box_scores[i].home_score > box_scores[i].away_score:
                home_wins = 1
                home_losses = 0
                home_ties = 0
                away_wins = 0
                away_losses = 1
                away_ties = 0
            elif box_scores[i].home_score < box_scores[i].away_score:
                home_wins = 0
                home_losses = 1
                home_ties = 0
                away_wins = 1
                away_losses = 0
                away_ties = 0
            elif box_scores[i].home_score == box_scores[i].away_score:
                home_wins = 0
                home_losses = 0
                home_ties = 1
                away_wins = 0
                away_losses = 0
                away_ties = 1
        else:
            # df_wlt = df.set_index('Team ID')
            stats_temp_home_wins = df_og.at[box_scores[i].home_team.team_id, 'Wins']
            stats_temp_home_losses = df_og.at[box_scores[i].home_team.team_id, 'Losses']
            stats_temp_home_ties = df_og.at[box_scores[i].home_team.team_id, 'Ties']
            stats_temp_away_wins = df_og.at[box_scores[i].away_team.team_id, 'Wins']
            stats_temp_away_losses = df_og.at[box_scores[i].away_team.team_id, 'Losses']
            stats_temp_away_ties = df_og.at[box_scores[i].away_team.team_id, 'Ties']
            if box_scores[i].home_score > box_scores[i].away_score:
                home_wins = stats_temp_home_wins + 1
                home_losses = stats_temp_home_losses
                home_ties = stats_temp_home_ties
                away_wins = stats_temp_away_wins
                away_losses = stats_temp_away_losses + 1
                away_ties = stats_temp_away_ties
            elif box_scores[i].home_score < box_scores[i].away_score:
                home_wins = stats_temp_home_wins
                home_losses = stats_temp_home_losses + 1
                home_ties = stats_temp_home_ties
                away_wins = stats_temp_away_wins + 1
                away_losses = stats_temp_away_losses
                away_ties = stats_temp_away_ties
            if box_scores[i].home_score == box_scores[i].away_score:
                home_wins = stats_temp_home_wins
                home_losses = stats_temp_home_losses
                home_ties = stats_temp_home_ties + 1
                away_wins = stats_temp_away_wins
                away_losses = stats_temp_away_losses
                away_ties = stats_temp_away_ties + 1
        try:
            print(box_scores[i].home_team.ties)
            home_record = str(box_scores[i].home_team.wins) + "-" + str(box_scores[i].home_team.losses) + "-" + + box_scores[i].home_team.ties
        except:
            home_record = str(box_scores[i].home_team.wins) + "-" + str(box_scores[i].home_team.losses) + "-0"
        try:
            print(box_scores[i].away_team.ties)
            away_record = str(box_scores[i].away_team.wins) + "-" + str(box_scores[i].away_team.losses) + "-" + + box_scores[i].away_team.ties
        except:
            away_record = str(box_scores[i].away_team.wins) + "-" + str(box_scores[i].away_team.losses) + "-0"
        home_plusminus = home_weeklyscore - away_weeklyscore
        away_plusminus = away_weeklyscore - home_weeklyscore
        if week == 1:
            cume_home_points = home_weeklyscore
            cume_away_points = away_weeklyscore
        else:
            cume_home_points = df_og.at[box_scores[i].home_team.team_id, 'Cumulative points'] + home_weeklyscore
            cume_away_points = df_og.at[box_scores[i].away_team.team_id, 'Cumulative points'] + away_weeklyscore

        home_array = [box_scores[i].home_team.team_id, box_scores[i].home_team.owner,name_trim_home,week,i,"Home", box_scores[i].home_team.division_name, home_wins,home_losses,home_ties, "(" + str(home_record) + ")",box_scores[i].home_team.points_for,cume_home_points, home_weeklyscore,home_plusminus]
        away_array = [box_scores[i].away_team.team_id, box_scores[i].away_team.owner,name_trim_away,week,i,"Away", box_scores[i].away_team.division_name, away_wins,away_losses,away_ties, "(" + str(away_record) + ")",box_scores[i].away_team.points_for,cume_away_points, away_weeklyscore,away_plusminus]
        if year < 2019:
            print('ESPN deleted all weekly data prior to 2019. only stats are final roster and weekly team scores.')

            # pl_home_starters_array = positional_stat_puller(box_scores[i].home_team)
            # pl_away_starters_array = positional_stat_puller(box_scores[i].away_team)
        else:
            pl_home_starters_array = positional_stat_puller(box_scores[i].home_lineup)
            pl_away_starters_array = positional_stat_puller(box_scores[i].away_lineup)

        for value in pl_home_starters_array:
            home_array.append(value)
        team_dic[name_trim_home] = home_array
        for value in pl_away_starters_array:
            away_array.append(value)
        team_dic[name_trim_away] = away_array

    df = pd.DataFrame(team_dic)
    df1_transposed = df.T

    df1_transposed = df1_transposed.rename(columns={0: "Team ID", 1:'Owner' ,2:'Team Name', 3: 'Week', 4: "Matchup_ID", 5: "Home/Away", 6: "Division",7:'Wins', 8: 'Losses', 9:'Ties', 10: 'Record (season)', 11: "Total pts (season)",12:'Cumulative points',13:'Points for (week)', 14: 'Plus/Minus'})
    #
    rb_count = 0
    wr_count = 0
    for col in range(9):
        if pl_home_starters_array[col][1] == "RB" and rb_count == 0:
            new_col = "RB1"
            rb_count = 1
        elif pl_home_starters_array[col][1] == "RB" and rb_count == 1:
            new_col = "RB2"
        elif pl_home_starters_array[col][1] == "WR" and wr_count == 0:
            new_col = "WR1"
            wr_count = 1
        elif pl_home_starters_array[col][1] == "WR" and rb_count == 1:
            new_col = "WR2"
        else:
            new_col = pl_home_starters_array[col][1]
        df1_transposed = df1_transposed.rename(columns={col+15: new_col})
    df1_transposed = df1_transposed.rename(columns={24: "BE"})
    df1_transposed = df1_transposed.set_index('Team ID')
    print('df1_transposed is here:')
    print(df1_transposed)
    return df1_transposed

    ######################################
    # data for each individual position
    ######################################
    # stats = stats_display(df1_transposed, position)
    """"
    RB_stats = stats_display(df1_transposed, "RB1")
    RB_stats = stats_display(df1_transposed, "RB2")
    WR_stats = stats_display(df1_transposed, "WR1")
    WR_stats = stats_display(df1_transposed, "WR2")
    TE_stats = stats_display(df1_transposed, "TE")
    DHC_stats = stats_display(df1_transposed, "D/ST")
    """
    # return stats


def positional_stat_puller(data):
    ##########################
    # positional data
    ##########################
    rb_cnt = 0
    wr_cnt = 0
    total_bench = []
    qb_home_array = []
    rb1_home_array = []
    rb2_home_array = []
    wr1_home_array = []
    wr2_home_array = []
    te_home_array = []
    flex_home_array = []
    dst_home_array = []
    hc_home_array = []
    all_positions = ['QB', 'TQB', 'RB', 'RB/WR', 'WR', 'WR/TE', 'TE', 'OP', 'DT', 'DE', 'LB', 'DL', 'CB', 'S', 'DB',
                      'DP', 'D/ST', 'K', 'P', 'HC', 'BE', 'IR', '', 'RB/WR/TE', 'ER', 'Rookie']
    position_dic = []
    for j in range(len(data)):
        position_dic.append(data[j].slot_position)
    print(position_dic)
    exit()
    for j in range(len(data)):
        print(data[j].name)
        data[j].name = data[j].name.replace("'", "")
        for position in all_positions:
            if data[j].slot_position == position:
                position_dic[position] = [data[j].name, data[j].slot_position, data[j].points,data[j].position,
                                          data[j].proTeam,data[j].pro_opponent,data[j].projected_points,
                                          data[j].points_breakdown]



        if data[j].slot_position == "IR":
            pass
        elif data[j].slot_position == "BE":
            bench_home_array = [data[j].name, data[j].slot_position, data[j].points]
            total_bench.append([position_dic])

        elif data[j].slot_position == "QB":
            qb_home_array = [data[j].name, data[j].slot_position, data[j].points]
        elif data[j].slot_position == "RB":
            if rb_cnt == 0:
                rb1_home_array = [data[j].name, data[j].slot_position, data[j].points]
                rb_cnt = 1
            else:
                rb2_home_array = [data[j].name, data[j].slot_position, data[j].points]
                print('rb2 array and name:')
                print(rb2_home_array)
                print(data[j].name)
        elif data[j].slot_position == "WR":
            if wr_cnt == 0:
                wr1_home_array = [data[j].name, data[j].slot_position, data[j].points]
                wr_cnt = 1
            else:
                wr2_home_array = [data[j].name, data[j].slot_position, data[j].points]
        elif data[j].slot_position == "TE":
            te_home_array = [data[j].name, data[j].slot_position, data[j].points]
        elif data[j].slot_position == "RB/WR/TE":
            flex_home_array = [data[j].name, data[j].slot_position, data[j].points]
        elif data[j].slot_position == "D/ST":
            dst_home_array = [data[j].name, data[j].slot_position, data[j].points]
        elif data[j].slot_position == "HC":
            hc_home_array = [data[j].name, data[j].slot_position, data[j].points]
    pl_array = [qb_home_array, rb1_home_array, rb2_home_array, wr1_home_array, wr2_home_array,
                              te_home_array, flex_home_array, dst_home_array, hc_home_array, total_bench]
    for i in range(len(pl_array)):
        if not pl_array[i]:
            pl_array[i] = ["empty","",0.0]
        else:
            pass
    return pl_array


def stats_display(df, position):
    # stat_df = df[['Team ID','Week','Matchup_ID',position]]
    # stat_df[['Player', 'Position', 'Points']] = pd.DataFrame(stat_df[position].tolist(), index=stat_df.index)
    # stat_df = stat_df[['Player', 'Points']]
    # stat_df = stat_df.sort_values(by='Points', ascending=False)
    #df[['Player', 'Position', 'Points']] = pd.DataFrame(df[position].tolist(), index=df.index)

    return df

def compile_stats(position):
    for pos in position:
        print(pos)
        for i in range(1,14):
            print("##############################")
            print("week " + str(i) + " " + str(pos) +  " points")
            print("##############################")
            if i == 1:

                df = side_points(0,i, pos)
            elif i > 1:
                df2 = side_points(0,i, pos)
                df = df.append(df2)
                print(df)

        print(df)
        # df.to_csv(str(position) + "_out.csv", encoding="utf-8-sig")
        df.to_csv(str('Fulldata') + "_out.csv", encoding="utf-8-sig")

def scheduler(league_index, username, password, year, week, timer):
    league = League(league_id=league_index, year=year, espn_s2=username, swid=password)
    matchups = league.box_scores(week)
    file_str = str(league_index) + '_' + str(year) + '_' + str(week) + "_TDEP.csv"
    if os.path.isfile(file_str):
        print('file exists. Collecting data.')
        schedule.every(timer).minutes.do(week_scores, file=file_str, timer=timer,league=league,week=week)
        #schedule.every(timer).seconds.do(week_scores, file=file_str,matchups=matchups, timer=timer,league=league,week=week)

    else:
        home_dict = {}
        away_dict = {}
        for i in range(0,6):
            home_dict[i] = [i,matchups[i].home_team.team_id,deEmojify(matchups[i].home_team.team_name),0]
            away_dict[i+6] = [i,matchups[i].away_team.team_id,deEmojify(matchups[i].away_team.team_name),0]
            z = {**home_dict, **away_dict}
        df = pd.DataFrame.from_dict(z, orient='index')
        df = df.rename(columns={0: 'matchup ID', 1: 'team ID', 2: 'Team', 3: 0})
        df.to_csv(str(league_index) + '_' + str(year) + '_' + str(week) + "_TDEP.csv",encoding="utf-8-sig",index=False)
        print(df)
        print('file for week selected did not exist. creating file.')

def week_scores(file, timer,league,week):
    og_df = pd.read_csv(file,encoding="utf-8-sig")
    home_dict = {}
    away_dict = {}
    matchups = league.box_scores(week)

    for i in range(0,6):
        home_dict[i] = [matchups[i].home_score]
        away_dict[i+6] = [matchups[i].away_score]
        z = {**home_dict, **away_dict}
        df = pd.DataFrame.from_dict(z, orient='index')
        df = df.rename(columns={0:int(og_df.columns[-1])+timer})
    og_df = og_df.join(df)
    print(og_df)
    og_df.to_csv(file,encoding="utf-8-sig",index=False)

def pull_all_data(league_index, username, password, draft,year):
    weekly_df_array = []

    for year in range(2022,2023):

        # league = League(league_id=league_index, year=year,username=username, password=password)
        league = League(league_id=league_index, year=year,espn_s2=username, swid=password)
        print('week: ' + str(league.nfl_week))
        if draft == 0:
            for i in range(1, league.nfl_week):
                if year < 2019:
                    box_scores = league.scoreboard(i)
                    print(box_scores[i].home_team)
                    print(box_scores[i].home_score)
                    print(box_scores)

                else:
                    box_scores = league.box_scores(i)
                    if i == 1:
                        stats = side_points(box_scores, i, 'null', year)
                        weekly_df_array.append(stats)
                    else:
                        print(i)
                        stats_append = side_points(box_scores, i, weekly_df_array[i-2], year)
                        weekly_df_array.append(stats_append)
            combined_df = pd.concat(weekly_df_array)
            print(combined_df)
            combined_df.to_csv(str(league_index) + "_" + str(year) + "_team_stats.csv", encoding="utf-8-sig")
        elif draft == 1:
            pick = league.draft
            array = []
            for p in range(len(pick)):
                temp_player = league.player_info(name=None, playerId=pick[p].playerId)
                player_value = round(temp_player.total_points / pick[p].bid_amount,2)
                pick_array = {'team ID': pick[p].team.team_id,'Owner': pick[p].team.owner,'Player ID': pick[p].playerId, 'Player Name': pick[p].playerName,
                              'Pro Team':temp_player.proTeam,'Position':temp_player.position,'Total Points':
                                  temp_player.total_points,'Round Drafted': pick[p].round_num, 'round_pick':
                                  pick[p].round_pick,'Position Drafted':p+1, 'bid_amount': pick[p].bid_amount, "Dollar value":player_value}
                array.append(pick_array)
            df = pd.DataFrame(array)
            print(df)
            df.to_csv(str(league_index) + "_" + str(year) + "draft_stats.csv", encoding='utf-8-sig')


def side_points_tabulator(file, start, end,save_data,position):
    df = pd.read_csv(file, encoding='utf-8-sig')
    # iterate thru all weeks to pull all weekly stats
    for i in range(start,end):
        print('++++++++++++++++++++++++++week ' + str(i) + "+++++")
        df_week = df.loc[df['Week'] == i]   # trim df to be only those for the week of interest
        #print(df_week)

        # positions for stats
        pos = ['QB', 'RB1', 'RB2','WR1','WR2','TE','D/ST','HC','Points for (week)','Plus/Minus']
        df_meta = df_week[['Team ID', 'Week', "Owner"]]
        df_array = []
        for count, var in enumerate(pos):
            df_pos_temp = df_week[[var]] # make temporary dataframe with only the column of interest
            if count < 8:
                df_pos_temp[var] = df_pos_temp[var].apply(literal_eval) # make sure it's the correct type (list, int)
                df_pos_temp[['Player','Position','Points']] = pd.DataFrame(df_pos_temp[var].tolist(),index= df_pos_temp.index) # split array into individual columns
                del df_pos_temp[var]

            else:
                df_pos_temp = df_pos_temp.sort_values(by=var, ascending=False)
            df_final = pd.concat([df_meta, df_pos_temp], axis=1)  # array with all data
            df_array.append(df_final)

        side_point_list = []

        #### Most total points ##################################
        df_tot_pts = df_array[8].copy()
        df_tot_pts = df_tot_pts.sort_values(by='Points for (week)', ascending=False).reset_index(drop=True) #Side point RB data
        df_tot_pts['Side points'] = 0.0
        # do logic to figure out if multiple top scorers
        if df_tot_pts.at[0,'Points for (week)'] == df_tot_pts.at[1,'Points for (week)']:
            df_tot_pts.at[0,'Side points'] = 2
            df_tot_pts.at[1,'Side points'] = 2
        else:
            df_tot_pts.at[0, 'Side points'] = 2
        side_point_list.append(df_tot_pts)

        #### QB points ##################################
        df_array[0]['Total QB points'] = df_array[0]['Points']
        del df_array[0]['Points']
        df_array[0] = df_array[0].sort_values(by='Total QB points', ascending=False).reset_index(drop=True) #Side point RB data
        df_array[0]['Side points'] = 0.0
        # do logic to figure out if multiple top scorers
        if df_array[0].at[0,'Total QB points'] == df_array[0].at[1,'Total QB points']:
            df_array[0].at[0,'Side points'] = 1
            df_array[0].at[1,'Side points'] = 1
        else:
            df_array[0].at[0, 'Side points'] = 1
        side_point_list.append(df_array[0])

        #### RB points ##################################
        df_array[1]['RB1'] = df_array[1]['Player']
        df_array[1]['RB2'] = df_array[2]['Player']
        df_array[1]['Total RB points'] = df_array[1]['Points'] + df_array[2]['Points']
        del df_array[1]['Points']
        df_array[1] = df_array[1].sort_values(by='Total RB points', ascending=False).reset_index(drop=True) #Side point RB data
        df_array[1]['Side points'] = 0.0
        # do logic to figure out if multiple top scorers
        if df_array[1].at[0,'Total RB points'] == df_array[1].at[1,'Total RB points']:
            df_array[1].at[0,'Side points'] = 1
            df_array[1].at[1,'Side points'] = 1
        else:
            df_array[1].at[0, 'Side points'] = 1
        side_point_list.append(df_array[1])

        #### WR points ##################################
        df_array[3]['WR1'] = df_array[3]['Player']
        df_array[3]['WR2'] = df_array[4]['Player']
        df_array[3]['Total WR points'] = df_array[3]['Points'] + df_array[4]['Points']
        del df_array[3]['Points']
        df_array[3] = df_array[3].sort_values(by='Total WR points', ascending=False).reset_index(drop=True) #Side point RB data
        df_array[3]['Side points'] = 0.0
        # do logic to figure out if multiple top scorers
        if df_array[3].at[0,'Total WR points'] == df_array[3].at[1,'Total WR points']:
            df_array[3].at[0,'Side points'] = 1
            df_array[3].at[1,'Side points'] = 1
        else:
            df_array[3].at[0, 'Side points'] = 1
        side_point_list.append(df_array[3])

        #### TE points ##################################
        df_array[5]['Total TE points'] = df_array[5]['Points']
        del df_array[5]['Points']
        df_array[5] = df_array[5].sort_values(by='Total TE points', ascending=False).reset_index(drop=True) #Side point RB data
        df_array[5]['Side points'] = 0.0
        # do logic to figure out if multiple top scorers
        if df_array[5].at[0,'Total TE points'] == df_array[5].at[1,'Total TE points']:
            df_array[5].at[0,'Side points'] = 0.5
            df_array[5].at[1,'Side points'] = 0.5
        else:
            df_array[5].at[0, 'Side points'] = 0.5
        side_point_list.append(df_array[5])

        #### DST/HC points ##################################
        df_array[6]['D/ST'] = df_array[6]['Player']
        df_array[6]['HC'] = df_array[7]['Player']
        df_array[6]['Total DST/HC points'] = df_array[6]['Points'] + df_array[7]['Points']
        del df_array[6]['Points']
        df_array[6]['Position'] = 'DST/HC'
        df_array[6] = df_array[6].sort_values(by='Total DST/HC points', ascending=False).reset_index(drop=True) #Side point RB data
        df_array[6]['Side points'] = 0.0
        # do logic to figure out if multiple top scorers
        if df_array[6].at[0,'Total DST/HC points'] == df_array[6].at[1,'Total DST/HC points']:
            df_array[6].at[0,'Side points'] = 0.5
            df_array[6].at[1,'Side points'] = 0.5
        else:
            df_array[6].at[0, 'Side points'] = 0.5
        side_point_list.append(df_array[6])

        #### most point scored by owner who loses (0.5), dfs 8 and 9 ##################################
        df_mpsl = df_array[8].copy()
        df_mpsl['Plus/Minus'] = df_array[9]['Plus/Minus']
        df_mpsl_neg = df_mpsl[df_mpsl['Plus/Minus'] < 0.0]   # trim df to be only those for the week of interest
        df_mpsl_pos = df_mpsl[df_mpsl['Plus/Minus'] >= 0.0]   # trim df to be only those for the week of interest
        df_mpsl_neg = df_mpsl_neg.sort_values(by='Points for (week)', ascending=False).reset_index(drop=True)
        df_mpsl_pos = df_mpsl_pos.sort_values(by='Points for (week)', ascending=True).reset_index(drop=True)
        df_mpsl = df_mpsl_neg.append(df_mpsl_pos).reset_index(drop=True)
        df_mpsl['Side points'] = 0.0
        df_mpsl.at[0,'Side points'] = 0.5
        side_point_list.append(df_mpsl)

        #### Lost with second highest score out of all owners (1 pt) dfs 8 and 9 ##################################
        df_lshs = df_array[8].copy()
        df_lshs['Plus/Minus'] = df_array[9]['Plus/Minus']
        df_lshs = df_lshs.sort_values(by='Points for (week)', ascending=False).reset_index(drop=True)
        df_lshs['Side points'] = 0.0
        if df_lshs.at[1,'Plus/Minus'] < 0:
            df_lshs.at[1,'Side points'] = 1.0
        else:
            pass
        side_point_list.append(df_lshs)

        #### Least amount of points scored by an owner (-.5 points) ##################################
        df_least = df_array[8].copy()
        df_least = df_least.sort_values(by='Points for (week)', ascending=True).reset_index(drop=True)
        df_least['Side points'] = 0.0
        ### if tie code
        if df_least.at[0,'Points for (week)'] == df_least.at[1,'Points for (week)']:
            df_least.at[0,'Side points'] = -0.5
            df_least.at[1,'Side points'] = -0.5
        else:
            df_least.at[0, 'Side points'] = -0.5
        side_point_list.append(df_least)

        #### Largest margin of victory (0.5 points) ##################################
        df_lrgst_margin = df_array[9].copy()
        df_lrgst_margin = df_lrgst_margin.sort_values(by='Plus/Minus', ascending=False).reset_index(drop=True)
        df_lrgst_margin['Side points'] = 0.0
        ### if tie code
        if df_lrgst_margin.at[0,'Plus/Minus'] == df_lrgst_margin.at[1,'Plus/Minus']:
            df_lrgst_margin.at[0,'Side points'] = 0.5
            df_lrgst_margin.at[1,'Side points'] = 0.5
        else:
            df_lrgst_margin.at[0, 'Side points'] = 0.5

        side_point_list.append(df_lrgst_margin)

        ## format the DF to store stuff
        df_names = ['Total points', 'QB points', 'RB points','WR points','TE points','DST/HC points','Most pts scored by losing owner','Lost with second highest pts','Least amount of pts','Largest margin of victory']
        final_total_sidepts = side_point_list[0].copy()
        final_total_sidepts = final_total_sidepts[['Team ID','Owner', 'Side points']]
        final_total_sidepts.at[0,"Side points"] = 0.0
        final_total_sidepts = final_total_sidepts.set_index('Team ID')
        for v in range(len(side_point_list)):
            #side_point_list[v] = side_point_list[v].head(2)  # trim df to be only top 1 for the week of interest
            if v == 0:
                final_deep_stats = side_point_list[v].copy()
            else:
                final_deep_stats = pd.concat([final_deep_stats, side_point_list[v]], axis=0, ignore_index=True)

            side_point_list[v] = side_point_list[v].set_index('Team ID') # set index to team id
            for team in range(1,13):
                final_total_sidepts.at[team, 'Side points'] = final_total_sidepts.at[team, 'Side points'] + side_point_list[v].at[team, 'Side points']
        final_total_sidepts = final_total_sidepts[final_total_sidepts['Owner'].notna()]
        final_total_sidepts['Week'] = i
        if i == start:
            export_df = final_total_sidepts
            export_deep_stats = final_deep_stats
        else:
            print('appending')
            export_df = export_df.append(final_total_sidepts)
            export_deep_stats = export_deep_stats.append(final_deep_stats)
    #print(export_df)
    #print(export_deep_stats)
    if save_data == 1:
        export_df.to_csv("side-points-2021.csv", encoding='utf-8-sig')
        export_deep_stats.to_csv("side-point-deep-stats-2021.csv", encoding='utf-8-sig')
    if save_data == 2:
        popaxismsg(side_point_list[position],"asf",500)
    if save_data == 3:
        return side_point_list[position]
    if save_data == 4:
        return export_df


def side_point_graphs(data,week):
    df = pd.read_csv(data, encoding='utf-8-sig')
    stat_list = ["Points for (week)", "Total QB points"]
    # dfs for: QB RB WR TE DST/HC MOST-PTS LEAST-PTS BIGGEST-WIN CUMULATIVE
    if week == 0:
        pass
    df_temp = df.loc[df['Week'] == week]
    print(df_temp)


def analysis(file):
    df = pd.read_csv(file, encoding='utf-8-sig')
    #df = df.set_index('team ID')
    array = []
    dic = {}
    for i in range(1,13):
        df_2 = df[df['team ID']==i]
        df_2['inverse_pos'] = (192 - df_2["Position Drafted"])
        df_2['weighted pos'] =  df_2['inverse_pos'] * df_2["bid_amount"]
        weighted_value = df_2["weighted pos"].mean()
        array.append(weighted_value)
        dic[df_2['Owner'].iloc[0]] = weighted_value
        a = pd.DataFrame.from_dict(dic,orient='index')
    a = a.rename(columns={0: 'aggression'})
    print(a)
    return a

def draft_decompose(file, pos):
    font = {'family': 'Arial',
            'size': 12}

    matplotlib.rc('font', **font)

    pos_array = ['RB', 'QB', 'WR','TE','D/ST','HC']
    colors = ['Blues', 'Greens','Oranges', 'Reds']

    # following plots position data ($ vs draft pick)
    if pos == 1:
        fig, axs = plt.subplots(2, 3, sharex=True, sharey=True)

        j = 0
        df = pd.read_csv(file, encoding='utf-8-sig')
        for i in pos_array:
            temp_df = df[df['Position']==i]
            print(temp_df)
            if j < 3:
                axs[0, j].scatter(temp_df['Unnamed: 0'], temp_df['bid_amount'], s=35, marker="o",c=temp_df['bid_amount'],edgecolors='black',linewidth=.5)
                plt.text(0.95, 0.95, i, horizontalalignment='right',
                         verticalalignment='top', transform=axs[0, j].transAxes)
                axs[0, j].xaxis.set_major_locator(MultipleLocator(50))
                axs[0, j].yaxis.set_major_locator(MultipleLocator(20))
                axs[0,0].set_ylabel('Dollars spent')

            else:
                axs[1, j-3].scatter(temp_df['Unnamed: 0'], temp_df['bid_amount'], s=35, marker="o",c=temp_df['bid_amount'],edgecolors='black',linewidth=.5)
                plt.text(0.95, 0.95, i, horizontalalignment='right',
                         verticalalignment='top', transform=axs[1, j-3].transAxes)
                axs[0, j-3].xaxis.set_major_locator(MultipleLocator(50))
                axs[0, j-3].yaxis.set_major_locator(MultipleLocator(20))
                axs[1,0].set_ylabel('Dollars spent')
                axs[1,1].set_xlabel('Draft position')
            j = j+1
        plt.xlim([-10, 192])
        plt.ylim([-2, 80])
        plt.show()

    # following plots team data ($ vs draft pick)
    if pos == 2:
        fig, axs = plt.subplots(3, 4, sharex=True, sharey=True)
        plt.gcf().set_size_inches(8, 8)
        j = 0
        df = pd.read_csv(file, encoding='utf-8-sig')

        for i in df.Owner.unique():

            temp_df = df[df['Owner']==i]
            print('temp df')
            print(temp_df)
            if j < 4:
                off = 0
                row = 0
            elif j>3 and j < 8:
                off = 4
                row = 1
            elif j >7 and j < 12:
                off = 8
                row = 2
            axs[row, j-off].scatter(temp_df['Unnamed: 0'], temp_df['bid_amount'], s=55, marker="o",c=temp_df['bid_amount'],edgecolors='black',linewidth=.75,cmap=cm.YlGnBu,vmin=-20, vmax=80)
            plt.text(0.95, 0.95, i.split(' ')[0], horizontalalignment='right',
                     verticalalignment='top', transform=axs[row, j-off].transAxes,fontsize=12)
            axs[row, j-off].xaxis.set_major_locator(MultipleLocator(50))
            axs[row, j-off].yaxis.set_major_locator(MultipleLocator(20))
            if j-off == 0:
                axs[row, j-off].set_ylabel('Dollars spent')
            if row == 2:
                axs[row, j-off].set_xlabel('Draft position')

            j = j+1

            pass
        plt.xlim([-10, 192])
        plt.ylim([-2, 80])
        plt.tight_layout()
        plt.savefig('foo.svg')
        plt.show()

    # this plots total draft data ($ vs draft pick)
    if pos == 3:
        df = pd.read_csv(file, encoding='utf-8-sig')

        temp_df = df

        fig, axs = plt.subplots(1, 1, sharex=True, sharey=True)
        plt.gcf().set_size_inches(4, 4)

        axs.scatter(temp_df['Unnamed: 0'], temp_df['bid_amount'], s=35, marker="o",
                                  c=temp_df['bid_amount'], edgecolors='black', linewidth=.75, cmap=cm.YlGnBu, vmin=-20,
                                  vmax=120)
        #plt.text(0.95, 0.95, '2021', horizontalalignment='right', verticalalignment='top', transform=axs.transAxes, fontsize=12)
        axs.xaxis.set_major_locator(MultipleLocator(50))
        axs.yaxis.set_major_locator(MultipleLocator(20))
        axs.set_ylabel('Dollars spent')
        axs.set_xlabel('Draft position')

        plt.xlim([-10, 192])
        plt.ylim([-2, 80])
        plt.tight_layout()
        plt.savefig('foo.svg')
        plt.show()

    # this plots aggression coefficient
    if pos == 4:
        file_array = []
        years = ['2017','2018','2019','2020','2021']
        #            anal_df = analysis(i).sort_values(by=['aggression'])

        for i in file:
            anal_df = analysis(i)
            anal_df = anal_df.reset_index()
            for j in years:
                if j in i:
                    anal_df = anal_df.rename(columns={'index': 'Owner','aggression': j})
                else:
                    pass
            for i in range(len(anal_df)):
                j = anal_df.at[i,'Owner'].split(' ')[0]
                anal_df.at[i,'Owner'] = j
                anal_df.set_index('Owner')
            file_array.append(anal_df)

        test_df = pd.concat([file_array[0], file_array[1]], axis=1)
        print(test_df)
        test_df = test_df.loc[:, ~test_df.columns.duplicated()]
        test_df = test_df.sort_values(by=[years[4]])
        test_df = test_df.set_index('Owner')
        arr = []
        for agg in test_df.index.values:
            print(agg)
            arr.append(test_df.at[agg,'2021'] - test_df.at[agg,'2020'])
        print(arr)
        test_df['diff'] = arr

        print(test_df)


        fig, axs = plt.subplots(len(test_df.columns), 1, sharex=False, sharey=True)
        plt.gcf().set_size_inches(10, 10)
        x = np.arange(len(test_df)+1)
        red = Color('#482677')
        colors = list(red.range_to(Color('#B8DE29'), 12))
        colors = [color.rgb for color in colors]
        set = [1,2,3,4,5,6,7,8,9,10,11,12]
        for i in range(len(test_df.columns)):
            print(i)
            print(len(test_df.columns))
            if i == len(test_df.columns)-1:
                print('YES')
                axs[i].bar(test_df.index.values, test_df['diff'], color=colors)
                axs[i].set_ylim([test_df['diff'].min() - 50, test_df['diff'].max()+ 50])
            else:
                axs[i].bar(test_df.index.values,test_df[test_df.columns[i]],color=colors)
                axs[i].set_ylim([test_df['2021'].min() - 50, test_df['2021'].max()+ 50])
                axs[i].set_ylabel('Aggression')
            year = year_finder(test_df.columns[i])
            plt.text(0.07, 0.95, year, horizontalalignment='right',
                     verticalalignment='top', transform=axs[i].transAxes,fontsize=12)

        axs[i].set_xlabel('Owner')

        plt.show()

def year_finder(name):
    years = ['2017', '2018', '2019', '2020', '2021']
    for i in years:
        if i in name:
            return i
        else:
            pass

def popaxismsg(data,poptitle,size):
    gridcounter = 0
    popup = tk.Tk()
    popup.wm_title(poptitle)
    popup.resizable(width=700, height=500)
    S = tk.Scrollbar(popup)
    xscrollbar = tk.Scrollbar(popup, orient=HORIZONTAL)
    T = tk.Text(popup, width=size, wrap=NONE, xscrollcommand=xscrollbar.set)
    xscrollbar.config(command=T.xview)
    xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
    S.pack(side=tk.RIGHT, fill=tk.Y)
    T.pack(side=tk.LEFT, fill=tk.Y)
    S.config(command=T.yview)
    T.config(yscrollcommand=S.set)
    T.pack()
    T.insert(tk.END, data)
    popup.mainloop()