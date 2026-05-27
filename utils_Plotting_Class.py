"""
This module defines the :class:`MultiCurvePlotter` class, which provides
utilities for visualising the results of caching experiments.  Each policy
evaluated in the experiment produces a series of average miss ratios over
time along with confidence intervals.  The plotter takes these results and
produces line charts with optional shaded regions representing variance or
confidence intervals.  It also allows saving a standalone legend for
separate inclusion in composite figures.

Typical usage involves instantiating :class:`MultiCurvePlotter` with the
list of policies, mapping of colours/markers/labels/linestyles for each
policy, and dictionaries of average curves and variance bounds (or
confidence intervals).  The :meth:`plotFunction` method then creates and
saves a figure showing all selected policies.
"""

import numpy as np
import matplotlib.pyplot as plt

# from matplotlib.ticker import MaxNLocator, FormatStrFormatter
from matplotlib.ticker import ScalarFormatter


class MultiCurvePlotter:
    def __init__(self, idCurves: list, idCurvesVar: list, mappingResColMarLab: dict, resultsAvg: dict,
                 resultsVar: dict,
                 x_label: str, y_label: str,
                 fontSize: int = 45, markerSize: int = 5, line_width: int = 2, offset: int = 0):
        self.policies = idCurves
        self.policies_fill = idCurvesVar
        self.mappingResColMarLab = mappingResColMarLab
        self.resultsAvg = resultsAvg
        self.resultsVar = resultsVar
        self.x_label = x_label
        self.y_label = y_label
        self.fontSize = fontSize
        self.markerSize = markerSize
        self.line_width = line_width
        self.orderLegendPolicies = ["LRU", "LFU", "L_NFPL", "S_NFPL", "D_NFPL", "OPT"]
        self.offset = offset

    def genYaxis(self):
        n = len(self.policies)
        y_axis = [0] * n
        for i in range(n):
            alg = self.policies[i]
            y_axis[i] = self.resultsAvg[alg]
        return y_axis

    def genYFill(self):
        n = len(self.policies_fill)
        y_fill = [0] * n
        for i in range(n):
            alg = self.policies_fill[i]
            y_fill[i] = (self.resultsVar[alg][0], self.resultsVar[alg][1])
        return y_fill

    def save_legend_only(self, filename="legend_only.pdf"):
        fig, ax = plt.subplots(figsize=(10, 2))
        handles = []
        labels = []

        legend_policies = [p for p in self.orderLegendPolicies if p in self.policies]

        for policy in legend_policies:
            mapping = self.mappingResColMarLab[policy]
            handle, = ax.plot([], [],
                              marker=mapping[1],
                              color=mapping[0],
                              label=mapping[2],
                              linestyle=mapping[3],
                              markersize=self.markerSize,
                              linewidth=self.line_width,
                              fillstyle='none',
                              markeredgewidth=10)
            handles.append(handle)
            labels.append(mapping[2])

        ax.legend(handles, labels, loc='center', ncol=len(handles), fontsize=self.fontSize - 10)
        ax.axis('off')
        plt.savefig(f'Images/{filename}', bbox_inches='tight')
        plt.close(fig)

    def plotFunction(self, step: int, name_img: str, show_legend: bool = False):
        n_points = len(self.resultsAvg[self.policies[0]])
        x_axis = step * np.arange(1, n_points + 1)
        y_axis = self.genYaxis()
        y_fill = self.genYFill()
        _, ax_ = plt.subplots(figsize=(18, 10))
        plt.xlabel(self.x_label, fontsize=self.fontSize)
        plt.ylabel(self.y_label, fontsize=self.fontSize)

        n = len(y_axis)
        map_plot_policy = {}
        for i in range(n):
            alg = self.policies[i]
            mapping = self.mappingResColMarLab[alg]
            pi = plt.plot(x_axis[self.offset:],
                          y_axis[i][self.offset:],
                          linewidth=self.line_width,
                          marker=mapping[1],
                          label=mapping[2],
                          color=mapping[0],
                          markersize=self.markerSize,
                          # linestyle=line_style[i],
                          fillstyle='none',
                          markeredgewidth=10,
                          linestyle=mapping[3]
                          )[0]
            map_plot_policy[alg] = pi

        m = len(y_fill)

        for i in range(m):
            alg = self.policies_fill[i]
            mapping = self.mappingResColMarLab[alg]
            ax_.fill_between(x_axis[self.offset:],
                             y_fill[i][0][self.offset:], y_fill[i][1][self.offset:], color=mapping[0],
                             alpha=0.1)

        plt.xticks(fontsize=self.fontSize - 10)
        plt.yticks(fontsize=self.fontSize - 10)

        formatter = ScalarFormatter(useMathText=True)
        formatter.set_powerlimits((-1, 1))  # Forces scientific notation for large and small numbers
        ax_.ticklabel_format(axis='x', style='sci', scilimits=(-1, 1))
        ax_.xaxis.get_offset_text().set_size(50)

        ax_.xaxis.set_major_formatter(formatter)
        # Force the use of scientific notation and display the base 10 exponent
        # orderLabels = []
        # for ele in self.orderLegendPolicies:
        #     orderLabels.append(self.mappingResColMarLab[ele][2])
        # plt.legend([map_plot_policy[label] for label in self.orderLegendPolicies],
        #            orderLabels, fontsize=self.fontSize - 10)
        # plt.legend(fontsize=self.fontSize - 10)
        if show_legend:
            legend_policies = [p for p in self.orderLegendPolicies if p in map_plot_policy]
            orderLabels = [self.mappingResColMarLab[p][2] for p in legend_policies]
            plt.legend([map_plot_policy[p] for p in legend_policies],
                       orderLabels,
                       fontsize=self.fontSize - 10)

        path = f'{name_img}'
        plt.savefig(path, bbox_inches='tight')

        plt.show()
