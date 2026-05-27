"""
utils_Request_Process
=====================

This module defines several classes and helper functions for generating
sequences of requests that simulate different access patterns in a caching
system.  The base class :class:`Requests` encapsulates common attributes
(number of distinct items, length of the request sequence, and random seed).

Subclasses implement synthetic request models, including uniform random
requests, Zipf-distributed requests, round-robin patterns, two-group popularity
models, and piecewise-shifting Zipf requests.

Classes
-------
Requests
    Base class that defines the API for generating a request sequence.

RoundRobin
    Deterministic request pattern cycling through all items in order.

Stationary
    Random requests drawn in an i.i.d. fashion from a fixed probability vector.

Zipf
    Stationary requests with a Zipf popularity distribution.

TwoGroups
    Stationary requests where a subset of items forms a popular group.

General_RR
    A round‑robin sequence where the frequency of each item follows a
    specified probability vector.

Zipf_RR, TwoGroups_RR
    Convenience wrappers for :class:`General_RR` with Zipf and two‑groups
    distributions respectively.

Zipf_Swap
    The distribution within each segment is Zipf(a), but the identity of the
    most popular items drifts in blocks. This models non-stationary demand
    with piecewise-constant shifts.


Functions
---------
probabilities_vector_Zipf
    Compute a Zipf popularity vector of length ``n_items`` with exponent
    ``alpha``.

probabilities_vector_2Groups
    Generate a popularity vector consisting of two groups: a top group of
    size ``k`` with total probability ``alpha``, and a second group with the
    remaining probability mass.
"""

import pickle
from typing import Tuple

import numpy as np
import pandas as pd


class Requests:
    def __init__(self, n: int, T: int, seed: int = 0):
        self.n = n
        self.T = T
        self.seed = seed

    def genRequests(self):
        return np.zeros(self.T, dtype=int)


class RoundRobin(Requests):

    def genRequests(self):
        co = self.T // self.n
        re = self.T % self.n
        return np.concatenate((np.tile(np.arange(0, self.n), co), np.arange(0, re)))


class Stationary(Requests):
    def __init__(self, n, T, seed=0):
        super().__init__(n, T, seed)
        self.p_vector = np.ones(n) / n

    def set_p_vector(self,p_vector):
        self.p_vector= p_vector

    def genRequests(self):
        rng = np.random.default_rng(self.seed)
        population = np.arange(0, self.n, dtype=np.int32)

        return rng.choice(a=population,
                          size=self.T,
                          p=self.p_vector)


class TwoGroups(Stationary):
    def __init__(self, n: int, T: int, mass_popular: float, n_popular: int, seed=0):
        super().__init__(n, T, seed)
        self.mass_popular = mass_popular
        self.n_popular = n_popular
        self.p_vector = probabilities_vector_2Groups(n, mass_popular, n_popular)

class Zipf(Stationary):
    def __init__(self, n: int, T: int, a: float, seed=0):
        super().__init__(n, T, seed)
        self.a = a
        self.p_vector = probabilities_vector_Zipf(n_items=self.n,
                                                  alpha=self.a)



class Zipf_Swap(Zipf):
    """
        Generates a length-T request sequence over n items where the popularity profile
        changes abruptly a fixed number of times while remaining Zipf-like.

        Mechanism
        ---------
        1) Start from a Zipf(a) probability vector over ranks 0..n-1.
        2) Split the horizon T into `n_swaps` consecutive segments
           (the last one absorbs any remainder if T % n_swaps != 0).
        3) For segment k = 0,1,...:
           - Cyclically rotate the Zipf probability vector by k * swap_size positions
             (mod n). This “slides” the hot set through the catalogue.
           - Sample that segment i.i.d. from the rotated vector.
        4) Concatenate all segments to obtain the full request trace.
    """
    def __init__(self, n: int, T: int, a: float, n_segments: int =2, swap_size: int = 5, seed: int=0 ):
        super().__init__(n, T, a,seed)
        self.swap_size= swap_size
        self.n_segments= n_segments

    def genRequests(self):
        T_k = self.T//self.n_segments
        r = self.T%self.n_segments
        p_vector = probabilities_vector_Zipf(self.n,self.a)
        req_process = [0] *self.n_segments
        for j in range(self.n_segments):
            size_segment = T_k
            if j==self.n_segments -1:
                size_segment= T_k + r
            obj = Stationary(self.n, size_segment, self.seed+j)
            obj.set_p_vector(p_vector)
            req_process[j] =obj.genRequests()
            p_vector = np.roll(p_vector, self.swap_size)

        return np.concatenate(req_process)





class General_RR(Stationary):

    def genRequests(self):
        res = np.zeros(self.T, dtype=np.int32)
        rng = np.random.default_rng(self.seed)
        occ: np.ndarray = rng.multinomial(self.T, self.p_vector)
        occ = np.flip(np.sort(occ))
        occ = np.concatenate((occ, np.array([0])))
        cursor: int = 0
        s: int = 0
        for i in range(self.n):
            cur_item = self.n - i - 1
            occ_item = occ[cur_item] - s
            if occ_item > 0:
                res[cursor: cursor + occ_item * (cur_item + 1)] = np.tile(np.arange(cur_item, -1, -1), occ_item)
                cursor += occ_item * (cur_item + 1)
                s += occ_item
        return res


class Zipf_RR(General_RR):
    def __init__(self, n, T, a: float, seed=0):
        super().__init__(n, T, seed)
        self.a = a
        self.p_vector = probabilities_vector_Zipf(n, a)



class TwoGroups_RR(General_RR):
    def __init__(self, n: int, T: int, mass_popular: float, n_popular: int, seed=0):
        super().__init__(n, T, seed)
        self.mass_popular = mass_popular
        self.n_popular = n_popular
        self.p_vector = probabilities_vector_2Groups(n, mass_popular, n_popular)







def probabilities_vector_Zipf(n_items, alpha):
    one_to_n = np.arange(start=1,
                         stop=n_items + 1,
                         dtype=float,
                         step=1)

    not_normalized = np.power(np.reciprocal(one_to_n), alpha)
    return not_normalized / np.sum(not_normalized)


def probabilities_vector_2Groups(n_items: int, alpha: float, k: int):
    """
    :param n_items:
    :param alpha:
    :param k:
    :return: p_1 = p_k = alpha / k, p_{k+1} = p_{N} = (1-alpha)/ N
    """
    thres = k * (n_items - k) / (n_items ** 2)
    if alpha <= thres:
        return np.ones(n_items) / n_items

    else:
        a = np.ones(k) * alpha / k
        b = np.ones(n_items - k) * (1 - alpha) / (n_items - k)
        return np.concatenate((a, b))


