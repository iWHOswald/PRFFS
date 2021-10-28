def side_points(position):
    df = side_points()
    ###############################
    # this needs to find top QB, RB duo, WR duo, TE, DST + HC, most points with loss, lost with second highest points,least amount of points,

    stat_df = df[[position]]
    stat_df[['Player', 'Position', 'Points']] = pd.DataFrame(stat_df[position].tolist(), index=stat_df.index)
    stat_df = stat_df[['Player', 'Points']]
    stat_df = stat_df.sort_values(by='Points', ascending=False)
    #df[['Player', 'Position', 'Points']] = pd.DataFrame(df[position].tolist(), index=df.index)
