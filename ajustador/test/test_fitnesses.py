import numpy as np

from ajustador import fitnesses
import measurements1

w1 = measurements1.waves042811
w2 = measurements1.waves042911

import pytest
@pytest.mark.parametrize("fitness", [
    fitnesses.response_fitness,
    fitnesses.baseline_fitness,
    fitnesses.rectification_fitness,
    fitnesses.charging_curve_fitness,
    fitnesses.falling_curve_time_fitness,
    fitnesses.mean_isi_fitness,
    fitnesses.spike_time_fitness,
    fitnesses.spike_count_fitness,
    fitnesses.spike_latency_fitness,
    fitnesses.spike_onset_fitness,
    fitnesses.spike_width_fitness,
    fitnesses.spike_height_fitness,
    fitnesses.spike_ahp_fitness,
    fitnesses.hyperpol_fitness,
    fitnesses.spike_fitness,
    fitnesses.simple_combined_fitness,
])
def test_basics(fitness):
    n = fitness(w1, w2)
    assert np.isnan(float(n)) or n > 0
