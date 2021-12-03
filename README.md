# git-pork
This is the official data and analytics repo of Pork Rub Fantasy Football. This software is written in Python 3 and uses the ESPN api to pull data. The API can be found here:
[espn-api](https://github.com/cwendt94/espn-api).
Functions that allow for pulling tons or raw data for any league can be found here. Here is a brief listing of functions and what they can do (located in main.py):  

<b>pull_all_data(league_index, username, password, draft)</b>

This function pulls data using your league ID (league_index arg). username and password can also be used if it's a private league. draft is a boolean where 0 does not pull draft data (strictly seasonal data) and 1 pulls strictly draft data.

The seasonal data is pulled and saved into a pandas dataframe which is then saved as a csv file that can be further analyzed/plotted with matplotlib or excel.

Example of dataframe saving data from 2020 season:
![alt text](https://i.imgur.com/cfPEVCQ.png)

The draft data contains all data possible to pull from the api. It dumps data into a pandas dataframe which is also saved to a csv.

Example of dataframe containing data from a draft:
![alt text](https://i.imgur.com/fwA2qlI.png)


