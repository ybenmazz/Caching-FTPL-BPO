"""
utils_Cache_Algos
===================

This module contains a collection of classes and helper functions that implement
several caching algorithms used to study the behaviour of online learning for
caching.  The algorithms are designed to respond to a stream of requests for
items.  Each policy decides which items to keep in the cache and which to
evict when a new item arrives.  The key idea is to track hits (when the
requested item is already in the cache) and misses (when it is not), and to
update internal data structures accordingly.  The policies provided here are
useful for simulating different caching strategies and analysing their
performance.

Classes
-------
CacheAlgorithm
    An abstract base class that defines the common interface for all caching
    policies.  It keeps track of the current cache contents, whether each
    possible item is cached, and measures of time and observability.

LRU
    Implements the Least Recently Used policy.  Items that have not been
    accessed recently are evicted first.

LFU
    Implements the Least Frequently Used policy.  Items with the lowest
    access frequency are evicted first.

S_NFPL, L_NFPL, D_NFPL
    Variants of NFPL.

OPT
    The optimal static caching policy with knowledge of future requests.

Functions
---------
confidenceIntervals
    Compute confidence intervals around empirical mean curves obtained from
    multiple runs of a policy.  Two methods are provided: one based on the
    Student's t-distribution and one based on quantiles.

TopCEff
    Efficiently update the set of cached items by replacing the item with
    lowest metric value if a new item has a higher metric.

"""

import numpy as np
import scipy


