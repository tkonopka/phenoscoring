"""A simple logger that prints messages, or not if set to quiet

@author: Tomasz Konopka
"""

from datetime import datetime


## ##################################################################
## 


def time():
    """Return a time string"""
    
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class SimpleLogger():
    """A simple logger class.""" 
    
    
    def __init__(self, verbose=True, prefix ="_time_"):
        self.verbose = verbose
        self.debugging = False
        self.indent = 2
        self.prefix_type = prefix

    
    def prefix(self):
        result = self.prefix_type
        if self.prefix_type == "_time_":
            result = time()
        return "["+ result + "] "
    
    
    def log(self, msg, indent=0):
        """Print a log message with a date and custom indentation."""    
        
        if not self.verbose:
            return
        
        print(self.prefix() + (" "*indent) + msg, flush=True)


    def msg1(self, msg):
        """Print a primary message."""    
                
        self.log(msg, 0)
    

    def msg2(self, msg):
        """Print a secondary message."""    
        
        self.log(msg, self.indent)
    
    
    def msg3(self, msg):
        """Print a tertiary message."""    
        
        self.log(msg, 2*self.indent)
    
    def debug(self, msg):
        """Print a message for debugging (depends on statsus of self.debug)"""
        
        if not self.debugging:
            return        
        print(self.prefix() + " DEBUG: " + msg, flush=True)

