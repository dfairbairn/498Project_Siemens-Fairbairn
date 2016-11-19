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
        sql = 'select EVENT_ID, PIT_ID, PITCH_SEQ_TX from %s where BAT_HOME_ID="0" and GAME_ID="%s"' % (table,g)
        pitches_0 = pd.read_sql(sql, mysql_cn)
        pitch_counts = 0
        for i in range(len(pitches_0) - 1): 
            # look for first instance of a change of pitchers 
            if pitches_0['PIT_ID'][i] != pitches_0['PIT_ID'][i+1]:
                pitch_changes.append( (pitches_0['EVENT_ID'][i], g, pitch_counts) )
                logging.info("Found a primary switch: ",str(pitches_0['EVENT_ID'][i]),str(g))
                break # Should just break from this inner loop
            else:
                # len(pitches_0['PITCH_SEQ_TX'][i])
                pitch_counts += len(pitches_0['PITCH_SEQ_TX'][i])

        # Next, check for a main pitcher change for the opposition 
        sql = 'select EVENT_ID, PIT_ID, PITCH_SEQ_TX from %s where BAT_HOME_ID="1" and GAME_ID="%s"' % (table,g)
        pitches_1 = pd.read_sql(sql, mysql_cn)
        pitch_counts = 0
        for i in range(len(pitches_1) - 1): 
            # look for first instance of a change of pitchers 
            if pitches_1['PIT_ID'][i] != pitches_1['PIT_ID'][i+1]:
                pitch_changes.append( (pitches_1['EVENT_ID'][i], g, pitch_counts) )
                logging.info("Found a primary switch: ",str(pitches_1['EVENT_ID'][i]),str(g))
                break # Should just break from this inner loop
            else:
                pitch_counts += len(pitches_0['PITCH_SEQ_TX'][i])
    return pitch_changes 

def get_pitch_counts(events):
    """ 
    For the list of events, find the number of pitches performed by pitcher in that game.

    *** Right now, we accomplish this in get_main_pitch_changes and events_at_eventid, but
    this function might be necessary if we want the pitch counts for events *other* than the
    event immediately preceding a pitch change. *** 

    """
    return -1

def events_at_eventid(pchange, data):
    """
    Grab the events preceding each event_id,game_id pair.
    
    **PARAMS**
    pchange: A list of event_id, game_id's corresponding to 
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
    # Right now: grabs all events just before pitcher change. 
    # TODO: variable window of n events before window?
    f = map(lambda x: data.loc[data['GAME_ID'] == x[1]].loc[data['EVENT_ID'] == x[0]].index[0], pchange)
    f = data.loc[f]
    #pitch_count_df = pd.DataFrame([ [p[0],p[2]] for p in pchange ],columns=['EVENT_ID','PIT_COUNT'])
    pitch_count_df = pd.DataFrame([ (p[0],p[1],p[2]) for p in pchange], columns=['EVENT_ID','GAME_ID','PIT_COUNT'])
    print pitch_count_df
    # Do a join on the events list in f with the pitch count dataframe (join on EVENT_ID)
    #f_plus_pcount = pd.concat([ f, pitch_count_df ], axis=1)
    f_plus_pcount = pd.merge(f, pitch_count_df, on=['EVENT_ID','GAME_ID'], how='inner')

    return f_plus_pcount

def parse_pseq(seq):
    """ 
    Parse a pitch sequence transcript from Retrosheet's "PITCH_SEQ_TX" event 
    variable.

    Ignore:    
    1 2 3 . + > N V

    e.g. 
    evs = pd.read_sql('select PITCH_SEQ_TX from events where GAME_ID="ANA201505100"',mysql_cn)
    """     
    return len(seq)

def plot_events(change_events):
    """
    Does bar chart plots of specific event columns in the provided dataframe
    
    Note: A next step might be to find the usual distribution of these events 
        in a given event ID?
    """
    plt.figure()
    pd.value_counts(change_events['INN_CT'], sort=False).sort_index().plot(kind='bar', title='Inning')
    plt.figure()
    pd.value_counts(change_events['BAT_DEST_ID'], sort=False).sort_index().plot(kind='bar', title='Batter Destination')
    plt.figure()
    pd.value_counts(change_events['RBI_CT'], sort=False).sort_index().plot(kind='bar', title='RBIs')
    plt.figure()
    pd.value_counts(change_events['EVENT_OUTS_CT'], sort=False).sort_index().plot(kind='bar', title='Outs')
    plt.figure()
    pd.value_counts(change_events['PA_BALL_CT'], sort=False).sort_index().plot(kind='bar', title='Balls')

    home = pd.DataFrame(change_events.loc[change_events['BAT_HOME_ID']==1]['HOME_SCORE_CT']-change_events.loc[change_events['BAT_HOME_ID']==1]['AWAY_SCORE_CT'])
    away = pd.DataFrame(change_events.loc[change_events['BAT_HOME_ID']==0]['AWAY_SCORE_CT']-change_events.loc[change_events['BAT_HOME_ID']==0]['HOME_SCORE_CT'])
    #print "Home and Away look like: ",home
    score_diffs = home.append(away,ignore_index=True) 
    #print "Type of score_diffs: ",type(score_diffs)
    #print score_diffs
    plt.figure()
    pd.value_counts(score_diffs[0], sort=False).sort_index().plot(kind='bar', title='Score Difference')
    plt.show()

def plot_all_pchanges():
    """ 
    In case we want to run the grand computation all at once (and wait 5 min) 
    """
    mysql_cn = db_connect()
    dataframe = pd.read_sql('select * from events', mysql_cn)
    allpchanges = get_main_pitch_changes(mysql_cn)
    evs_allpchanges = events_at_eventid(allpchanges,dataframe)
    plot_events(evs_allpchanges) 

if __name__ == "__main__":
    
    mysql_cn = db_connect()
    # myevents vs. events - myevents seems to be faster, so maybe its worth 
    # connecting with mysql and specifying a trimmed down events view
    dataframe = pd.read_sql('select * from myevents', mysql_cn)
 
    gl = get_games(mysql_cn) # function defaults to just getting Anaheim's home 2015 games
    
    lst = get_main_pitch_changes(mysql_cn, games_list=gl)
    print "List of (event_id, game_id) pairs corresponding to changes of pitcher: \n",lst
    
    change_events = events_at_eventid(lst, dataframe)
    #plot_events(change_events)

    #mysql_cn.close()   
