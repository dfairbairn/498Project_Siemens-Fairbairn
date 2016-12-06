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
    sql = 'select * from mygames where GAME_ID in (' + str(in_p) + ')'
    data = pd.read_sql(sql, mysql_cn)

    p_change_vars['TEAM_WINS']=False

    print p_change_vars.index
    for i in p_change_vars.index:
    #for i in range(1,10):
        row = p_change_vars.ix[i]
        print i
        val =  row['PIT_ID']==data.loc[data['GAME_ID']==row['GAME_ID']]['WIN_PIT_ID']
        row['TEAM_WINS'] = (row['PIT_ID']==data.loc[data['GAME_ID']==row['GAME_ID']]['WIN_PIT_ID']).values[0]
        p_change_vars.ix[i] = row

    return p_change_vars


def findPitWin(gameID, pitID, mysql_cn):
    sql = 'select * from mygames where GAME_ID="' + gameID + '"'
    dat = pd.read_sql(sql, mysql_cn)
    return (dat['WIN_PIT_ID'] == pitID)

mysql = MySQL.connect(host='35.160.8.83', port=3306, user='ubuntu', passwd='R3tr0sh33t', db='retrosheet2')

f = findGameWin('WAS201307070', True, mysql)
print f

#r = df.applymap(lambda x: (x['WIN_PIT_ID'] == x['HOME_START_PIT_ID']))

p_change = pd.read_csv('AL_pchange_vars.csv')
