"""
Class describing a generator iterating over a single db table.
"""

from .db import get_conn
from .table import DBTable


## ##################################################################
## 


class DBGenerator:
    """Class that retrieves rows from a table."""
    
    def __init__(self, table, logic="AND", where=dict(), fieldnames=None):
        """set up this generator with a DBTable object
        
        Arguments:
            table       DBTable object
            where       dictionary with exact constraints.
                        e.g. dict(id="A")
            fieldnames  iterable with fields to extract in output
        """
        
        if not issubclass(type(table), DBTable):
            raise Exception("table must be of class DBTable")
        
        self.table = table        
        self.logic = " "+logic+" "
        self.where = where
        
        if fieldnames is None:
            fieldnames = table.fieldnames()
        self.fieldnames = fieldnames
        
        # check that explicit fields are present in the database table model
        for x in self.where:
            if x not in table.textfields and x not in table.realfields:
                raise Exception("invalid fieldname: "+str(x))
        for x in fieldnames:
            if x not in table.fieldnames():
                raise Exception("invalid fielname: "+str(x))                
    
                    
    def next(self):
        """Retrieve all the data from the table, one row at a time."""
                
        # create select statement
        fields = ", ".join(self.fieldnames)
        sql = "SELECT "+fields+" FROM "+self.table.tabname
                
        where_sql = []
        where_data = []
        if len(self.where)>0:            
            for k,v in self.where.items():
                where_sql.append(k+"=?")
                where_data.append(v)            
            sql += " WHERE "+ self.logic.join(where_sql)
        
        # execute query and yield one row at a time
        with get_conn(self.table.dbfile) as conn:
            cur = conn.cursor()            
            cur.execute(sql, where_data)                
            for row in cur:                
                yield row  

