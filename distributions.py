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
import timeit

def db_connect():
    """ Connect to the database """
    mysql_cn = MySQL.connect(host='35.160.8.83', port=3306, user='ubuntu', \
                                        passwd='R3tr0sh33t', db='retrosheet2')
    return mysql_cn

def get_games(mysql_cn, year='2015', team='ANA', table='events'):
    """
    Grab a list of game ID's for a particular year and team from the events table.
    """
    # using the regexp functionality in mysql we can specify substrings
    # e.g. for specifying year
    sql = 'select distinct GAME_ID from %s where GAME_ID regexp %s and HOME_TEAM_ID="%s"' % (table,str(year),team) 
    games_list = pd.read_sql(sql,mysql_cn)

    return games_list   

def get_main_pitch_changes(df, games_list=None):
    """
    Compute the event_ids corresponding to a change of primary pitchers in
    games of the given list.

    ** PARAMS **
    df : dataframe containing the games and events of interest
    [games_list] : can specify a list of game ID's from which to restrict the 
                    search for pitching changes from the given table

    ** RETURNS **
    pitch_changes: a list of (event_id, game_id, pitch_counts-before-change) tuples.

                    This list is intended to then be used by a different method
                    which would grab other events (e.g. ball count) surrounding
                    the (event_id, game_id)

    """
    if games_list==None:
        games_list = dataframe['GAME_ID'].unique()
    elif type(games_list)==type([]):
        games_list = dataframe(games_list, columns=['GAME_ID'])

    pitch_changes=[] # store primary pitcher changes as (EVENT_ID,GAME_ID) tuples)
    
    for gameid in games_list:
        # Ensure we have game id's as strings

        g = str( gameid )
        logging.info("Checking Game ID: " + g)

        # First, check for a change for the first team

        pitches_0 = df.loc[df['BAT_HOME_ID']==0].loc[df['GAME_ID']==g]
        
        pitch_counts = 0
        for i in range(len(pitches_0) - 1): 
            # look for first instance of a change of pitchers 
            if pitches_0['PIT_ID'].iloc[i] != pitches_0['PIT_ID'].iloc[i+1]:
                pitch_changes.append( (pitches_0['EVENT_ID'].iloc[i], g, pitch_counts) )
                logging.info("Found a primary switch: ",str(pitches_0['EVENT_ID'].iloc[i]),str(g))
                break # Should just break from this inner loop
            else:
                # len(pitches_0['PITCH_SEQ_TX'][i])
                pitch_counts += parse_pseq(pitches_0['PITCH_SEQ_TX'].iloc[i])

        # Next, check for a main pitcher change for the opposition 
        pitches_1 = df.loc[df['BAT_HOME_ID']==1].loc[df['GAME_ID']==g]
        pitch_counts = 0
        for i in range(len(pitches_1) - 1): 
            # look for first instance of a change of pitchers 
            if pitches_1['PIT_ID'].iloc[i] != pitches_1['PIT_ID'].iloc[i+1]:
                pitch_changes.append( (pitches_1['EVENT_ID'].iloc[i], g, pitch_counts) )
                logging.info("Found a primary switch: ",str(pitches_1['EVENT_ID'].iloc[i]),str(g))
                break # Should just break from this inner loop
            else:
                pitch_counts += parse_pseq(pitches_1['PITCH_SEQ_TX'].iloc[i])
    return pitch_changes 


