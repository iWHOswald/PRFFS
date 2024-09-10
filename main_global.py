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
import prffs_library_global
import glob
from ast import literal_eval
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
from matplotlib import rcParams

pd.options.mode.chained_assignment = None  # default='warn'


league_str = '917761'
password = '{71735CA3-D03A-47E3-BB18-B4314B399BB1}'
espn = "AEAI2axDp0zJHsR%2BXUt496H0E1r56UjU7QjY6OBYkXXGFkO%2FWgfyUys%2BVo%2B4Rsz4k9MBskSsCb8Si6mY1bZDdFzekj4vZ0g5RSHx0T7lNpQP%2BnmkKR5B21OJ9%2Bfpfwt4IMyajlCjG8G%2FU1Z6PnEQXS1l9daaP2gF4palYuw9zjNy%2ByI7NXDj0VDRDc2cw17KRwwjeU3NP%2FbsCF2t3PDPBgAplsX%2BhpUmYXnDa1jSQ5h2rRdI7Rrea7GzztnLtg94MfBkQk5QkRrsUFoq2U96iQk7ugXqpoo7u3azVG9EzDiSPw%3D%3D"
#league_str = '1018860'
#password = '{A3A24C9B-6362-4155-A24C-9B6362D155A9}'
#espn = 'AEBvp4U1b1bIDog69lrCJxZ2a%2BSS8T7TmrfYGDZlNtLjfJThvvpcJaV2%2BJyMn0L7nyy%2Bw6lS5oKyHnyi0yoE4OESWB6o%2BYTJVZQzgUG7VZBb3mjdVR%2F2POH6zH2lHMZ8MKOD954mVS7Zts0SSyHUT2%2BLUZNGYWwQaQ4VNqDYB4BVodYHrFLbbaJ5eyQFaEQWQzs%2BOZbhMZq1EdtqcYvP0oqqQGmbkycsnmmsL00POHjvdF28wR7YUzQldIgekL0pp%2Fgxs9ZQwtw%2Bz5nQ0dSFuQzx'
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 500)
sns.set_theme(style="white", context="talk")
sns.set(font="Verdana")

font = {'family': 'arial',
        'weight': 'normal',
        'size': 12}
matplotlib.rc('font', **font)
rcParams['figure.figsize'] = 6,6


class IoPlot(tk.Tk):   # IoPlot will inherit attributes from the tkinter module. the (tk.TK) is not technically necesary
    def __init__(self, *args, **kwargs):  # this is here to always load the following. always run when IoPlot is called
        tk.Tk.__init__(self, *args, **kwargs)
        #tk.Tk.iconbitmap(self, default='terpylyticsicon.ico')
        tk.Tk.wm_title(self, "Pork Rub Fantasy analytics tool V 1.0")
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=0)
        container.grid_columnconfigure(0, weight=0)
        menubar = tk.Menu(container)
        helpmenu = Menu(menubar, tearoff=0)
        helpmsg = str("1. fill ")
        aboutmsg = str("Pork Rub Fantasy Analytics Tool (PRFAT) V 1.0" '\n' "Coded in Python 3 by Iain W. H. Oswald, PhD." '\n' "Github: https://github.com/iWHOswald/")
        abouttitle = str("Pork Rub Fantasy Analytics Tool")
        helptitle = str("Help")
        helpmenu.add_command(label="Help", command=lambda: IoPlot.pophelpmsg(self, helpmsg, helptitle))
        helpmenu.add_command(label="About...", command= lambda: IoPlot.pophelpmsg(self, aboutmsg, abouttitle))
        menubar.add_cascade(label="Help", menu=helpmenu)
        tk.Tk.config(self, menu=menubar)
        self.frames = {}
        for F in (MainWindow, SecWindow):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(MainWindow)


    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    #   ANOTHER POP MSG
    def popaxismsg(self, data, poptitle, size):
        gridcounter = 0
        popup = tk.Tk()
        popup.wm_title(poptitle)
        popup.resizable(width=700, height=500)
        S = tk.Scrollbar(popup)
        xscrollbar = tk.Scrollbar(popup, orient=HORIZONTAL)
        T = tk.Text(popup, width=size,wrap=NONE, xscrollcommand=xscrollbar.set)
        xscrollbar.config(command=T.xview)
        xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        S.pack(side=tk.RIGHT, fill=tk.Y)
        T.pack(side=tk.LEFT, fill=tk.Y)
        S.config(command=T.yview)
        T.config(yscrollcommand=S.set)
        T.pack()
        T.insert(tk.END, data)

        popup.mainloop()

