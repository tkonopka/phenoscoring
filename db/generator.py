"""
Class describing a generator iterating over a single db table.

This provides a shortcut interface to add simple contrainst on the
sql SELECT statement.
"""

from .db import get_conn
from .table import DBTable


class DBGenerator:
    """Class that retrieves rows from a table."""
    
    def __init__(self, table, logic="AND", where=dict(), fieldnames=None):
        """set up this generator with a DBTable object

        :param table: DBTable object
        :param logic: string, use AND or OR
        :param where: dictionary with exact constraints
        :param fieldnames: iterable with fields to extract in output
        """

        if not issubclass(type(table), DBTable):
            raise Exception("table must be of class DBTable")
        
        self.table = table        
        self.logic = " " + logic + " "
        self.where = where
        self.fieldnames = fieldnames if fieldnames else table.fieldnames()
        
        # check that explicit fields are present in the database table model
        for x in self.where:
            if x not in table.text_fields and x not in table.real_fields:
                raise Exception("invalid field name: "+str(x))
        for x in self.fieldnames:
            if x not in table.fieldnames():
                raise Exception("invalid field name: "+str(x))

    def next(self):
        """Retrieve all the data from the table, one row at a time."""

        fields = ", ".join(self.fieldnames)
        sql = "SELECT " + fields + " FROM " + self.table.name
                
        where_sql = []
        where_data = []
        if len(self.where) > 0:
            for k, v in self.where.items():
                where_sql.append(k + "=?")
                where_data.append(v)            
            sql += " WHERE " + self.logic.join(where_sql)

        with get_conn(self.table.dbfile) as conn:
            cur = conn.cursor()            
            cur.execute(sql, where_data)                
            for row in cur:                
                yield row  

