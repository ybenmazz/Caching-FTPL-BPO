"""
main
====

This script serves as the entry point for running experiments on a variety of caching policies under different request patterns. It orchestrates the following steps:

1. Parse user‑defined parameters either from the command line or via a graphical interface using the Gooey library.  These parameters include
   problem dimensions (number of items, cache size, time horizon), request distribution settings, which caching policies to evaluate, and plot customisation options.


2. Construct a request generator according to the chosen request type  (e.g. Zipf distribution, round‑robin, or real trace) and produce the sequence of requests.


3. For each selected caching policy, instantiate the corresponding class from :mod:`utils_Cache_Algos`, run multiple simulations to estimate the average miss ratio and confidence intervals over time,
   and record the execution time.

4. Optionally load pre‑computed results from a pickle file to avoid re‑running the experiments.


5. Display summary statistics for each policy and plot the average miss ratios with confidence bands using :class:`utils_Plotting_Class.MultiCurvePlotter`.

To run this script, use:

    python main_.py

When executed, a Gooey GUI will appear allowing you to configure the experiment parameters.  Alternatively, if you prefer a pure command‑line
interface, remove the ``@Gooey`` decorator in ``utils_Input_Acquisition.create_input_dictionary``.
"""

import numpy as np

import time
from utils_Cache_Algos import *
from utils_Request_Process import *
from utils_Input_Acquisition import *
from utils_Plotting_Class import *

import pickle

if __name__ == '__main__':
    print(0)

    input_dict = create_input_dictionary()
    UseFile = input_dict['read_file']
    nameFileRead = input_dict['file_name']
    nameImage = input_dict['img_name']

    n = input_dict['n_items']
    c = input_dict['cache_capacity']
    T = input_dict['time_horizon']
    p = input_dict['BPO_probability']
    p2 = 1.0
    b = input_dict['batch_size']
    MSamples = input_dict['n_samples']

    # Request Parameters
    nameRequest = input_dict['type_requests']

    a = input_dict["skew_zipf"] # Zipf

    n_segments = input_dict['n_segments_Zipf_Swap'] #Zipf_Swap
    swap_size = input_dict['swap_size_Zipf_Swap']   #Zipf_Swap

    mass_popular = input_dict['mass_popular_TwoGroups'] #TwoGroups
    n_popular = input_dict['n_popular_TwoGroups']  #TwoGroups



    seed_requests = input_dict['seed_requests']


    # Policy Parameters
    policiesList = input_dict['Policies']
    seed_policy = input_dict['seed_policy']
    policiesCI = list({"L_NFPL", "D_NFPL", "S_NFPL"} & set(policiesList))


    # Plotting Parameters
    nPlotPoints = input_dict['n_plot_points']
    step = max(1, int(np.ceil(T / nPlotPoints)))
    fontSize = input_dict['fontSize']
    markerSize = input_dict['markerSize']

    showLegendInside = bool(input_dict['show_legend_inside'])

    # Requests type creation
    argReq_RR, argReq_Zipf = {'n': n, 'T': T}, {'n': n, 'T': T, 'a': a, 'seed': seed_requests}

    argReq_TwoGroups = {'n': n, 'T': T, 'mass_popular': mass_popular, 'n_popular': n_popular, 'seed': seed_requests}

    argReq_ZipfSwap = {'n': n, 'T': T, 'a':a, 'n_segments': n_segments,  'swap_size': swap_size, 'seed': seed_requests}


    mappingReqArg = {"RoundRobin": argReq_RR, "Zipf": argReq_Zipf, "Zipf_RR": argReq_Zipf, 'Zipf_Swap': argReq_ZipfSwap,
                     "TwoGroups": argReq_TwoGroups, "TwoGroups_RR": argReq_TwoGroups}

    objProcess: Requests = globals()[nameRequest](**mappingReqArg[nameRequest])
    rProcess: np.ndarray = objProcess.genRequests()

    n, T = objProcess.n, objProcess.T
    print(f"total requests {n, T}")

    # Caching policies Creation
    arg_class1, arg_class2, arg_class3 = ({'n': n, 'c': c, 'p': p}, {'n': n, 'c': c, 'p': p, 'q': p2},
                                          {'n': n, 'c': c, 'p': p, 'q': p2, 'b': b})

    mappingClassArg = {"LFU": arg_class1, "LRU": arg_class1, "S_NFPL": arg_class2, "L_NFPL": arg_class2,
                       "D_NFPL": arg_class3}
    resultsAvg = {}
    resultsCI = {}
    executionTime = {}
    if not UseFile:

        for alg in policiesList:
            start = time.time()
            obj: CacheAlgorithm = globals()[alg](**mappingClassArg[alg])
            results: np.ndarray = obj.finalCost(step, MSamples, rProcess, seed_policy)

            resultsAvg[alg] = results[1]
            resultsCI[alg] = [results[0], results[2]]
            end = time.time()
            executionTime[alg] = (end - start) / MSamples

        costOpt: np.ndarray = OPT(n, c).finalCost(step, 1, rProcess, seed_policy)
        resultsAvg["OPT"] = costOpt

        file = open(f'{nameFileRead}', 'wb')
        dic = {'Avg': resultsAvg, 'CI': resultsCI, "Time": executionTime}
        pickle.dump(dic, file)
    else:
        file = open(f'{nameFileRead}', 'rb')
        obj: dict = pickle.load(file)
        resultsAvg, resultsCI = obj['Avg'], obj['CI']
        executionTime = obj['Time']
        costOpt = resultsAvg["OPT"]

    for policy in policiesList:
        var = max(resultsCI[policy][1][-1] - resultsAvg[policy][-1],
                  - resultsCI[policy][0][-1] + resultsAvg[policy][-1])

        print(policy, resultsAvg[policy][-1], "variance", "{:e}".format(var), "execution",
              "{:e}".format(executionTime[policy]))
        print()

    print("costOpt", "{:e}".format(costOpt[-1]))

    mappingColMarkLab = {
        "S_NFPL": ["Red", '<', "S-NFPL", "solid"],
        "L_NFPL": ["Purple", '>', "L-NFPL", "dotted"],
        "D_NFPL": ["Blue", 'v', f"D-NFPL", "dashed"],
        "LFU": ["Brown", '^', "LFU", "solid"],
        "LRU": ["magenta", '.', "LRU", "dotted"],
        "OPT": ["Green", "s", "OPT", "solid"]
    }

    x_label, y_label = 'Number of requests', 'Average miss ratio'
    lineWidth = 1
    idCurves = policiesList + ["OPT"]
    idCurvesVar = list(policiesCI)
    offset = 0
    obj: MultiCurvePlotter = MultiCurvePlotter(idCurves, idCurvesVar, mappingColMarkLab, resultsAvg, resultsCI,
                                               x_label,
                                               y_label,
                                               fontSize,
                                               markerSize,
                                               lineWidth,
                                               offset)

    obj.save_legend_only("Test/legend_only_L.pdf")
    obj.plotFunction(step, nameImage, show_legend=showLegendInside)
