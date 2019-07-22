'''Tests for contents of scoring/distance.py

@author: Tomasz Konopka
'''

import numpy as np
import unittest
from scoring.distance import vec_norm
from scoring.distance import cosine_distance


class DistanceTests(unittest.TestCase):
    
    def setUp(self):
        """For setup, ensure db does not exist."""
        
        self.data = np.array(range(30*24))
        self.data.shape = (30,24)
        self.x = self.data[:, 1]        
        self.y = self.data[:, 2]
        self.xlist = self.x.tolist()
        self.ylist = self.y.tolist()     

    def test_cosine_distance(self):
        """manual implementation of distance with numba."""

        xnorm = vec_norm(self.x)
        ynorm = vec_norm(self.y)
        self.assertGreater(xnorm, 0)
        self.assertGreater(ynorm, 0)
        distance = cosine_distance(self.x, self.y, xnorm, ynorm)
        self.assertGreater(distance, 0.0)
        self.assertLess(distance, 1)

