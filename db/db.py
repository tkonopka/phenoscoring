"""
Commonly used functions for working with an sqlite3 database. 
"""

import os
from sqlite3 import connect, Row


# ##################################################################
#


def setup_db(filepath, tables=(), reset=False):
    """Create or reset an sqlite DB."""
    
    if os.path.exists(filepath) and not reset:
        return
    
    if os.path.exists(filepath) and reset:
        os.remove(filepath)
        
    # create table with appropriate columns
    with get_conn(filepath) as conn:
        for tab in tables:
            make_table(conn, tab.name,
                       tab.text_fields, tab.real_fields)


def get_conn(dbfile, timeout=5000):
    """Get a connection to the database"""
        
    conn = connect(dbfile, timeout=timeout)        
    conn.row_factory = Row            
    return conn


def make_table(conn, table_name, text_fields, real_fields):
    """create a new table in the db

    :param conn: connection
    :param table_name: string, name for new table
    :param text_fields: list, names for fields of type TEXT
    :param real_fields: list, names for fields of type REAL
    """

    all_fields = []
    for field in text_fields:
        all_fields.append(str(field)+" TEXT")
    for field in real_fields:
        all_fields.append(str(field)+" REAL")
        
    sql = "CREATE TABLE " + table_name + " (" + ", ".join(all_fields) + ")";
    conn.cursor().execute(sql)
    conn.commit()