class SecWindow(tk.Frame):

    def __init__(self, parent, controller): # setup the layout of the page
        tk.Frame.__init__(self, parent)


class MainWindow(tk.Frame):

    def __init__(self, parent, controller): # setup the layout of the page
        tk.Frame.__init__(self, parent)
        self.league_loaded = 0
        gridcounter = 0  # This is what allows you to easily add new grid elements; just add gridcounter +=1
        #df_og = pd.read_csv('917761_2021_team_stats.csv')
        #max_week = df_og['Week'].max()
        self.arr = []
        max_week = 4
        #for i in df_og['']
        for i in range(max_week):
            self.arr.append(i+1)
        print(self.arr)

        print('weeks played in season: ' + str(max_week))
        try:
            league = League(league_id=917761, year=2022)
        except:
            print('cannot connect to league. Can only generate stats stored locally.')
        self.button_list = []
        self.stats = ['Most points',"QB", "RB", "WR", "TE", 'DST/HC','Most points in loss','2nd highest points in loss',
        'Least points', 'largest margin-of-victory','side points']
        # this stuff takes care of setting up the data set entry drop down menu. Location etc #

        self.league_id_lbl = Label(self, text="League ID:")
        self.league_id_lbl.grid(sticky=W, row=gridcounter, column=0)
        self.league_id = Entry(self, width=10)
        self.league_id.insert(0,league_str)
        self.league_id.grid(sticky=W, row=gridcounter, column=1)
        gridcounter = gridcounter + 1
        self.league_id_lbl = Label(self, text="username:")
        self.league_id_lbl.grid(sticky=W, row=gridcounter, column=0)
        self.username = Entry(self, width=10)
        self.username.insert(0,espn)
        self.username.grid(sticky=W, row=gridcounter, column=1)
        gridcounter = gridcounter + 1
        self.league_id_lbl = Label(self, text="password:")
        self.league_id_lbl.grid(sticky=W, row=gridcounter, column=0)
        self.password = Entry(self, width=10)
        self.password.insert(0,password)
        self.password.grid(sticky=W, row=gridcounter, column=1)
        gridcounter = gridcounter + 1
        self.league_id_lbl = Label(self, text="Year:")
        self.league_id_lbl.grid(sticky=W, row=gridcounter, column=0)
        self.year_id = Entry(self, width=10)
        self.year_id.insert(0,'2022')
        self.year_id.grid(sticky=W, row=gridcounter, column=1)
        gridcounter = gridcounter + 1


        self.pull_data = ttk.Button(self, text="Pull data",command=lambda: prffs_library_global.pull_all_data(self.league_id.get(), self.username.get(), self.password.get(),0,self.year_id.get()))
        self.pull_data.grid(sticky=NW, row=gridcounter, column=0, pady=4, padx=4)
        self.pull_data = ttk.Button(self, text="Pull draft data",command=lambda: prffs_library_global.pull_all_data(self.league_id.get(), self.username.get(), self.password.get(),1,self.year_id.get()))
        self.pull_data.grid(sticky=NW, row=gridcounter, column=1, pady=4, padx=4)

        gridcounter = gridcounter + 1

        var = IntVar()
        self.week = Label(self, text="Weeks:")
        self.week.grid(sticky=W, row=gridcounter, column=0)
        wkvar = StringVar()
        wkvar.set(1)
        self.week = OptionMenu(self, wkvar, *self.arr)
        self.week.grid(sticky=W, row=gridcounter, column=1)

        self.recent_week = self.arr[-1]

        gridcounter = gridcounter + 1
        self.plot_list = []
        for counter, value in enumerate(self.stats):
            #self.stat = ttk.Button(self, text=value,
            #                                       command=lambda: MainWindow.button_lister(self, counter))
            self.stat = Radiobutton(self, text=value, variable=var, value=counter)
            self.stat.grid(sticky=W, row=gridcounter, column=1)
            self.plot = ttk.Checkbutton(self, text="Plot")
            self.plot.state(['!alternate'])
            self.plot.state(['!selected'])
            self.plot.grid(sticky=W, row=gridcounter, column=0)
            self.button_list.append(counter)
            self.plot_list.append(self.plot)
            gridcounter = gridcounter + 1

        self.get_stats = ttk.Button(self, text="view plot",command=lambda: MainWindow.plot_organizer(self,self.plot_list,var.get(),wkvar.get(),0))
        self.get_stats.grid(sticky=NW, row=gridcounter, column=0, pady=4, padx=4)
        self.get_stats = ttk.Button(self, text="get stats",command=lambda: MainWindow.button_lister(self,var.get(),wkvar.get()))
        self.get_stats.grid(sticky=NW, row=gridcounter, column=1, pady=4, padx=4)
        gridcounter = gridcounter + 1
        self.get_stats = ttk.Button(self, text="save wkly plot",command=lambda: MainWindow.plot_organizer(self,self.plot_list,var.get(),wkvar.get(),1))
        self.get_stats.grid(sticky=NW, row=gridcounter, column=0, pady=4, padx=4)
        self.get_stats = ttk.Button(self, text="view cumulative pts",command=lambda: MainWindow.cum_points(self,self.plot_list,var.get(),wkvar.get(),0))
        self.get_stats.grid(sticky=NW, row=gridcounter, column=1, pady=4, padx=4)
        gridcounter = gridcounter + 1
        self.get_stats = ttk.Button(self, text="save cumulative pts plot",command=lambda: MainWindow.cum_points(self,self.plot_list,var.get(),wkvar.get(),1))
        self.get_stats.grid(sticky=NW, row=gridcounter, column=1, pady=4, padx=4)


    def button_lister(self, value,week):
        print(value)
        print('getting stats for week: ' + str(week))
        if week == "cumulative":
            prffs_library_global.side_points_tabulator('917761_' + str(self.year_id.get())+ '_team_stats.csv', 1, self.arr[-1], 2, value)
            print('DF #: ' +  str(value))
        else:
            prffs_library_global.side_points_tabulator('917761_' + str(self.year_id.get())+ '_team_stats.csv', int(week), int(week)+1, 2, value)

    def cum_points(self,df,var,wkvar,save):
        data_array = []
        df_arr = []
        for i in range(1, self.recent_week + 1):
            data = prffs_library_global.side_points_tabulator('917761_2022_team_stats.csv', i, i + 1, 4, var)
            data_array.append(data)
        data_end = pd.concat(data_array).reset_index()

        data_end = data_end.groupby(["Team ID", "Owner"], as_index=False)["Side points"].sum()
        data_end = data_end.sort_values('Side points', ascending=False)

        df_arr.append(data_end)

        MainWindow.plotter(self, df_arr,wkvar, save)

    def plotter2(self, df_array,week,save): # this plots cumulative data.

        # style stuff
        sns.set_theme(style="white", context="talk")
        sns.set(font="Verdana")

        font = {'family': 'arial',
                'weight': 'normal',
                'size': 12}
        matplotlib.rc('font', **font)
        # style stuff

        df_names = []
        fig, axs = plt.subplots(1, 1, sharex=True, sharey=True,figsize=(6, 6))
        MainWindow.name_fix(self, df_array)
        axis = plt.subplot2grid((1, 1), (0, 0))
        print(df_array)
        axis.axhline(0, color="k", clip_on=False)
        sns.barplot(x=df_array['Owner'], y=df_array['Points'], palette="rocket", ax=axis)

        if 'Plus/Minus' in str(df_array['Position'][0]):
            axis.set_title(str(df_array['Position'][0]).replace('Plus/Minus','Margin of victory'))
        axis.set_title('Cumulative ' +  str(df_array['Position'][0]) + ' points through week ' + str(self.recent_week))

        # add text above histograms
        for p in axis.patches:
            axis.annotate("%.2f" % p.get_height(), (p.get_x() + p.get_width() / 2., p.get_height()),
                           ha='center', va='center', fontsize=10, color='black', xytext=(0, 5),
                           textcoords='offset points')
        axis.set_xticklabels(axis.get_xticklabels(), rotation=45)
        sns.despine(bottom=True)
        plt.tight_layout(h_pad=2)
        df_names.append(df_array.columns[:-2].values)
        #filename = str(df_array[0].columns[-2]).replace('/', '-')
        #if self.save_button.instate['']
        if save == 1:
            plt.savefig('week'+str(week)+'_'+ filename +'.png',dpi=300)
        else:
            plt.show()


    def plot_organizer(self,plot_list, value, week,save):
        df_list = []
        for counter, i in enumerate(plot_list):
            if str(i.state()) == "('selected',)":
                if counter != 10:
                    df = prffs_library_global.side_points_tabulator(str(self.league_id.get()) + '_' + str(self.year_id.get())+ '_team_stats.csv', int(week), int(week)+1, 3, counter)
                    print('DF #: ' + str(counter))
                elif counter == 10:
                    df = prffs_library_global.side_points_tabulator(str(self.league_id.get()) + '_' + str(self.year_id.get())+ '_team_stats.csv', int(week), int(week)+1, 4, counter)
                    print('DF #: ' + str(counter))
                df_list.append(df)

        MainWindow.plotter(self, df_list, week,save)


    def name_fix(self,df):
        for i in df['Owner']:

            df["Owner"].replace({i: i.split()[0]}, inplace=True)
        print(df)
        return df


    def plotter(self, df_array,week,save):

        # style stuff
        sns.set_theme(style="white", context="talk")
        sns.set(font="Verdana")

        font = {'family': 'arial',
                'weight': 'normal',
                'size': 12}
        matplotlib.rc('font', **font)
        # style stuff


        num_plots = len(df_array)
        if num_plots == 12:
            num_plots = 1
        print('number of plots to generate: ' + str(num_plots))
        df_names = []
        if num_plots > 0:
            fig, axs = plt.subplots(2, 1, sharex=True, sharey=True,figsize=(6, 6))
            for i in range(len(df_array)):
                MainWindow.name_fix(self, df_array[i])
                axis = plt.subplot2grid((num_plots, 1), (i, 0))

                axis.axhline(0, color="k", clip_on=False)
                if week == 0:
                    sns.barplot(x=df_array[i]['Owner'], y=df_array[i]['Side points'], palette="rocket", ax=axis)
                else:
                    sns.barplot(x=df_array[i]['Owner'], y=df_array[i].iloc[:, -2], palette="rocket", ax=axis)

                if 'week' in str(df_array[i].columns[-2]):
                    axis.set_title(str(df_array[i].columns[-2]).replace('(week)','') + ' (Week ' + str(week)+")")
                elif 'Plus/Minus' in str(df_array[i].columns[-2]):
                    axis.set_title(str(df_array[i].columns[-2]).replace('Plus/Minus','Margin of victory') + ' (Week ' + str(week)+")")
                elif week == 0:
                    axis.set_title('Cumulative side points (Through week ' + str(self.recent_week) + ')')
                else:
                    axis.set_title(str(df_array[i].columns[-2]) + ' (Week ' + str(week)+")")

                # add text above histograms
                for p in axis.patches:
                    axis.annotate("%.2f" % p.get_height(), (p.get_x() + p.get_width() / 2., p.get_height()),
                                   ha='center', va='center', fontsize=10, color='black', xytext=(0, 5),
                                   textcoords='offset points')
                axis.set_xticklabels(axis.get_xticklabels(), rotation=45)
                sns.despine(bottom=True)
                plt.tight_layout(h_pad=2)
                df_names.append(df_array[i].columns[:-2].values)
            if len(df_array) > 1:
                filename = str(df_array[0].columns[-2]).replace('/', '-') + '_' + str(df_array[1].columns[-2]).replace('/', '-')
            else:
                filename = str(df_array[0].columns[-2]).replace('/', '-')
            if save == 1:
                plt.savefig(str(self.year_id.get())+ '_week'+str(week)+'_'+ filename +'.png',dpi=300)
            else:
                plt.show()


    def tdep_plotter(self,df,week,team,division,cumulative,):
        df_teams = df[df['Team id'] == team]
        print(df_teams)


