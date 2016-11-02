import pandas as pd
import MySQLdb as MySQL

def db_connect():
    """ Connect to the database """
    mysql_cn = MySQL.connect(host='35.160.8.83', port=3306, user='ubuntu', \
                                        passwd='R3tr0sh33t', db='retrosheet')
    return mysql_cn

def get_all_games(mysql_cn, table='events'):
    sql = ('select distinct GAME_ID from %s',table) 
    games_list = pd.read_sql(sql)
    return games_list   

def get_main_pitch_changes(mysql_cn,table='events',games_list=None):
    """
    Compute the 

    """
    pitch_changes = pd.DataFrame(columns=["EVENT_ID","GAME_ID"])
    
    if games_list==None: 
        sql = ('select distinct GAME_ID from %s',table) 
        games_list = pd.read_sql(sql)
 
 
    pitch_changes=[] # store primary pitcher changes as (EVENT_ID,GAME_ID) tuples)

    for g in games_list:
        # First, check for a change for the first team
        sql = ('select EVENT_ID, PIT_ID from %s where BAT_HOME_ID='0' and GAME_ID=%s',table,g)
        pitches_0 = pd.read_sql(sql)
        for i in range(len(pitches_0) - 1): 
            # look for first instance of a change of pitchers 
            if pitches_0['PIT_ID'][i] != pitches_0['PIT_ID'][i+1]
                pitch_changes.append( (pitches_0['EVENT_ID'][i+1], g) )
                print "Found a primary switch: ",str(pitches_0['EVENT_ID'][i+1], g)
                break # Should just break from this inner loop

        # Next, check for a main pitcher change for the opposition 
        sql = ('select EVENT_ID, PIT_ID from %s where BAT_HOME_ID='1' and GAME_ID=%s',table,g)
        pitches_1 = pd.read_sql(sql)
        for i in range(len(pitches_1) - 1): 
            # look for first instance of a change of pitchers 
            if pitches_1[PIT_ID][i] != pitches_1[PIT_ID][i+1]
                pitch_changes.append( (pitches_1['EVENT_ID'][i+1], g) )
                print "Found a primary switch: ",str(pitches_1['EVENT_ID'][i+1], g)
                break # Should just break from this inner loop
    
    return pitch_changes 


if __name__ == "__main__":
    mysql_cn = MySQL.connect(host='35.160.8.83', port=3306, user='ubuntu', passwd='R3tr0sh33t', db='retrosheet')

    dataframe = pd.read_sql('select * from myevents', mysql_cn)

    mysql_cn.close()

    print(dataframe)
    
