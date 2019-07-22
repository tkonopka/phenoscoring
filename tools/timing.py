"""Helper functions for timing performance

@author: Tomasz Konopka
"""

from timeit import default_timer as timer


def time_function_2(a, b, fun, replicate=5000):
    """assess running time for fun(a, b)"""
    
    start = timer()
    for i in range(replicate):
        fun(a, b)    
    end = timer()
    
    return end-start


def time_function_1(a, fun, replicate=5000):
    """assess running time for fun(a, b)"""

    start = timer()
    for i in range(replicate):
        fun(a)
    end = timer()

    return end-start

def time_function_0(fun, replicate=5000):
    """assess running time for fun(a, b)"""
    
    start = timer()
    for i in range(replicate):
        fun()    
    end = timer()
    
    return end-start

