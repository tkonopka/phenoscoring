"""
Computation of distances and neighbors
"""

import numba
from numpy import sqrt as sqrt


@numba.njit()
def vec_norm(a):
    """compute norm of a vector."""
    
    result = 0.0
    for i in range(len(a)):
        result += a[i]*a[i]
    return sqrt(result)


@numba.njit()
def cosine_distance(a, b, anorm, bnorm):
    """compute cosine distance between a and b.
    
    Arguments:
        a      array or list
        b      array or list
        anorm  precomputed norm of a
        bnorm  precomputed norm of b
    
    Returns:
        cosine distance 1 - ab/anorm*bnorm
    """
    
    result = 0.0
    for i in range(len(a)):
        result += a[i]*b[i]
    return 1.0 - (result/(anorm*bnorm))


@numba.njit()
def cosine_distances(v, mat, mat_norms):
    """compute cosine distances between an array and columns in a matrix.
    
    Arguments:
        v          array or list
        mat        matrix
        mat_norms  array or list with matrix column norms
    
    Returns:
        list of cosine distances to each column in the matrix
    """
    
    matlen = mat.shape[1]
    result = [0.0]*matlen
    vnorm = vec_norm(v)
    for i in range(matlen):
        w = mat[:, i]
        wnorm = mat_norms[i]
        result[i] = cosine_distance(v, w, vnorm, wnorm)
    return result


@numba.njit()
def neighbor_average(mat, priors, indexes):
    """compute an average of data in a matrix, weighted by priors."""
    
    # compute normalization factor
    norm = 0.0
    for j in indexes:
        norm += priors[j]
    
    # create vector, initially empty, to mimic a column
    n_features = mat.shape[0]
    result = [0.0] * n_features
    
    # add contents from the matrix
    for j in indexes:
        jprior = priors[j]
        data = mat[:,j]
        for i in range(n_features):
            result[i] += jprior * data[i]
    
    # normalize by the weights
    for i in range(n_features):
        result[i] = result[i] / norm
    
    return result
