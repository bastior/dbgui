import numpy as np
import math as mt


def weightedSum(performance_table,
                criteria_weights,
                criteria_directions):

    alternative_number, criteria_number = performance_table.shape

    solution = []

    for alt in performance_table:
        solv = 0
        for i in range(len(alt)):
            if criteria_directions[i] == "min":
                criteria_weights[i] = criteria_weights[i] * -1
            solv += alt[i] * criteria_weights[i] 

        solution.append(solv)

    return solution
