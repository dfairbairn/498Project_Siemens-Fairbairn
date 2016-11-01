"""
file: datasets.py
authors: David Fairbairn and Kyle Siemens
date: October 2016

Code for acquiring specific game data from our database.

Right now I've just canniablized some of the code from parse.py for
connecting to the mysql server in case that helps.

***
Reading up on SQL alchemy, it looks like I need to instead be using session 
objects to make queries, so the cannibalized code might be not useful. I need
to read up on what types of classes to create in Python which we pair with the
query objects!
***


"""

import os
import subprocess
import ConfigParser
import threading
import Queue
import sqlalchemy
import csv
import time
import glob
import re
import getopt
import sys

import sqlalchemy.orm.session as s
Session = s.sessionmaker()

def connect(config):   
    try:
        ENGINE = config.get('database', 'engine')
        DATABASE = config.get('database', 'database')

        HOST = None if not config.has_option('database', 'host') else config.get('database', 'host')
        USER = None if not config.has_option('database', 'user') else config.get('database', 'user')
        SCHEMA = None if not config.has_option('database', 'schema') else config.get('database', 'schema')
        PASSWORD = None if not config.has_option('database', 'password') else config.get('database', 'password')
    except ConfigParser.NoOptionError:
        print 'Need to define engine, user, password, host, and database parameters'
        raise SystemExit

    if ENGINE == 'sqlite':
        dbString = ENGINE + ':///%s' % (DATABASE)
    else:
        if USER and PASSWORD:
            dbString = ENGINE + '://%s:%s@%s/%s' % (USER, PASSWORD, HOST, DATABASE)
        elif USER:
            dbString = ENGINE + '://%s@%s/%s' % (USER, HOST, DATABASE)
        else:
            dbString = ENGINE + '://%s/%s' % (HOST, DATABASE)
        
    db = sqlalchemy.create_engine(dbString)
    conn = db.connect()
     
    return conn


if __name__=='__main__':
    # First, test if we can connect using the config.ini file
    config = ConfigParser.ConfigParser()
    config.readfp(open('config.ini'))
    
    try:
        conn = connect(config)
    except Exception, e:
        print('Cannot connect to database: %s' % e)
        raise SystemExit

    sess = s.Session()
    
