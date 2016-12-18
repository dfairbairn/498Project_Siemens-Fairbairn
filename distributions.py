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
import numpy as np
import os 

# Logging module might be a handy thing to be using 
import logging
import timeit

import csv

def db_connect():
    """ Connect to the database """
    mysql_cn = MySQL.connect(host='35.160.8.83', port=3306, user='ubuntu', \
                                        passwd='R3tr0sh33t', db='retrosheet2')
    return mysql_cn

def get_games(mysql_cn, year='2013', team='ANA', table='games'):
    """
    Grab a list of game ID's for a particular year and team from the games table.

    *Hopefully* will stay in the myevents view.
    """
    # using the regexp functionality in mysql we can specify substrings
    # e.g. for specifying year
    sql = 'select distinct GAME_ID from %s where GAME_ID regexp "%s" and HOME_TEAM_ID="%s"' % (table,str(year),team) 
    games_df = pd.read_sql(sql,mysql_cn) 
    games_arr = games_df.as_matrix()
    games_list = [ g[0] for g in games_arr[:]]
    return games_list

def get_data(mysql_cn, games_list=None, table='myevents'):
    """
    Little function to use sql to grab events from the myevents frame.

    Can optionally supply a gameslist param to restrict grabbed games 
    to those corresponding from the given game(s).
    """
    events = None
    for g in games_list:
        sql = 'select * from %s where GAME_ID="%s"' % (table,g)
        tmp_df = pd.read_sql(sql,mysql_cn)
        events = pd.concat( [events, tmp_df],ignore_index=True)
    return events

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
    if type(games_list)==type([]):
        # If function receives a list, turn it into a games dataframe
        games_df = pd.DataFrame(games_list, columns=['GAME_ID'])
    else:
        # If function receives something else, make games dataframe from scratch
        games_df = pd.DataFrame(df['GAME_ID'].unique(), columns=['GAME_ID'])

    pitch_changes=[] # store primary pitcher changes as (EVENT_ID,GAME_ID) tuples)
    
    for gameid in games_df['GAME_ID']:
        #print 'Individual gameid: ',gameid
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

def get_pchanges_nback(df, games_list=None,nback=1):
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
    if type(games_list)==type([]):
        # If function receives a list, turn it into a games dataframe
        games_df = pd.DataFrame(games_list, columns=['GAME_ID'])
    else:
        # If function receives something else, make games dataframe from scratch
        games_df = pd.DataFrame(df['GAME_ID'].unique(), columns=['GAME_ID'])

    pitch_changes=[] # store primary pitcher changes as (EVENT_ID,GAME_ID) tuples)
    
    for gameid in games_df['GAME_ID']:
        #print 'Individual gameid: ',gameid
        # Ensure we have game id's as strings
        g = str( gameid )
        logging.info("Checking Game ID: " + g)

        # First, check for a change for the first team

        pitches_0 = df.loc[df['BAT_HOME_ID']==0].loc[df['GAME_ID']==g]
        
        pitch_counts = 0
        for i in range(len(pitches_0) - 1): 
            # look for first instance of a change of pitchers 
            if pitches_0['PIT_ID'].iloc[i] != pitches_0['PIT_ID'].iloc[i+1]:
                logging.info("Found a primary switch: ",str(pitches_0['EVENT_ID'].iloc[i]),str(g))
                # Found a pitch switch. Now take events 'nback' backwards from there.
                for j in range(nback):
                    # Some edge cases pitch changes might occur so close to the beginning
                    # of the game that e.g. 3 back would be before the game started. So we check.
                    k = i-j
                    if k >= 0:
                        # If we look 1, then 2, then 3 events before a pitch change, then the 
                        # corresponding pitch count here will be pitch_counts-1, pitch_counts-2, ...
                        pitch_changes.append( (pitches_0['EVENT_ID'].iloc[k], g, pitch_counts-j) )
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
                logging.info("Found a primary switch: ",str(pitches_1['EVENT_ID'].iloc[i]),str(g))
                # Found a pitch switch. Now take events 'nback' backwards from there.
                for j in range(nback):
                    # Some edge cases pitch changes might occur so close to the beginning
                    # of the game that e.g. 3 back would be before the game started. So we check.
                    k = i-j
                    if k >= 0:
                        # If we look 1, then 2, then 3 events before a pitch change, then the 
                        # corresponding pitch count here will be pitch_counts-1, pitch_counts-2, ...
                        pitch_changes.append( (pitches_1['EVENT_ID'].iloc[k], g, pitch_counts-j) )
                break # Should just break from this inner loop
            else:
                pitch_counts += parse_pseq(pitches_1['PITCH_SEQ_TX'].iloc[i])
    return pitch_changes 