#prffs_library_global.scheduler(917761, espn, password,2021,10,1) # args = leagueID, ID, PW, YEAR, WEEK, time interval
#while True:
#    schedule.run_pending()
#    time.sleep(1)


def plot_intergame_data(df,matchup_id):

    df = pd.read_csv(df,encoding='utf-8-sig')
    name_arr = []
    if matchup_id != 10:
        df = df[df['matchup ID'] == matchup_id]
    for i in df['Team']:
        name_arr.append(i.rstrip().lstrip())

    df_matchup = df.drop(['team ID'],axis=1)
    df1_transposed = df_matchup.T
    df1_transposed = df1_transposed.rename(columns={df1_transposed.columns[0]:name_arr[0],df1_transposed.columns[1]:name_arr[1]})
    df1_transposed = df1_transposed.drop(['Team','matchup ID','0']).reset_index()
    df1_transposed = df1_transposed.melt('index', var_name='cols', value_name='vals')
    print(df1_transposed)

    ###############
    # plot the data

    g = sns.lineplot(x="index", y="vals",hue='cols',palette='magma', data=df1_transposed,markers=True,dashes=False,style='cols',markersize=14,
                     markeredgecolor='black')
    t = sns.lineplot(x="index", y="vals",hue='vals',palette='magma',style='cols', data=df1_transposed,markers=True,dashes=False,markersize=14,
                     markeredgecolor='black')

    sns.despine(bottom=True)

    g.xaxis.set_major_locator(ticker.MultipleLocator(1000))
    g.xaxis.set_major_formatter(ticker.ScalarFormatter())
    g.set_xlabel("Game time (minutes)")

    g.set_ylabel("Points")
    if matchup_id == 10:

        g.legend(loc='lower right',
                 labels=['All teams'],frameon=False)
    else:
        g.legend(loc='lower right',
                 labels=[name_arr[0], name_arr[1]],frameon=False)


    plt.show()
    plt.tight_layout(h_pad=2)

    #plt.savefig(str(matchup_id)+"_t-dep.png", dpi=300)

