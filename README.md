# Synthetic Caching Policy Comparison Tool

This repository provides a simulation tool for comparing caching policies on **synthetic request sequences** while allowing for partial observation of the requests. This tool accompanies the following paper: 

- [arXiv version][arxiv]
- [Published version][published]


The tool is designed to be used through a graphical interface built with **Gooey**. Users launch the main script, choose the experiment parameters from the GUI, and generate plots comparing the selected caching policies.

---

## Repository structure

```text
.
├── main_.py
├── utils_Cache_Algos.py
├── utils_Input_Acquisition.py
├── utils_Request_Process.py
├── utils_Plotting_Class.py
├── requirements.txt
├── README.md
├── Images/
│   └── Test/
└── Files/
    └── Test/
```

---

## Main files

### `main_.py`

Main entry point. It launches the graphical interface, reads the chosen parameters, runs the simulations, saves the results, and produces the plots.

### `utils_Input_Acquisition.py`

Defines the Gooey graphical interface. This is where users choose the request model, cache size, time horizon, policies, plotting options, and output filenames.

### `utils_Request_Process.py`

Defines the synthetic request generators.

### `utils_Cache_Algos.py`

Implements the caching policies.

### `utils_Plotting_Class.py`

Handles plotting, confidence intervals, and the standalone legend.

---

## Installation

First, make sure Python is installed on your computer.


Creating a virtual environment is recommended, but not mandatory. It keeps the Python packages used by this project separate from the packages used by other projects on your computer.

On macOS or Linux:

```bash
python -m venv venv
source venv/bin/activate
```

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Then install the dependencies:

```bash
pip install -r requirements.txt
```

---

## Running the tool

Launch the graphical interface with:

```bash
python main_.py
```

A Gooey window will open. From this interface, you can choose the request model, cache size, time horizon, caching policies, and plotting options.



---

## Synthetic request models

The tool supports the following synthetic request processes.

### `RoundRobin`

Requests items cyclically:

```text
0, 1, 2, ..., n-1, 0, 1, ...
```

This is useful as a simple deterministic baseline.

### `Zipf`

Generates independent requests according to a Zipf popularity distribution.

Important parameter:

- `skew_zipf`: Zipf exponent. Larger values mean more concentrated popularity.

### `Zipf_RR`

A deterministic round-robin-style sequence whose item frequencies follow a Zipf-like profile.

### `Zipf_Swap`

A non-stationary synthetic workload. The request distribution is Zipf within each segment, but the identity of popular items shifts across segments.

Important parameters:

- `n_segments_Zipf_Swap`: number of popularity phases.
- `swap_size_Zipf_Swap`: how much the popularity vector is shifted at each phase.

### `TwoGroups`

A stationary synthetic workload with two groups:

- a popular group,
- a less popular group.

Important parameters:

- `mass_popular_TwoGroups`: total probability mass assigned to the popular group.
- `n_popular_TwoGroups`: number of popular items.

### `TwoGroups_RR`

A deterministic round-robin-style sequence whose frequencies follow the two-group popularity model.

---

## Caching policies

The following policies can be compared:

- `L_NFPL`
- `S_NFPL`
- `D_NFPL`
- `LFU`
- `LRU`

The script also computes `OPT`, the optimal static cache benchmark, and includes it in the plot automatically.

---

## Main parameters

### General parameters

| Parameter | Meaning |
|---|---|
| `n_items` | Number of distinct items in the catalogue |
| `cache_capacity` | Cache size |
| `time_horizon` | Number of requests |
| `BPO_probability` | Probability that a request is observed |
| `batch_size` | Batch size used by `D_NFPL` |
| `n_samples` | Number of independent simulation runs |

### Request parameters

| Parameter | Meaning |
|---|---|
| `type_requests` | Synthetic request model |
| `skew_zipf` | Zipf exponent |
| `n_segments_Zipf_Swap` | Number of segments for `Zipf_Swap` |
| `swap_size_Zipf_Swap` | Popularity shift size for `Zipf_Swap` |
| `mass_popular_TwoGroups` | Probability mass of the popular group |
| `n_popular_TwoGroups` | Number of popular items |
| `seed_requests` | Random seed for the request sequence |

### Policy parameters

| Parameter | Meaning |
|---|---|
| `Policies` | List of caching policies to compare |
| `seed_policy` | Random seed for randomized policies |

### Plotting and output parameters

| Parameter | Meaning |
|---|---|
| `n_plot_points` | Approximate number of points shown in the plot. The script computes the interval automatically as `ceil(time_horizon / n_plot_points)` |
| `fontSize` | Plot font size |
| `markerSize` | Plot marker size |
| `read_file` | If `0`, run simulations; if `1`, load saved results |
| `file_name` | Pickle file used to save/load results |
| `img_name` | Output plot filename |
| `show_legend_inside` | If `1`, also show the legend inside the main plot |

---

## Output files

The tool produces:

1. A plot of the average miss ratio over time.
2. A standalone legend PDF.
3. A pickle file containing the simulation results.

Example output paths:

```text
Images/Test/test.pdf
Images/Test/legend_only_L.pdf
Files/Test/test.pickle
```

The standalone legend is saved in the same folder as the main plot. For example, if the main plot is saved as:

```text
Images/Test/test.pdf
```

then the legend is saved as:

```text
Images/Test/legend_only_L.pdf
```

---


## Loading previous results

If `read_file = 0`, the script runs the simulations and saves the result dictionary to `file_name`.

If `read_file = 1`, the script skips the simulations and loads the saved pickle file from `file_name`.

This is useful when simulations are expensive and you only want to regenerate plots.

---

## Example configuration

A typical experiment could use:

```text
type_requests = Zipf_Swap
n_items = 100
cache_capacity = 10
time_horizon = 10000
BPO_probability = 1.0
batch_size = 50
n_samples = 10
Policies = L_NFPL S_NFPL D_NFPL LFU LRU
n_plot_points = 10
img_name = Images/Test/zipf_swap.pdf
show_legend_inside = 0
```

Then run:

```bash
python main_.py
```

and choose the parameters in the graphical interface.

---

## Notes

- The tool is currently intended for synthetic request sequences only.
- `OPT` is added automatically and does not need to be selected in the policy list.
- Confidence intervals are plotted for the randomized NFPL policies.
- The main plot and standalone legend are saved separately to make it easier to include them in papers or presentations.


[arxiv]: https://arxiv.org/abs/2503.02758

[published]: https://ieeexplore.ieee.org/document/11273899