def get_main_pitch_changes2(mysql_cn,table='events',games_list=None):
    """
    ** Deprecated **

    Compute the event_ids corresponding to a change of primary pitchers in
    games of the given list.

    ** PARAMS **
    mysql_cn : sql connection so that the database can be accessed
    [table] : string for which table within the database should be queried 
                for accessing events (could be the name of a view)
    [games_list] : can specify a list of games from which to restrict the 
                    search for pitching changes from the given table

    ** RETURNS **
    pitch_changes: a list of (event_id, game_id, pitch_counts-before-change) tuples.

                    This list is intended to then be used by a different method
                    which would grab other events (e.g. ball count) surrounding
                    the (event_id, game_id)


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
                pitch_counts += parse_pseq(pitches_0['PITCH_SEQ_TX'][i])

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
                pitch_counts += parse_pseq(pitches_1['PITCH_SEQ_TX'][i])
    return pitch_changes 

def get_pitch_counts(events):
    """ 
    For the list of events, find the number of pitches performed by pitcher in that game.

    *** Right now, we accomplish this in get_main_pitch_changes and events_at_eventid, but
    this function might be necessary if we want the pitch counts for events *other* than the
    event immediately preceding a pitch change. *** 

    """
    return -1

def events_at_eventid(pchange, data, get_pitcount=True, get_scorediff=True):
    """
    Grab the events preceding each event_id,game_id pair.
    
    **PARAMS**
    pchange :   A list of event_id, game_id's, and pitch counts corresponding to 
                changes of pitchers
    data :      dataframe of all the events of interest
    [get_pitcount] :    boolean flag denoting whether to attempt to fold in pitch #'s into DF
    [get_scorediff] :   boolean flag denoting whether to attempt to fold in score diffs into DF

    **RETURNS**
    f : a pandas dataframe with only the events at the event_id,game_id times as
        specified within pchange

    Events to try to get:
    - winning/losing score differential for team doing the switch out 
        (HOME_SCORE_CT  - AWAY_SCORE_CT or vice versa)
    - #balls, #strikes, #outs in the previous pitch sequence
    - #on-base-hits in the previous pitch sequence (~BAT_DEST_ID ?)
    - Inning
    - How many runs allowed (RBI_CT)
    - pitch counts -- PIT_CT
    -- Opposition Season Record?
    """
    # Right now: grabs all events just before pitcher change. 
    # TODO: variable window of n events before window?

    # Grab the events from table 'data' corresponding to game_id, event_id in each row
    f = map(lambda x: data.loc[data['GAME_ID'] == x[1]].loc[data['EVENT_ID'] == x[0]].index[0], pchange)
    f = data.loc[f]

    if get_pitcount:
        #pitch_count_df = pd.DataFrame([ [p[0],p[2]] for p in pchange ],columns=['EVENT_ID','PIT_COUNT'])
        pitch_count_df = pd.DataFrame([ (p[0],p[1],p[2]) for p in pchange], columns=['EVENT_ID','GAME_ID','PIT_COUNT'])
        print pitch_count_df
        # Do a join on the events list in f with the pitch count dataframe (join on EVENT_ID)
        #f_plus_pcount = pd.concat([ f, pitch_count_df ], axis=1)
        f_plus_pcount = pd.merge(f, pitch_count_df, on=['EVENT_ID','GAME_ID'], how='inner')
        f = f_plus_pcount

    if get_scorediff:
        #print "Home and Away look like: ",home
        diff = (f['HOME_SCORE_CT'] - f['AWAY_SCORE_CT']).as_matrix()
        #home = (f.loc[f['BAT_HOME_ID']==1]['HOME_SCORE_CT']-f.loc[f['BAT_HOME_ID']==1]['AWAY_SCORE_CT']).as_matrix()
        #away = (f.loc[f['BAT_HOME_ID']==0]['AWAY_SCORE_CT']-f.loc[f['BAT_HOME_ID']==0]['HOME_SCORE_CT']).as_matrix()
        bat_home = f['BAT_HOME_ID'].as_matrix()

        # for i in rows of f (different events) ... if BAT_HOME_ID = 1 we do Home[i] - Away[i], else Away[i] - Home[i]

        scorediff_df = pd.DataFrame([ (p[0],p[1],diff[i]) if bat_home[i]==1 else (p[0],p[1],-diff[i]) for i,p in enumerate(pchange)], \
                        columns=['EVENT_ID','GAME_ID','SCORE_DIFF'])
        #print scorediff_df
        f = pd.merge(f, scorediff_df, on=['EVENT_ID', 'GAME_ID'], how='inner')

    return f

def parse_pseq(seq):
    """ 
    Parse a pitch sequence transcript from Retrosheet's "PITCH_SEQ_TX" event 
    variable.

    Ignore:    
    1 2 3 . * + > N V   

    e.g. 
    evs = pd.read_sql('select PITCH_SEQ_TX from events where GAME_ID="ANA201505100"',mysql_cn)
    """     
    stlst = '123.+*>NV'
    trimmed = [ char for char in seq if stlst.find(char) == -1 ]
    return len(trimmed)

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

def doStatsAL(mysql_cn):
    """
    Grabs all the events within our scope (2001-2013, American League) and
    does statistics on them? Covariance matrix???

    """
    mysql_cn = db_connect()
    dataframe = pd.read_sql('select * from myevents', mysql_cn)

    st = timeit.default_timer()    
    nl_pchanges = get_main_pitch_changes(dataframe)
    end = timeit.default_timer()
    nl_pch_events = evets_at_eventid(nl_pchanges, dataframe)

    # Extracting the desired columns depends on what we have in the view, so 
    # the below code might be sensitive to change in the DB
    variables = nl_pch_events.iloc[:,['INN_CT','RBI_CT','PA_BALL_CT','EVENT_OUTS_CT','BAT_DEST_ID','SCORE_DIFF','PIT_CT']]
    print variables.cov()

    variables.to_csv("tmp_variables.csv")
    dataframe.to_csv("tmp_dataframe.csv")
    f = open('tmp_timing.txt','w')
    f.write("Took " + str(end-st) + " seconds to determine changes of primary pitchers within our dataset.")
    return dataframe,variables 

if __name__ == "__main__":
    mysql_cn = db_connect()
    # myevents vs. events - myevents is noticeably faster, so maybe its worth 
    # continuing to connect with mysql and creating a trimmed down events view

    st = timeit.default_timer()    
    dataframe = pd.read_sql('select * from myevents', mysql_cn)
    end = timeit.default_timer()
    print "Accessing events in view: ", end-st

    gl = get_games(mysql_cn) # function defaults to just getting Anaheim's home 2015 games
    lst = get_main_pitch_changes2(mysql_cn, table='myevents', games_list=gl)
    print "List of (event_id, game_id) pairs corresponding to changes of pitcher: \n",lst
    change_events = events_at_eventid(lst, dataframe)

    doStatsAL(mysql_cn)
    #plot_events(change_events)
    #mysql_cn.close()   

#    st = timeit.default_timer()    
#    nl_pchanges = get_main_pitch_changes(dataframe)
#    nl_pch_events = events_at_eventid(nl_pchanges, dataframe)
#    end = timeit.default_timer()
#    print "Pitch change ID'ing in View: ", end-st
#    print "List of (event_id, game_id) pairs corresponding to changes of pitcher in view: \n",nl_pchanges