#for i in range(0,5):
#    plot_intergame_data('917761_2021_6_TDEP.csv',i)
#plot_intergame_data('917761_2021_8_TDEP.csv',10)

def plot_tdependent_data(df,y):

    # this function interpolates between two colors to generate a gradient for the bar graph

    bar_colors = [0,0,0,0,0,0,0,0,0,0,0,0] #initialize an array to store the color values
    #dark_green = Color("#003e17")  #your first color as hex code
    #colors = list(dark_green.range_to(Color("#f4ec16"), 8)) #generate a list of colors for the bar graph
    dark_green = Color("blue")
    colors = list(dark_green.range_to(Color("red"), 12))
    for i in range(len(colors)): # iterate and transpose the values in the list to an array
        bar_colors[i] = str(colors[i])[:-3]
    print(bar_colors) #sanity check to make sure your values look reasonable
    #bar_colors = ['blue','green','purple','black','yellow',]


    df = pd.read_csv(df,encoding='utf-8-sig')
    name_arr = []
    for i in df['Owner']:
        name_arr.append(i.rstrip().lstrip())
    name_arr = name_arr[0:11]

    df = df[['Team ID', 'Owner','Week','Division','Wins','Losses','Ties','Cumulative points']]
    df_arr = []
    for i in df['Team ID']:
        df_temp = df[df['Team ID'] == i]
        if y == 'cum points':
            y_val = 'Cumulative points'
            df_temp = df_temp[['Week',y_val,'Owner']]
            df_arr.append(df_temp)
    print(df_arr)

    ###############
    # plot the data
    for i in range(len(df_arr)):
        g = sns.lineplot(x=df_arr[i]['Week'], y=df_arr[i][y_val],style=df_arr[i]['Owner'],markers=True,dashes=False,markersize=12,markeredgecolor='black')

    sns.despine(bottom=True)

    g.xaxis.set_major_locator(ticker.MultipleLocator(1000))
    g.xaxis.set_major_formatter(ticker.ScalarFormatter())
    g.set_xlabel("Week")

    g.set_ylabel("Points")
    g.legend(loc='lower right',
             labels=name_arr,frameon=False)


    plt.show()
    plt.tight_layout(h_pad=2)

    #plt.savefig(str(matchup_id)+"_t-dep.png", dpi=300)


#plot_tdependent_data('917761_2021_team_stats.csv','cum points')


draft_years = ['917761_2021draft_stats_py.csv','917761_2020_draft_stats.csv']
# analysis('917761_2020draft_stats.csv')


### CALCULATE SIDE POINTS ON PER-WEEK BASIS ###
### ARGS = team_stats CSV, START WEEK, END WEEK ###
# file, start, end,save_data,position
#side_points_tabulator('917761_2021_team_stats.csv', 1,5,1,0)


#week_scores(917761, espn, password,2021,4)

# side poitn graphs
#side_point_graphs('side-point-deep-stats-2021.csv', 1)

### PULL SEASONAL DATA ###
#pull_all_data(917761, espn, password,1)

### DRAFT ANALYSIS IN CSV ###
# draft_decompose(draft_years,4)

app = IoPlot()
app.geometry("500x600")
app.mainloop()
