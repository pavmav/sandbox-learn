# -*- coding: utf-8 -*-

import copy


def run_simulation(initial_field, check_stop_function, score_function, times=5, verbose=False):
    list_results = []
    for iteration in range(times):
        field = copy.deepcopy(initial_field)
        while not check_stop_function(field):
            field.make_time()
        current_score = score_function(field)
        list_results.append(current_score)
        if verbose:
            print "Iteration: {0}  Score: {1})".format(iteration+1, current_score)

    return list_results
