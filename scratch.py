from espn_api.football import League
import pandas as pd



def raw_player_data(league_index, username, password, year):
    positions = ['QB','RB','WR','TE','D/ST','K','HC']Z
    player_vars = ['acquisitionType', 'eligibleSlots', 'game_played', 'injured', 'injuryStatus', 'name', 'playerId',
                   'points', 'points_breakdown', 'posRank', 'position', 'proTeam', 'pro_opponent', 'pro_pos_rank',
                   'projected_breakdown', 'projected_points', 'projected_total_points', 'slot_position', 'stats',
                   'total_points']
    player_data = {}
    player_data_list = []

    league = League(league_id=league_index, year=year,espn_s2=username, swid=password)
    #df = pd.read_csv('players_2021_wk17.csv' encoding='utf-8-sig')
    for i in positions:
        player_list = league.free_agents(size=100, position=i)
        asdf = player_list[]
        for j in range(len(player_list)):
            player_attributes = [a for a in dir(player_list[j]) if not a.startswith('__') and 'acquisitionType' not in a
                                 and 'game_played' not in a and 'points_breakdown' not in a
                                 and 'injured' not in a
                                 and 'projected_breakdown' not in a]
            for k in player_attributes:
                player_data[k] = getattr(player_list[j], k)
            player_data_list.append(player_data)
            player_data = {}
    df = pd.DataFrame(player_data_list)
    print(df)
    df.to_csv('PLAYERS_OUT.csv', index=False)


password = '{71735CA3-D03A-47E3-BB18-B4314B399BB1}'
espn = "AEAI2axDp0zJHsR%2BXUt496H0E1r56UjU7QjY6OBYkXXGFkO%2FWgfyUys%2BVo%2B4Rsz4k9MBskSsCb8Si6mY1bZDdFzekj4vZ0g5RSHx0T7lNpQP%2BnmkKR5B21OJ9%2Bfpfwt4IMyajlCjG8G%2FU1Z6PnEQXS1l9daaP2gF4palYuw9zjNy%2ByI7NXDj0VDRDc2cw17KRwwjeU3NP%2FbsCF2t3PDPBgAplsX%2BhpUmYXnDa1jSQ5h2rRdI7Rrea7GzztnLtg94MfBkQk5QkRrsUFoq2U96iQk7ugXqpoo7u3azVG9EzDiSPw%3D%3D"


raw_player_data(917761, espn, password,2021)



# THIS IS ONE OF THE STAT PULLERS. CAN'T REMEMBER IF ITS GLOBAL OR NOT

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
    for j in range(len(data)):
        print(data[j].name)
        if data[j].slot_position == "IR":
            pass
        elif data[j].slot_position == "BE":
            bench_home_array = [data[j].name, data[j].slot_position, data[j].points]
            total_bench.append([data[j].name, data[j].slot_position, data[j].points])

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
            pl_array[i] = ['empty','',0.0]
        else:
            pass
    return pl_array