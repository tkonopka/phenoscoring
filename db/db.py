"""
Commonly used functions for working with an sqlite3 database. 
"""

import os
from sqlite3 import connect, Row


## ##################################################################
## 


def setup_db(filepath, tables=[], reset=False):
    """Create or reset an sqlite DB."""
    
    if os.path.exists(filepath) and not reset:
        return
    
    if os.path.exists(filepath) and reset:
        os.remove(filepath)
        
    ## create table with appropriate columns
    with get_conn(filepath) as conn:
        for onetab in tables:
            make_table(conn, onetab.tabname, 
                       onetab.textfields, onetab.realfields)


def get_conn(dbfile, timeout=5000):
    """Get a connection to the databse"""
        
    conn = connect(dbfile, timeout=timeout)        
    conn.row_factory = Row            
    return conn


def make_table(conn, tabname, textfields, realfields):
    """Create a new table in the DB.
    
    conn - a db connection
    tabname -- name of the table
    textfields, realfields -- lists with the required fields        
    """                

    allfields = []
    for field in textfields:
        allfields.append(str(field)+" TEXT")
    for field in realfields:
        allfields.append(str(field)+" REAL")
        
    sql = "CREATE TABLE " + tabname + " (" + ", ".join(allfields) + ")";
    conn.cursor().execute(sql)
    conn.commit()

