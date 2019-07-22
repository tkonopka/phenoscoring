'''Tests for contents of tools/timing.py

@author: Tomasz Konopka
'''

import unittest
from tools.timing import time_function_2, time_function_1, time_function_0


class TimingTests(unittest.TestCase):
    """Test cases for function check_file."""
    
        
    def test_measure_function_time_2(self):
        """measure a two-argument function."""
                
        def f2(a, b):
            return a+b
        
        self.assertGreater(time_function_2(2,3, f2, replicate=10), 0)


    def test_measure_function_time_1(self):
        """measure a one-argument function."""

        def f1(a):
            return a+1

        self.assertGreater(time_function_1(2, f1, replicate=10), 0)

    def test_measure_function_time_0(self):
        """measure a zero-argument function"""
                
        def f0():
            return 0
        
        self.assertGreater(time_function_0(f0, replicate=10), 0)    

