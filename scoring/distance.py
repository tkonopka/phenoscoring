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
    """compute cosine distance

    :param a: array or list
    :param b: array or list
    :param anorm: number, precomputed norm of a
    :param bnorm: number, precomputed norm of b
    :return: number, cosine distance between a and b
    """
    
    result = 0.0
    for i in range(len(a)):
        result += a[i]*b[i]
    return 1.0 - (result/(anorm*bnorm))


@numba.njit()
def cosine_distances(v, mat, mat_norms):
    """compute cosine distances between an array and columns in a matrix

    :param v: array or list
    :param mat: matrix
    :param mat_norms: array or list with matrix column norms
    :return: list of cosine distance to each column in the matrix
    """

    mat_cols = mat.shape[1]
    result = [0.0]*mat_cols
    v_norm = vec_norm(v)
    for i in range(mat_cols):
        w = mat[:, i]
        w_norm = mat_norms[i]
        result[i] = cosine_distance(v, w, v_norm, w_norm)
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
    result = [0.0]*n_features
    
    # add contents from the matrix
    for j in indexes:
        jprior = priors[j]
        data = mat[:, j]
        for i in range(n_features):
            result[i] += jprior*data[i]
    
    # normalize by the weights
    for i in range(n_features):
        result[i] = result[i] / norm
    
    return result
