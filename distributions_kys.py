"""
file: distributions.py
authors: David Fairbairn and Kyle Siemens
date: November 2016
description: This file contains code for retrieving our data for the CMPT498
    project on the topic of analyzing the occurrence of switching out the main
    pitcher in recent MLB games.


A function for extracting from the database (event_id,game_id) tuples 
corresponding to change outs of the primary pitcher, and separate functions 
*will* take these data and determine aspects of the game state prior to the 
switch such as:
- winning/losing score differential for team doing the switch out
- #balls in the previous pitch sequence
- #on-base-hits in the previous pitch sequence
-- [Batter destination arrival]
- #outs
- Opposition Season Record
- inning at the time
- RBI/how many runs

"""


import pandas as pd
import MySQLdb as MySQL
import matplotlib.pyplot as plt

# Logging module might be a handy thing to be using 
import logging

def db_connect():
    """ Connect to the database """
    mysql_cn = MySQL.connect(host='35.160.8.83', port=3306, user='ubuntu', \
                                        passwd='R3tr0sh33t', db='retrosheet')
    return mysql_cn

def get_games(mysql_cn, year='2015', team='ANA', table='events'):
    # using the regexp functionality in mysql we can specify substrings
    # e.g. for specifying year
    sql = 'select distinct GAME_ID from %s where GAME_ID regexp %s and HOME_TEAM_ID="%s"' % (table,str(year),team) 
    games_list = pd.read_sql(sql,mysql_cn)

    return games_list   

def get_main_pitch_changes(mysql_cn,table='events',games_list=None):
    """
    Compute the event_ids corresponding to a change of primary pitchers in
    games of the given list.

    Testing situation: Works! But could be faster. Perhaps we *should* just use
    the grand single pandas dataframe

    """

    pitch_changes = pd.DataFrame(columns=["EVENT_ID","GAME_ID"])
    
    if type(games_list)==type(None): 
        sql = 'select distinct GAME_ID from %s' % (table) 
        games_list = (pd.read_sql(sql,mysql_cn))['GAME_ID']
    elif type(games_list)==type(pd.DataFrame()):
        games_list = games_list['GAME_ID']
    else: 
        logging.error( "Bad games list input" )
        return None
    logging.info( "List of games: " + str(games_list))

    pitch_changes=[] # store primary pitcher changes as (EVENT_ID,GAME_ID) tuples)

    for gameid in games_list:
        # Ensure we have game id's as strings
        g = str( gameid )
        logging.info("Checking Game ID: " + g)

        # First, check for a change for the first team
        sql = 'select EVENT_ID, PIT_ID from %s where BAT_HOME_ID="0" and GAME_ID="%s"' % (table,g)
        pitches_0 = pd.read_sql(sql, mysql_cn)

        for i in range(len(pitches_0) - 1): 
            # look for first instance of a change of pitchers 
            if pitches_0['PIT_ID'][i] != pitches_0['PIT_ID'][i+1]:
                pitch_changes.append( (pitches_0['EVENT_ID'][i], g) )
                logging.info("Found a primary switch: ",str(pitches_0['EVENT_ID'][i]),str(g))
                break # Should just break from this inner loop


        # Next, check for a main pitcher change for the opposition 
        sql = 'select EVENT_ID, PIT_ID from %s where BAT_HOME_ID="1" and GAME_ID="%s"' % (table,g)
        pitches_1 = pd.read_sql(sql, mysql_cn)

        for i in range(len(pitches_1) - 1): 
            # look for first instance of a change of pitchers 
            if pitches_1['PIT_ID'][i] != pitches_1['PIT_ID'][i+1]:
                pitch_changes.append( (pitches_1['EVENT_ID'][i], g) )
                logging.info("Found a primary switch: ",str(pitches_1['EVENT_ID'][i]),str(g))
                break # Should just break from this inner loop
   
    # TODO: output list of pitch changes as a pandas df 
    return pitch_changes 


def events_at_eventid(pchange_df, data):
    """
    Grab the events preceding each event_id,game_id pair
    
    **PARAMS**
    pchange_df: A pandas dataframe of event_id, game_id's corresponding to 
                changes of pitchers
    data:   dataframe of all the events of interest

    Events to try to get:
    - winning/losing score differential for team doing the switch out 
        (HOME_SCORE_CT  - AWAY_SCORE_CT or vice versa)
    - #balls, #strikes, #outs in the previous pitch sequence
    - #on-base-hits in the previous pitch sequence (~BAT_DEST_ID ?)
    - Inning
    - How many runs allowed (RBI_CT)
    -- Opposition Season Record?
    """
    f = map(lambda x: data.loc[data['GAME_ID'] == x[1]].loc[data['EVENT_ID'] == x[0]].index[0], pchange_df)
    return data.loc[f]


if __name__ == "__main__":
    
    mysql_cn = db_connect()
    # myevents vs. events - myevents seems to be faster, so maybe its worth 
    # connecting with mysql and specifying a trimmed down events view
    dataframe = pd.read_sql('select * from myevents', mysql_cn)

    #dataframe['GAME_ID'].loc[dataframe.isin([l[1] for l in lst])]
     
 
    gl = get_games(mysql_cn) # function defaults to just getting Anaheim's home 2015 games
    lst = get_main_pitch_changes(mysql_cn, games_list=gl)
    print "List of (event_id, game_id) pairs corresponding to changes of pitcher: \n",lst


    change_events = events_at_eventid(lst, dataframe)

    plt.figure()

    pd.value_counts(change_events['INN_CT'], sort=False).plot(kind='bar', title='Inning')
    pd.value_counts(change_events['BAT_DEST_ID'], sort=False).plot(kind='bar', title='Batter Destination')
    pd.value_counts(change_events['RBI_CT'], sort=False).plot(kind='bar', title='RBIs')
    pd.value_counts(change_events['EVENT_OUTS_CT'], sort=False).plot(kind='bar', title='Outs')
    pd.value_counts(change_events['PA_BALL_CT'], sort=False).plot(kind='bar', title='Balls')

    home = change_events.loc[change_events['BAT_HOME_ID']==1]['HOME_SCORE_CT']-change_events.loc[change_events['BAT_HOME_ID']==1]['AWAY_SCORE_CT']
    away = change_events.loc[change_events['BAT_HOME_ID']==0]['AWAY_SCORE_CT']-change_events.loc[change_events['BAT_HOME_ID']==0]['HOME_SCORE_CT']
    score_diffs = home.merge(away)
    pd.value_counts(score_diffs, sort=False).sort_index().plot(kind='bar', title='Score Diff')


    plt.show()

    mysql_cn.close()