class CacheAlgorithm:

    def __init__(self, n: int, c: int, p: float):

        self.capacity = c
        self.n_items = n
        self.p = p

        self.timeStep = 0
        self.contentBinary, self.content = None, None
        self.rng = None

    def handleMiss(self, r_item: int):
        pass

    def handleHit(self, r_item: int):
        pass

    def singleRunCost(self, seed: int, interval: int, requests: np.ndarray):
        self.reset(seed)
        T = requests.shape[0]
        n_points = T // interval
        """
        The parameter "interval" determines the length of the cost vector. 
        """
        if T % interval != 0:
            n_points += 1
        mask = self.rng.choice(a=[True, False],
                               p=[self.p, 1 - self.p],
                               size=T)
        """
        The vector "mask" models the partial observability of the requests. 
        """

        costs = np.zeros(n_points)
        normalization = np.zeros(n_points)
        cost = 0
        for t in range(T):
            self.timeStep = t + 1
            r_item: int = int(requests[t])
            observed: bool = bool(mask[t])
            if self.contentBinary[r_item] and observed:
                self.handleHit(r_item)
            elif not self.contentBinary[r_item]:
                cost += 1
                if observed:
                    self.handleMiss(r_item)

            if (t + 1) % interval == 0:
                costs[(t + 1) // interval - 1] = cost
                normalization[(t + 1) // interval - 1] = t + 1
        if T % interval != 0:
            costs[n_points - 1] = cost
            normalization[n_points - 1] = T

        return costs / normalization

    def reset(self, seed):
        self.timeStep = 0
        rng = np.random.default_rng(seed)
        """
        Selects C files uniformly at random.
        """
        self.content = rng.choice(np.arange(self.n_items), size=self.capacity, replace=False)
        self.contentBinary = np.zeros(self.n_items, dtype=bool)
        self.contentBinary[self.content] = True
        """
        The top C items can be computed directly via seed. 
        """
        self.rng = np.random.default_rng(seed)
        """
        Ensures seed is used to simulate the partial observability
        of the requests. 
        """

    def finalCost(self, interval: int, n_samples: int, requests: np.ndarray, seed: int):
        T = requests.shape[0]
        n_points = T // interval
        if T % interval != 0:
            n_points += 1
        costsMatrix = np.zeros((n_samples, n_points))

        for i in range(n_samples):
            costsMatrix[i] = self.singleRunCost(seed=i + seed,
                                                interval=interval,
                                                requests=requests)

        return confidenceIntervals(costsMatrix, flagQuantile=False, alpha=0.05)


class LRU(CacheAlgorithm):
    """
    the attribute content refers to an ordered list that keeps track of the C most recently used items.
    """

    def handleHit(self, r_item: int):
        index_item = np.where(self.content == r_item)[0][0]

        if index_item > 0:  # No need to do anything if it's already the most recent
            x = np.delete(self.content, index_item)
            self.content = np.insert(x, 0, r_item)
            # Move the item to the front (most recently used position)

    def handleMiss(self, r_item: int):
        evicted_item = self.content[-1]
        self.content = np.roll(self.content, 1)
        self.content[0] = r_item
        self.contentBinary[evicted_item] = 0
        self.contentBinary[r_item] = 1


class LFU(CacheAlgorithm):
    """
    The attribute content represents a dictionary that associates for each cached item its corresponding count.
    """

    def __init__(self, n: int, c: int, p: float):
        super().__init__(n, c, p)
        self.metric_decision: np.ndarray = None

    def reset(self, seed):
        super().reset(seed)
        keys = self.content
        self.content: dict = {}
        for item in keys:
            self.content[item] = 0
        self.metric_decision = np.zeros(self.n_items)

    def UpdateMetricDecision(self, r_item):
        self.metric_decision[r_item] += 1
        return True

    def handleHit(self, r_item):
        self.UpdateMetricDecision(r_item)

    @staticmethod
    def TopCEffDic(r_item: int, val_request: int, dict_Counts: dict,
                   storedContentBinary: np.ndarray):
        min_item = min(dict_Counts, key=dict_Counts.get)
        min_value = dict_Counts[min_item]

        if val_request >= min_value:
            dict_Counts.pop(min_item)
            dict_Counts[r_item] = val_request
            storedContentBinary[min_item] = False
            storedContentBinary[r_item] = True

    def handleMiss(self, r_item):

        if self.UpdateMetricDecision(r_item):
            self.TopCEffDic(r_item, self.metric_decision[r_item], self.content, self.contentBinary)


class S_NFPL(LFU):
    def __init__(self, n: int, c: int, p: float, q: float, distribution="Uniform"):
        super().__init__(n, c, p)
        self.distribution = distribution
        self.q = q

        self.eta: float = None
        self.gamma: np.ndarray = None
        # self.frequencyTable = None
        self.content, self.contentBinary = None, None

    def setEta(self, T: int):
        if self.distribution == "Uniform":
            self.eta = np.sqrt(T / (2 * self.capacity)) * self.p * self.q

        if self.distribution == "Gaussian":
            self.eta = np.sqrt(T / self.capacity) * (4 * np.pi * np.log(self.n_items)) ** (-1 / 4)

    def reset(self, seed):
        self.timeStep = 0

        self.rng = np.random.default_rng(seed)
        self.gamma: np.ndarray = self.genNoise()
        # self.frequencyTable = np.zeros(self.n_items)
        self.metric_decision = self.gamma
        self.content, self.contentBinary = self.TopC(self.metric_decision, self.capacity)

        self.rng = np.random.default_rng(seed)

    def finalCost(self, interval: int, n_samples: int, requests: np.ndarray, seed: int):
        T = requests.shape[0]
        self.setEta(T)
        return super().finalCost(interval, n_samples, requests, seed)

    def genNoise(self):
        if self.distribution == "Uniform":
            return self.rng.uniform(0, self.eta, size=self.n_items)
        if self.distribution == "Gaussian":
            return self.eta * self.rng.normal(size=self.n_items)

    @staticmethod
    def TopC(metricVector: np.ndarray, c: int):
        u = np.argsort(metricVector)
        u = np.flip(u)
        content = u[:c]
        contentBinary = np.zeros(metricVector.shape[0], dtype=bool)
        contentBinary[content] = 1

        keys = content
        content: dict = {}
        for item in keys:
            content[item] = 0
        return content, contentBinary

    def UpdateMetricDecision(self, r_item):
        beta = np.random.binomial(n=1, p=self.q)
        if beta == 1:
            self.metric_decision[r_item] += 1
            return True
        """
        When the weights for each file do not change, there is no need to Find TOP C.
        """
        return False


class L_NFPL(S_NFPL):

    def __init__(self, n: int, c: int, p: float, q: float):
        super().__init__(n, c, p, q)
        self.frequency_table: np.ndarray = None

    def reset(self, seed):
        super().reset(seed)
        self.frequency_table = np.zeros(self.n_items)

    def UpdateMetricDecision(self, r_item):
        beta = np.random.binomial(n=1, p=self.q)
        if beta == 1:
            self.frequency_table[r_item] += 1
        a = self.frequency_table[r_item]
        delta = (np.ceil((a - self.gamma[r_item]) / self.eta) -
                 np.ceil((a - 1 - self.gamma[r_item]) / self.eta))
        if delta >= 1:
            self.metric_decision[r_item] += (self.eta * delta)
            return True
        return False


class D_NFPL(S_NFPL):
    def __init__(self, n: int, c: int, p: float, q: float, b: int, distribution="Uniform"):
        super().__init__(n, c, p, q, distribution)
        self.b = b
        self.frequency_table = None

    def reset(self, seed):
        super().reset(seed)
        self.frequency_table = np.zeros(self.n_items)

    def UpdateMetricDecision(self, r_item):

        beta = self.rng.binomial(n=1, p=self.q)
        if beta == 1:
            self.frequency_table[r_item] += 1
        if self.timeStep % self.b == 0:
            self.gamma = self.genNoise()
            self.metric_decision = self.frequency_table + self.gamma
            self.content, self.contentBinary = self.TopC(self.metric_decision, self.capacity)
            return True
        return False

    def handleMiss(self, r_item):
        if self.UpdateMetricDecision(r_item):
            self.content, self.contentBinary = self.TopC(self.metric_decision, self.capacity)

            """
            The only difference is substituting the method "TopCEff" by "TopC". Here,
            it is necessary to sort the vector. 
            """


class D_NFPL_G(D_NFPL):
    def __init__(self, n: int, c: int, p: float, q: float, b: int):
        super().__init__(n, c, p, q, b, distribution="Gaussian")


class OPT(CacheAlgorithm):
    def __init__(self, n: int, c: int):
        super().__init__(n, c, 1)

    def finalCost(self, interval: int, n_samples: int, requests: np.ndarray, seed: int):
        T = requests.shape[0]
        n_points = T // interval
        if T % interval != 0:
            n_points += 1

        finalFrequencies = np.bincount(requests, minlength=self.n_items)
        finalFrequencies = np.sort(finalFrequencies)
        optCost = np.sum(finalFrequencies[:self.n_items - self.capacity]) / T

        return np.ones(n_points) * optCost


def confidenceIntervals(Matrix: np.ndarray, alpha: float = 0.2, flagQuantile: bool = True):
    muEmpirical = np.mean(Matrix, axis=0)
    # Size (T,)
    nSamples = Matrix.shape[0]
    # Matrix (nSamples, T)
    T = Matrix.shape[1]
    if not flagQuantile:

        sigma = np.std(Matrix, axis=0)

        quantileSt = scipy.stats.t.interval(1 - alpha, nSamples - 1, loc=0, scale=1)[1]
        vPlus = muEmpirical + quantileSt * sigma / np.sqrt(nSamples)
        vMinus = muEmpirical - quantileSt * sigma / np.sqrt(nSamples)
        return vMinus, muEmpirical, vPlus
    else:
        """
        Matrix is of size (n_samples, n_points)
        """
        sortedMatrix = np.sort(Matrix, axis=0)
        n_samples = sortedMatrix.shape[0]
        first_Index = int(np.floor(alpha * n_samples))
        second_Index = int(np.floor((1 - alpha) * n_samples))
        return sortedMatrix[:, first_Index], muEmpirical, sortedMatrix[:, second_Index]


def TopCEff(metricVector: np.ndarray, r_item: int, storedContent: np.ndarray,
            storedContentBinary: np.ndarray):
    u: int = np.argmin(metricVector[storedContent])

    fileRankC = int(storedContent[u])

    if metricVector[fileRankC] <= metricVector[r_item]:
        storedContent[u] = r_item
        storedContentBinary[fileRankC] = 0
        storedContentBinary[r_item] = 1
