"""
Class describing a single db table.
"""

import os
from .db import get_conn


# ##################################################################
#

class DBTable:
    """
    Class designed to be subclassed.
    
    Subclasses should implement a function to transfer data into 
    the self.data list.        
    
    This class opens/closes a connection at each operation.
    This should make it possible to use this class with multiprocessing.     
    """
    
    # insertN determines the number of rows that are sent at once.
    # (using >1000 can give sqlite3 error due to expression tree too-large)    
    insertN = 768

    # name of table in db
    tabname = ""
        
    # field names for the table in an array, split by type
    textfields = []
    realfields = []

    def __init__(self, dbfile):
        """Set up a connection and cursor for db operations.
        
        Args:
            dbfile:    filename for the database        
        """
        
        # perform checks that subclassing was performed correctly
        if self.tabname == "":
            raise Exception("table name cannot be blank")
        if len(self.textfields)+len(self.realfields)==0:
            raise Exception("table must contain at least one column")
                        
        self.dbfile = dbfile
        if not os.path.exists(dbfile):
            raise Exception("db does not exist on disk: "+str(dbfile))
               
        # record all field names (locally and in an available set)
        allfields = self.fieldnames()
        self.fieldset = set(allfields)
        
        # prep insert command
        temp = "(" + ", ".join(allfields) + ") VALUES "
        temp += "(" + ", ".join(["?"]*len(allfields))+" )"
        self.sqlinsert = "INSERT INTO " + self.tabname + temp

        # object cache
        self.data = []

    def save(self, force=True):
        """Send contents of self.data to the database table."""
                
        # perhaps delay saving operation
        if not force and len(self.data) < self.insertN:
            return            
        if len(self.data) == 0:
            return
                        
        with get_conn(self.dbfile) as conn:
            c = conn.cursor()
            # execute the insert in batches of insertN
            for x in range(0, len(self.data), self.insertN):                            
                xdata = self.data[x:x+self.insertN]
                c.executemany(self.sqlinsert, xdata)
                                                                                
        self.clear()

    def clear(self):
        """Remove everything from the current data store (not from db)"""
        self.data = []

    def count_rows(self):
        """Count rows in table."""
                              
        sql = "SELECT COUNT(*) FROM " + self.tabname
        with get_conn(self.dbfile) as conn:    
            result = conn.cursor().execute(sql).fetchone()[0]            
        return result

    def unique(self, field):
        """get a set of unique values in a given field."""
        
        # this is an unsafe sql query
        # but I couldn't get SELECT ? FROM self.tabname to work
        sql = "SELECT DISTINCT "+field+" FROM "+self.tabname                
        result = []
        with get_conn(self.dbfile) as conn:
            cur = conn.cursor()                            
            cur.execute(sql)
            for row in cur:                                    
                result.append(row[field])        
        return result

    def empty(self):
        """Remove all exisitng rows from table."""
        
        self.clear()
        sql = "DELETE FROM "+self.tabname        
        with get_conn(self.dbfile) as conn:
            conn.cursor().execute(sql)

    def update(self, data, where):
        """Update records in the table
        
        Arguments:
            data     dict with new values
            where    dict with WHERE clauses
            
        Returns:
            Nothing, but will update the db. Changes will affect
            as many rows as the where condition hits.
        """
        
        xdata = []
        set_parts = []
        where_parts = []
        for k,v in data.items():
            if k not in self.fieldset:
                raise Exception("invalid field name: "+k)
            set_parts.append(k+"=?")
            xdata.append(v)        
        if len(where) > 0:
            for k,v in where.items():
                if k not in self.fieldset:
                    raise Exception("invalid field name: "+k)
                where_parts.append(k+"=?")                
                xdata.append(v)
        
        sql = "UPDATE " + self.tabname + " SET "
        sql += ", ".join(set_parts)
        if len(where) > 0:
            sql +=  " WHERE "
            sql += " AND ".join(where_parts)
                    
        with get_conn(self.dbfile) as conn:
            cur = conn.cursor()
            cur.execute(sql, xdata)

    def delete(self, field, values):
        """remove rows from the db table based on values in one field
        
        Arguments:
            field     string, name of DB field
            values    list of values for the WHERE clause 
        """
        
        if field not in self.fieldset:
            raise Exception("invalid field name: "+field)
        
        sql = "DELETE FROM " + self.tabname + " WHERE "        
              
        with get_conn(self.dbfile) as conn:
            c = conn.cursor()            
            # execute the delete in batches
            for x in range(0, len(values), self.insertN):                            
                xdata = values[x:x+self.insertN]
                where = " OR ".join([field+"=?"]*len(xdata))
                c.execute(sql+where, xdata)

    def fieldnames(self):      
        """Get a list with all field names for this table."""
        
        result = []
        result.extend(self.textfields)
        result.extend(self.realfields)
        return result    

    def content(self):
        """Get a string with all the table content. Can be big!"""
        
        allfields = self.fieldnames()
        result = ["\t".join(allfields)]

        # create select statement
        comma_fields = ", ".join(allfields)
        sql = "SELECT " + comma_fields + " FROM " + self.tabname
        
        # execute query and yield one row at a time
        with get_conn(self.dbfile) as conn:
            cur = conn.cursor()
            cur.execute(sql)                
            for row in cur:                
                temp = [str(row[_]) for _ in allfields]
                result.append("\t".join(temp))
                
        return "\n".join(result)


# ###########################################################################
#

class DBTableExample(DBTable):
    """An example subclass of DBTable."""
    
    tabname = "example"
    textfields = ["key"]
    realfields = ["value"]
    
    def add(self, k, v):
        self.data.append([k, v])

