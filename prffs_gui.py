from espn_api.football import League
import CommonFunctions
# gui here
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
import re
import os
import glob
from ast import literal_eval
pd.options.mode.chained_assignment = None  # default='warn'


font = {'family': 'arial',
        'weight': 'normal',
        'size': 18}
matplotlib.rc('font', **font)


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 500)





# python 3 app
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

    def pophelpmsg(self, data, poptitle):
        gridcounter = 0
        popup = tk.Tk()
        popup.wm_title(poptitle)
        #popup.resizable(width=500, height=500)
        S = tk.Scrollbar(popup)
        T = tk.Text(popup, width=60)
        S.pack(side=tk.RIGHT, fill=tk.Y)
        T.pack(side=tk.LEFT, fill=tk.Y)
        S.config(command=T.yview)
        T.config(yscrollcommand=S.set)
        T.pack()
        T.insert(tk.END, data)

        popup.mainloop()

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

        league = League(league_id=917761, year=2020)
        self.roster = ["QB", "RB1", "RB2", "WR1", 'WR2','TE','FLEX','DEF','HC','K']
        # this stuff takes care of setting up the data set entry drop down menu. Location etc #
        self.league_id_lbl = Label(self, text="League ID:")
        self.league_id_lbl.grid(sticky=W, row=gridcounter, column=0)
        self.league_id = Entry(self, width=10)
        self.league_id.insert(0,league_id)
        self.league_id.grid(sticky=W, row=gridcounter, column=1)
        self.pull_data = ttk.Button(self, text="Pull data",command=lambda: MainWindow.pull_data(self))
        self.pull_data.grid(sticky=NW, row=gridcounter, column=2, pady=4, padx=4)

        gridcounter += 1
        self.league_id_lbl = Label(self, text="Username:")
        self.league_id_lbl.grid(sticky=W, row=gridcounter, column=0)
        self.league_id = Entry(self, width=10)
        self.league_id.insert(0,league_id)
        self.league_id.grid(sticky=W, row=gridcounter, column=1)
        gridcounter += 1
        self.league_id_lbl = Label(self, text="Password:")
        self.league_id_lbl.grid(sticky=W, row=gridcounter, column=0)
        self.league_id = Entry(self, width=10)
        self.league_id.insert(0,league_id)
        self.league_id.grid(sticky=W, row=gridcounter, column=1)
        gridcounter += 1

        year_array = MainWindow.year_finder(self, self.league_id.get())
        self.ssn_search_lbl = Label(self, text="Seasons to search")
        self.ssn_search_lbl.grid(sticky=W, row=gridcounter, column=0)
        gridcounter += 1
        self.year_all_toggle = ttk.Checkbutton(self, text="select all?",command=lambda: MainWindow.all_toggle(self,1))
        self.year_all_toggle.state(['!alternate'])
        self.year_all_toggle.state(['!selected'])
        self.year_all_toggle.grid(sticky=W, row=gridcounter, column=0)
        self.week_all_toggle = ttk.Checkbutton(self, text="select all?",command=lambda: MainWindow.all_toggle(self,2))
        self.week_all_toggle.state(['!alternate'])
        self.week_all_toggle.state(['!selected'])
        self.week_all_toggle.grid(sticky=W, row=gridcounter, column=1)
        self.team_all_toggle = ttk.Checkbutton(self, text="select all?",command=lambda: MainWindow.all_toggle(self,3))
        self.team_all_toggle.state(['!alternate'])
        self.team_all_toggle.state(['!selected'])
        self.team_all_toggle.grid(sticky=W, row=gridcounter, column=2)
        self.roster_all_toggle = ttk.Checkbutton(self, text="select all?",command=lambda: MainWindow.all_toggle(self,4))
        self.roster_all_toggle.state(['!alternate'])
        self.roster_all_toggle.state(['!selected'])
        self.roster_all_toggle.grid(sticky=W, row=gridcounter, column=3)

        gridcounter += 1

        self.button_list = []
        self.button_weeks = []
        self.button_teams = []
        self.button_roster = []

        for ctr, check in enumerate(year_array): # create button list of strains
            self.year_list = ttk.Checkbutton(self, text=check)
            self.year_list.state(['!alternate'])
            self.year_list.grid(sticky=W, row=gridcounter, column=0)
            gridcounter += 1
            self.button_list.append(self.year_list)
        gridcounter_wk = 1
        self.ssn_search_lbl = Label(self, text="week(s) to search")
        self.ssn_search_lbl.grid(sticky=W, row=gridcounter_wk, column=1)
        self.ssn_search_lbl = Label(self, text="team(s) to search")
        self.ssn_search_lbl.grid(sticky=W, row=gridcounter_wk, column=2)
        self.ssn_search_lbl = Label(self, text="position(s) to search")
        self.ssn_search_lbl.grid(sticky=W, row=gridcounter_wk, column=3)

        gridcounter_wk += 2
        for i in range(1,17):
            self.week_list = ttk.Checkbutton(self, text=i)
            self.week_list.state(['!alternate'])
            self.week_list.grid(sticky=W, row=gridcounter_wk, column=1)
            gridcounter_wk += 1
            self.button_weeks.append(self.week_list)
        gridcounter_wk = 3
        for i in league.teams:
            self.team_list = ttk.Checkbutton(self, text=str(i))
            self.team_list.state(['!alternate'])
            self.team_list.grid(sticky=W, row=gridcounter_wk, column=2)
            gridcounter_wk += 1
            self.button_teams.append(self.team_list)
        gridcounter_wk = 3

        for i in self.roster:
            self.roster_list = ttk.Checkbutton(self, text=str(i))
            self.roster_list.state(['!alternate'])
            self.roster_list.grid(sticky=W, row=gridcounter_wk, column=3)
            gridcounter_wk += 1
            self.button_roster.append(self.roster_list)


    def pull_data(self):
        df = pd.read_csv("df.csv")
        for i in range(len(self.button_list)):
            if str(self.button_list[i].state()) == "('selected',)":
                league = League(league_id=917761, year=int(self.button_list[i].cget("text")))
                for j in range(len(self.button_weeks)):
                    if str(self.button_weeks[j].state()) == "('selected',)":
                        for k in range(len(self.button_teams)):
                            if str(self.button_teams[k].state()) == "('selected',)":
                                matchups = league.scoreboard(int(self.button_weeks[j].cget("text")))
                                for x in range(0,5):
                                    if str(matchups[x].home_team) == str(self.button_teams[k].cget("text")):
                                        print(str(matchups[x].home_team))
                                        for l in range(len(self.button_roster)):
                                            #box_scores = league.box_scores(int(self.button_weeks[j].cget("text")))
                                            id = league.teams[0].roster[0].playerId
                                            player = league.player_info(playerId=id)
                                            print(player)
                                            if str(self.button_roster[l].state()) == "('selected',)":
                                                pass

                                    elif str(matchups[x].away_team) == str(self.button_teams[k].cget("text")):
                                        print(str(matchups[x].away_team))

                                for l in range(len(self.button_roster)):
                                    if str(self.button_roster[l].state()) == "('selected',)":
                                        pass

    def all_toggle(self,value):
        if value == 1:
            if self.year_all_toggle.instate(['selected']):
                for i in self.button_list:
                    i.state(['selected'])

            elif self.year_all_toggle.instate(['!selected']):
                for i in self.button_list:
                    i.state(['!selected'])
        elif value == 2:
            if self.week_all_toggle.instate(['selected']):
                for i in self.button_weeks:
                    i.state(['selected'])
            elif self.week_all_toggle.instate(['!selected']):
                for i in self.button_weeks:
                    i.state(['!selected'])

        elif value == 3:
            if self.team_all_toggle.instate(['selected']):
                for i in self.button_teams:
                    i.state(['selected'])

            elif self.team_all_toggle.instate(['!selected']):
                for i in self.button_teams:
                    i.state(['!selected'])
        elif value == 4:
            if self.roster_all_toggle.instate(['selected']):
                for i in self.button_roster:
                    i.state(['selected'])

            elif self.roster_all_toggle.instate(['!selected']):
                for i in self.button_roster:
                    i.state(['!selected'])


    def year_finder(self, id):
        self.year_array = []
        for i in range(2011, 2021):
            try:
                league = League(league_id=id, year=i)
                self.year_array.append(i)
                self.league_loaded = 1
            except:
                print(str(self.league_id.get()) + "League did not exist. skipping.")
        return self.year_array

#app = IoPlot()
#app.geometry("500x500")
#app.mainloop()