def events_at_eventid(pchange, data, get_pitcount=True, get_scorediff=True):
    """
    Grab the events preceding each event_id,game_id pair.
    
    **PARAMS**
    pchange :   A list of event_id, game_id's, and pitch counts corresponding to 
                at-bat events close to the time of a change of pitchers
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

    # Grab the events from table 'data' corresponding to game_id, event_id in each row
    f = map(lambda x: data.loc[data['GAME_ID'] == x[1]].loc[data['EVENT_ID'] == x[0]].index[0], pchange)
    f = data.loc[f]

    if get_pitcount:
        pitch_count_df = pd.DataFrame([ (p[0],p[1],p[2]) for p in pchange], columns=['EVENT_ID','GAME_ID','PIT_COUNT'])
        logging.info(pitch_count_df)
        # Do a join on the events list in f with the pitch count dataframe (join on EVENT_ID)
        f_plus_pcount = pd.merge(f, pitch_count_df, on=['EVENT_ID','GAME_ID'], how='inner')
        f = f_plus_pcount

    if get_scorediff:
        #print "Home and Away look like: ",home
        diff = (f['HOME_SCORE_CT'] - f['AWAY_SCORE_CT']).as_matrix()
        bat_home = f['BAT_HOME_ID'].as_matrix()

        scorediff_df = pd.DataFrame([ (p[0],p[1],diff[i]) if bat_home[i]==0 else (p[0],p[1],-diff[i]) for i,p in enumerate(pchange)], \
                        columns=['EVENT_ID','GAME_ID','SCORE_DIFF'])
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
    plt.figure()
    pd.value_counts(change_events['TEAM_WINS'], sort=False).sort_index().plot(kind='bar', title='Team Wins')
    plt.figure()
    pd.value_counts(change_events['PIT_COUNT'], sort=False).sort_index().plot(title='Pitch Count')

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

def pchangesAL(dataframe,fnamecsv,nback=1):
    """
    Grabs all the events within our scope (2001-2013, American League) and
    does statistics on them? Covariance matrix???
    
    dataframe contains events. 
    fnamecsv is the file to write to.
    """
    st = timeit.default_timer()    
    if nback != 1:
        al_pchanges = get_pchanges_nback(dataframe,nback=nback)
    else:
        al_pchanges = get_main_pitch_changes(dataframe)
    end = timeit.default_timer()

    f = open('./tmp_timing.txt','wr')
    f.write("Took " + str(end-st) + " seconds to determine changes of primary \
    pitchers corresponding to file name %s." % fnamecsv)

    with open(fnamecsv, 'wb') as csvfile:
        pwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for tup in al_pchanges:
            logging.info(tup)
            pwriter.writerow([tup[0]] + [tup[1]] + [tup[2]])
        #pwriter.writerows(nl_pchanges) # Would this make the tuples be read as strings later though?
    return al_pchanges

def statsFromAL(dataframe,fnamecsv,variables_csv="./tmp_variables.csv"):
    """
    Takes a file containing the list of pitch changes and gets the events and 
    computes their statistics.
    """
    import os
    al_pchanges = []
    tst = []
    with open(fnamecsv) as csvfile:
        preader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in preader:
            tup = row
            al_pchanges.append(tup)
            tst.append((int(tup[0]),tup[1],int(tup[2])))
    logging.info("al_pchanges: \n",al_pchanges[:10])
    logging.info("tst: \n",tst[:10]) 

    # Extract variables from this particular time
    st = timeit.default_timer()
    al_pch_events = events_at_eventid(tst, dataframe)
    end = timeit.default_timer()
    
    # I wanted to include timing data for both methods that perform time-consuming
    # calculations, so I wrote them to either append or write to file, depending on its presence
    append_or_write = 'a' if os.path.isfile('./tmp_timing.txt') else 'w'
    ftiming = open('tmp_timing.txt',append_or_write)
    ftiming.write('Performing events_at_eventid() for fname=%s took %f seconds.\n' % (fnamecsv, end-st))
    ftiming.close()

    # Extracting the desired columns depends on what we have in the view, so 
    # the below code might be sensitive to change in the DB
    variables = al_pch_events
    variables.to_csv(variables_csv)
    logging.info(variables.cov())
    return variables 

if __name__ == "__main__":
    # I have some minimal tests of each function we can run to ensure validity.

    # Test db_connect()
    mysql_cn = db_connect()

    # Test get_games()
    gl = get_games(mysql_cn) # Use defaults to select the Anaheim games subset
    if type(gl)!=type([]) or type(gl[0])!=type('This'):
        print "Failed get_games() test."
    gl = gl[:2] # Make our search space substantially smaller for subsequent tests' speed.
   
    # Test get_data
    data = get_data(mysql_cn, games_list=gl)
    if type(data)!=pd.DataFrame:
        print "Failed get_data() test."

    # Test get_main_pitch_changes() 
    pchanges = get_main_pitch_changes(data,games_list=gl)
    if pchanges==[] or type(pchanges)!=type([]) or type(pchanges[0])!=type( (0,'str',0) ):
        print "Failed get_main_pitch_changes() test."
    pchanges = get_main_pitch_changes(data)
    if pchanges==[] or type(pchanges)!=type([]) or type(pchanges[0])!=type( (0,'str',0) ):
        print "Failed get_main_pitch_changes() test."

    # Test get_pchange_nback()
    pchanges_n = get_pchanges_nback(data, games_list=gl,nback=3)
    if pchanges_n==[] or type(pchanges_n)!=type([]) or type(pchanges_n[0])!=type( (0,'str',0) ):
        print "Failed get_pchange_nback() test."

    # Test events_at_eventid()
    evs = events_at_eventid(pchanges_n, data)
    if type(evs)!=pd.DataFrame:
        print "Failed events_at_eventid()."

    # Test pchangesAL
    fnamecsv = './tst_ANA_pchanges.csv'
    alpch =  pchangesAL(data,fnamecsv)
    if alpch==[] or type(alpch)!=type([]) or type(alpch[0])!=type( (0,'str',0) ) or not os.path.isfile(fnamecsv):
        print "Failed pchangesAL() test."

    # Test statsAL
    fnamecsv = './tst_ANA_pchanges.csv'
    varcsv = './tst_ANA_vars.csv'
    pvars =  statsFromAL(data,fnamecsv,variables_csv=varcsv)
    if type(pvars)!=pd.DataFrame or not os.path.isfile(varcsv):
        print "Failed statsFromAL() test."
    os.system('rm %s' % varcsv)
    os.system('rm %s' % fnamecsv)

    dataframe = pd.read_sql('select * from myevents', mysql_cn)
    plot_events(dataframe)
    #fnamecsv = './AL_6pchanges.csv'
    #varcsv = './AL_6pchange_vars.csv'
    #myev_6pchanges = pchangesAL(dataframe,fnamecsv,nback=6)
    #variables_6bk = statsFromAL(dataframe,fnamecsv,variables_csv=varcsv)

    # Can READ PANDAS DF FROM A CSV LIKE SO:
    #new_df = pd.read_sql('./tmp_variables.csv')
    #mysql_cn.close()   
