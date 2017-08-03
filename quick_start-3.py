import measurements1
import ajustador as aju
import ajustador.drawing

params = aju.optimize.ParamSet(
    ('RA',           4.309,  0,   100),
    ('RM',           0.722,  0,    10),
    ('CM',           0.015,  0, 0.100))

fitness = aju.fitnesses.combined_fitness()

fit = aju.optimize.Fit('quick-start-d1.fit',
                       measurements1.waves042811[[0, 6, 23]],
                       'd1d2', 'D1',
                       fitness,
                       params)
fit.load()
aju.drawing.plot_history(fit, fit.measurement)