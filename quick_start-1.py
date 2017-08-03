from matplotlib import pyplot
import measurements1
exp = measurements1.waves042811
pyplot.plot(exp.waves[22].wave.x, exp.waves[22].wave.y)
pyplot.title(exp.name)