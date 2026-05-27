"""
utils_Input_Acquisition
=======================

This module defines a user interface for configuring experiments via
command‑line arguments.  The :func:`create_input_dictionary` function uses
`Gooey' to present a graphical form to
the user, making it easier to specify parameters without remembering
command‑line syntax.  When run from a command‑line environment, Gooey
transforms the parser into a window with input fields.

The configuration options are grouped into logical sections: general
parameters controlling problem size and simulation, request distribution
settings, choice of caching policies, and plotting parameters.  Default
values are provided for each option so that the user can run an example
experiment with minimal effort.  The returned dictionary is typically
consumed by the main script to initialise the request generator, create
policy instances, and customise plotting.

Usage
-----

Invoke :func:`create_input_dictionary` at the beginning of your main script:

.. code-block:: python

    from utils_Input_Acquisition import create_input_dictionary

    if __name__ == '__main__':
        params = create_input_dictionary()
        # use params["n_items"], params["cache_capacity"], ...

The function returns a dictionary mapping argument names to their parsed
values.
"""

import argparse
from gooey import Gooey, GooeyParser


@Gooey(program_name="Average miss ratio over time")
def create_input_dictionary():
    parser = GooeyParser(description="Average miss ratio over time")

    general_group = {'n_items': [int, 100], 'cache_capacity': [int, 10], 'time_horizon': [int, 10000],
                     'BPO_probability': [float, 1.0], 'batch_size': [int, 1], 'n_samples': [int, 1]}

    # General Parameters
    parser_general_group = parser.add_argument_group("General")
    for var in general_group:
        big_name = "--" + var
        parser_general_group.add_argument(big_name,
                                          help=var,
                                          type=general_group[var][0],
                                          default=general_group[var][1])

    # Choice of the request process
    requests_list = ['Zipf', 'Zipf_RR', 'Zipf_Swap', 'TwoGroups', 'TwoGroups_RR']
    parser_requests_group = parser.add_argument_group('Requests')

    parser_requests_group.add_argument('--type_requests',
                                       choices=requests_list,
                                       widget='Dropdown',
                                       default='Zipf',
                                       help='Select a synthetic request model'
                                       )

    parser_requests_group.add_argument('--skew_zipf',
                                       default=1.0,
                                       type=float,
                                       help='skew zipf')

    parser_requests_group.add_argument(
        '--n_segments_Zipf_Swap',
        type=int,
        default=3,
        help='Number of segments with different popularity distribution'
    )
    parser_requests_group.add_argument(
        '--swap_size_Zipf_Swap',
        type=int,
        default=5,
        help='How many positions the Zipf weight vector is cyclically rotated at each segment'
    )

    parser_requests_group.add_argument(
        '--mass_popular_TwoGroups',
        type=float,
        default=0.5,
        help='Probability of a request for a popular item '
    )

    parser_requests_group.add_argument(
        '--n_popular_TwoGroups',
        type=int,
        default=10,
        help='Number of popular items (Group 1)'
    )

    parser_requests_group.add_argument('--seed_requests',
                                       type=int,
                                       help='seed_requests',
                                       default=0)

    # Choice of the policies to compare
    policies_list = ["L_NFPL", "S_NFPL", "D_NFPL", "LFU", "LRU"]
    parser_policies_group = parser.add_argument_group('Policies')

    parser_policies_group.add_argument('--Policies',
                                       choices=policies_list,
                                       nargs='+',
                                       default='LRU',
                                       widget='Listbox',
                                       help='Select the policies to compare '
                                       )

    parser_policies_group.add_argument('--seed_policy',
                                       type=int,
                                       help='seed_policy',
                                       default=0)

    # Choice of plotting parameters
    plots_group = {'n_plot_points': [int, 10],
                   'fontSize': [int, 62], 'markerSize': [int, 14],
                   'read_file': [int, 0], 'file_name': [str, 'Files/Test/test.pickle'],
                   'img_name': [str, 'Images/Test/test.pdf'], 'show_legend_inside': [int, 0]}
    plotting_group = parser.add_argument_group("Plotting")

    for var in plots_group:
        big_name = "--" + var
        plotting_group.add_argument(big_name,
                                    help=var,
                                    type=plots_group[var][0],
                                    default=plots_group[var][1])

    args = parser.parse_args()
    return vars(args)
