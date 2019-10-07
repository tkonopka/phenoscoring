"""
Executing packets, possibly with a multiprocessing pool.
"""

import multiprocessing as mp


def run(p):
    """execute a run method in an object."""        
    return p.run()


def run_packets(packets, cores):
    """execute an array of packets."""
    
    if len(packets) <= 1 or cores <= 1:
        for packet in packets:
            run(packet)
    else:
        with mp.Pool(cores) as pool:
            pool.map(run, packets)

