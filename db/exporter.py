"""Generator over a db table to output data into a csv file

@author: Tomasz Konopka
"""

from .db import get_conn
from .table import DBTable


class DBExporter():
    """Class that retrieves rows from a table."""
    
    def __init__(self, table):
        """set up this generator with a DBTable object."""
        
        if not issubclass(type(table), DBTable):
            raise Exception("table must be of class DBTable")
        
        self.table = table
    
    
    def to_tsv(self, filename):
        """Retrieve data and write to an output file.""" 
        
        fieldnames = list(self.table.fieldnames())
        fields = ", ".join(fieldnames)
        sql = "SELECT "+ ", ".join(fieldnames)+ " FROM "+self.table.tabname
        
        with get_conn(self.table.dbfile) as conn, open(filename, "w") as f:
            f.writelines("\t".join(fieldnames)+"\n")
            cur = conn.cursor()
            cur.execute(sql)
            for row in cur:
                temp = [str(row[_]) for _ in fieldnames]
                f.writelines("\t".join(temp)+"\n")

