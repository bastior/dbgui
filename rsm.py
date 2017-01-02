import itertools
import operator

import numpy as np
from scipy.spatial.distance import euclidean


def rsm(performance_table,
        criteria_weights,
        criteria_directions,
        reference_points=None):

    scoring_fn = topsis_score  # Replace function name here if you want to use another scoring function
    eligibility_fn = check_eligibility  # Replace function name here if you want to use another checker

    alternative_number, criteria_number = performance_table.shape
    results = []
    pairs_used_num = []
    # reference_points = [['aspiration', 4, 4, 4],
    #                     ['statusquo', 2, 2, 2],
    #                     ['aspiration', 4, 3, 4]
    #                     ]

    # Run filtering function on reference points
    aspiration, statusquo = filter_ref_points(reference_points)

    # Normalize criteria directions
    for i, direction in enumerate(criteria_directions):
        if direction == "min":
            criteria_weights[i] *= -1

    # Apply weights to performace table and reference points
    performance_table *= criteria_weights
    aspiration *= criteria_weights
    statusquo *= criteria_weights

    # Create pairs of aspiration and statusquo points
    pairs = list(itertools.product(aspiration, statusquo))

    # Adjust cuboids to fit points
    pairs = adjust_cuboids(performance_table, pairs)

    # Calculate volumes for each pair
    pairs_with_volumes = []
    for pair in pairs:
        volume = reduce(operator.mul, [abs(pair[0][i] - [pair[1][i]]) for i in xrange(criteria_number)])
        pairs_with_volumes.append((pair, volume))

    # Main loop
    for alternative in performance_table:
        # Calculate score with every pair if eligible
        scores = []
        for pair, volume in pairs_with_volumes:
            if not eligibility_fn(alternative, *pair):
                continue
            scores.append((scoring_fn(alternative, *pair), volume))
        # Create final score for alternative depending on volumes per pair
        volume_sum = sum([v[1] for v in scores])
        results.append(float(np.sum(score * volume / volume_sum for score, volume in scores)))
        pairs_used_num.append(len(scores))

    # return results, pairs_used
    return results


def adjust_cuboids(alternatives, pairs):
    max_alternatives = alternatives.max(0)
    min_alternatives = alternatives.min(0)
    aspirations = np.array([p[0] for p in pairs])
    statusquos = np.array([p[1] for p in pairs])

    distances = aspirations.min(0) - statusquos.max(0)

    diffs = max_alternatives - aspirations.min(0)
    diffs = np.array([diff if diff >= 0 else 0 for diff in diffs])
    aspirations_coeffs = (distances+diffs)/distances

    diffs = statusquos.max(0) - min_alternatives
    diffs = np.array([diff if diff >= 0 else 0 for diff in diffs])
    statusquos_coeffs = (distances+diffs)/distances

    new_pairs = []
    for pair in pairs:
        distance = pair[0] - pair[1]
        modif_aspir = aspirations_coeffs * distance
        modif_statusq = statusquos_coeffs * distance
        new_pairs.append((pair[0] + modif_aspir, pair[1] - modif_statusq))

    return new_pairs


def filter_ref_points(reference_points):
    aspiration, statusquo = [], []
    for ref_point in reference_points:
        direction = ref_point.pop(0)
        if direction == 'aspiration':
            aspiration.append(ref_point)
        else:
            statusquo.append(ref_point)

    # redefine if needed
    final_aspiration, final_statusquo = [], []
    if len(aspiration) > 1 and len(statusquo) > 0:
        for i in xrange(len(aspiration)):
            l = aspiration[:i] + aspiration[i+1:]
            asp_dist = sum([euclidean(aspiration[i], x) for x in l])/len(l)
            sq_dist = sum([euclidean(aspiration[i], x) for x in statusquo])/len(statusquo)
            if asp_dist > sq_dist:
                print 'Moving aspiration point', aspiration[i], 'to statusquo group'
                final_statusquo.append(aspiration[i])
            else:
                final_aspiration.append(aspiration[i])
    if len(statusquo) > 1 and len(aspiration) > 0:
        for i in xrange(len(statusquo)):
            l = statusquo[:i] + statusquo[i+1:]
            asp_dist = sum([euclidean(statusquo[i], x) for x in aspiration])/len(aspiration)
            sq_dist = sum([euclidean(statusquo[i], x) for x in l])/len(l)
            if sq_dist > asp_dist:
                print 'Moving statusquo point', statusquo[i], 'to aspiration group'
                final_aspiration.append(statusquo[i])
            else:
                final_statusquo.append(statusquo[i])

    return np.array(aspiration, dtype=float), np.array(statusquo, dtype=float)


def check_eligibility(alternative, aspiration, statusquo):
    result = True
    for i, coord in enumerate(zip(aspiration, statusquo)):
        if aspiration[i] >= statusquo[i]:
            result &= aspiration[i] >= alternative[i] >= statusquo[i]
        else:
            result &= aspiration[i] <= alternative[i] <= statusquo[i]
    return result


def topsis_score(alternative, aspiration, statusquo):
    err_aspiration = np.power((alternative - aspiration), 2)
    err_statusquo = np.power((alternative - statusquo), 2)

    sqrt_sum_aspiration_v = np.sqrt(err_aspiration.sum())
    sqrt_sum_statusquo_v = np.sqrt(err_statusquo.sum())

    return sqrt_sum_statusquo_v / (sqrt_sum_aspiration_v + sqrt_sum_statusquo_v)
