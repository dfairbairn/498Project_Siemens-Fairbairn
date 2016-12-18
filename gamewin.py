"""
Finds who wins each game
this is terrible spaghetti code please dont look at me >.<
"""

import numpy as np
import pandas as pd
import MySQLdb as MySQL

def findGameWin(gameID, isHome, mysql_cn):
    sql = 'select * from mygames where GAME_ID="' + gameID + '"'
    row = pd.read_sql(sql, mysql_cn)
    homewin = (row['WIN_PIT_ID'] == row['HOME_START_PIT_ID'])
    return (homewin==isHome)

def findGamesWins(p_change_vars, mysql_cn):
    in_p=', '.join(map(lambda x: ("'" + x + "'"), p_change_vars['GAME_ID'].values))
    sql = 'select * from mynewgames where GAME_ID in (' + str(in_p) + ')'
    data = pd.read_sql(sql, mysql_cn)
    
    p_change_vars['TEAM_WINS']=False
    
    print p_change_vars.index
    for i in p_change_vars.index:
    #for i in range(1,2):
        print i
        row = p_change_vars.ix[i]
        game = data.loc[data['GAME_ID']==row['GAME_ID']]
        homeWin = (game['HOME_WIN'] == 1).values[0]
        homePit = (game['HOME_START_PIT_ID'] == row['PIT_ID']).values[0]
        row['TEAM_WINS'] = (homePit == homeWin)
        p_change_vars.ix[i] = row
   
    return p_change_vars


def findPitWin(gameID, pitID, mysql_cn):
    sql = 'select * from mygames where GAME_ID="' + gameID + '"'
    dat = pd.read_sql(sql, mysql_cn)
    return (dat['WIN_PIT_ID'] == pitID)

if __name__=="__main__":
    mysql = MySQL.connect(host='35.160.8.83', port=3306, user='ubuntu', passwd='R3tr0sh33t', db='retrosheet2')
    f = findGameWin('WAS201307070', True, mysql)
    print f
    #r = df.applymap(lambda x: (x['WIN_PIT_ID'] == x['HOME_START_PIT_ID']))
    
    p_change = pd.read_csv('AL_3pchange_vars.csv')
    
    new_p = findGamesWins(p_change, mysql)
    
    in_p=', '.join(map(lambda x: ("'" + x + "'"), p_change['GAME_ID'].values))
    sql = 'select * from mygames where GAME_ID in (' + str(in_p) + ')'
    data = pd.read_sql(sql, mysql)

