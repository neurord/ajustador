import numpy as np

from ajustador import fitnesses
import measurements1

wnames, waves = zip(*measurements1.waves.items())

fitness_list = [
    fitnesses.response_fitness,
    fitnesses.baseline_fitness,
    fitnesses.rectification_fitness,
    fitnesses.charging_curve_fitness,
    fitnesses.falling_curve_time_fitness,
    fitnesses.mean_isi_fitness,
    fitnesses.spike_time_fitness,
    fitnesses.spike_count_fitness,
    fitnesses.spike_latency_fitness,
    fitnesses.spike_width_fitness,
    fitnesses.spike_height_fitness,
    fitnesses.spike_ahp_fitness,
    fitnesses.hyperpol_fitness,
    fitnesses.spike_fitness,
    fitnesses.simple_combined_fitness,
]

import pytest
@pytest.mark.parametrize("w2", waves, ids=wnames)
@pytest.mark.parametrize("w1", waves, ids=wnames)
@pytest.mark.parametrize("fitness", fitness_list, ids=[f.__name__ for f in fitness_list])
def test_basics(w1, w2, fitness):
    y = fitness(w1, w2)

    if np.isnan(float(y)):
        return

    same = w1 is w2
    disjoint = not (w1.injection[:,None] == w2.injection).any()
    repeats = (np.diff(w1.injection) < 1e-14).any()

    if same or disjoint or repeats:
        assert y >= 0
    else:
        assert y > 0
