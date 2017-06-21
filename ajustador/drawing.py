import operator
import itertools
import math
import pprint
from matplotlib import pyplot, patches
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from scipy import stats, interpolate
import pandas as pd

from . import loader, fitnesses, utilities

def _on_close(event):
    event.canvas.figure.closed = True

try:
    _GRAPHS
except NameError:
    _GRAPHS = {}
def _get_graph(name, figsize=None, clear=True, newplot=False):
    if newplot:
        _GRAPHS.pop(name, None)
    try:
        f = _GRAPHS[name]
    except KeyError:
        pass
    else:
        if not f.closed:
            if clear:
                f.clear()
                f.canvas.draw() # this is here to make it easier to see what changed
                f.plot_counter = 0
            else:
                f.plot_counter += 1
            return f
    f = _GRAPHS[name] = pyplot.figure(figsize=figsize)
    f.canvas.set_window_title(name)
    f.closed = False
    f.plot_counter = 0
    f.canvas.mpl_connect('close_event', _on_close)
    return f

def plot_together(*groups, offset=False, labels=None, separate=False):
    f = _get_graph(groups[0].name + ' together')

    if separate:
        f.subplots_adjust(left=0.03, bottom=0.03, right=0.97, top=0.97,
                          wspace=0.26, hspace=0.20)
        n = len(groups[0].waves)
        columns = 1 if n == 1 else 2 if n in (2, 4) else 3 if n <= 9 else 4 if n <= 16 else 5
    else:
        ax = f.gca()

    for i, waves in enumerate(groups):
        c = [0, 0, 0]
        ptp = waves.injection.ptp()
        if ptp > 0:
            off = waves.injection.min() - 0.2 * ptp
            ptp *= 1.2
        else:
            off = waves.injection.min() - 100e-12
            ptp = 100e-12

        for j, curve in enumerate(waves.waves):
            if separate:
                ax = f.add_subplot(int(math.ceil(n/columns)), columns, j+1)

            c[(i+2) % len(c)] = np.clip((curve.injection - off)/ptp, 0, 1)
            kwargs = {}
            if j == len(waves.waves)-1:
                if labels is None or labels[i] is None:
                    kwargs['label'] = waves.name
                else:
                    kwargs['label'] = labels[i]
            y = curve.wave.y - (curve.baseline.x if offset else 0)
            ax.plot(curve.wave.x, y, c=tuple(c), **kwargs)

    ax.legend(loc='lower right', fontsize=8)
    f.tight_layout()
    f.canvas.draw()
    f.show()
    return f

def plot_waves(waves):
    f = _get_graph(waves.name + ' baseline and steady state', figsize=(16,10))
    f.subplots_adjust(left=0.03, bottom=0.03, right=0.97, top=0.97,
                      wspace=0.26, hspace=0.20)
    n = len(waves.waves)
    columns = 1 if n == 1 else 2 if n in (2, 4) else 3 if n <= 9 else 4 if n <= 16 else 5
    for i, curve in enumerate(waves.waves):
        ax = f.add_subplot(int(math.ceil(n/columns)), columns, i+1)
        ax.plot(curve.wave.x, curve.wave.y)
        ax.set_title('{} / {}V'.format(waves.name, curve.injection), fontsize=8)

        baseline = curve.baseline
        ax.hlines([baseline.x, baseline.x + baseline.dev*3, baseline.x - baseline.dev*3],
                  curve.wave.x.min(), curve.wave.x.max(), 'y')

        steady = curve.steady
        ax.hlines([steady.x, steady.x + steady.dev*3, steady.x - steady.dev*3],
                  curve.wave.x.min(), curve.wave.x.max(), 'g')

        spikes = curve.spikes
        if spikes.size:
            ax.vlines(spikes.x, -0.08, spikes.y, 'r')
            ax.text(0.5, 0.5, '{} spikes'.format(len(spikes)),
                    horizontalalignment='center',
                    transform=ax.transAxes)

    f.canvas.draw()
    f.show()
    return f

def plot_rectification(waves):
    f = _get_graph(waves.name + ' activation', figsize=(16,10))
    ii = 0
    n = len(waves.waves)
    columns = 1 if n == 1 else 2 if n in (2, 4) else 3 if n <= 9 else 4 if n <= 16 else 5
    for i, curve in enumerate(waves.waves):
        if curve.response.x >= -12e-12:
            continue
        ax = f.add_subplot(int(math.ceil(n/columns)), columns, i+1)
        ax.plot(curve.wave.x, curve.wave.y)
        ax.set_title('{0.filename} / {0.injection}V'.format(curve), fontsize=8)

        ccut = curve.falling_curve
        baseline = curve.baseline
        steady = curve.steady
        rect = curve.rectification
        ax.plot(ccut.x, ccut.y, 'r')
        ax.set_xlim(curve.baseline_before, ccut.x.max() + .01)

        fit = curve.falling_curve_fit
        if fit.good:
            ax.plot(ccut.x, baseline.x + fit.function(ccut.x, *fit.params), 'g--')
            ax.hlines([steady.x, steady.x-rect.x], 0.20, 0.40)

        ii += 1

    f.canvas.draw()
    f.show()
    return f

def plot_shape(what, *group):
    f = _get_graph('shape')
    f.canvas.set_window_title('shape for {}'.format(what))
    ax = f.gca()
    op = operator.attrgetter(what)
    for waves in group:
        inj, val = waves.injection, op(waves)
        ord = inj.argsort()
        ax.plot(inj[ord], val[ord],
                '-o' if waves.__class__.__module__ == 'ajustador.loader' else '--+',
                label=getattr(waves, 'name', '(mixed)'))
    ax.legend(loc='best', fontsize=8)

    f.canvas.draw()
    f.show()
    return f

def plot_shape2(what, *group):
    f = _get_graph('activation')
    ax = f.gca()
    for waves in group:
        x = [wave.falling_curve.y.min() if wave.falling_curve.y.size > 0 else np.nan
             for wave in waves]
        ax.plot(x, getattr(waves, what).x,
                '-o' if waves.__class__.__module__ == 'ajustador.loader' else '--+',
                label=getattr(waves, 'name', '(mixed)'))
    ax.legend(loc='best', fontsize=8)

    f.canvas.draw()
    f.show()
    return f

def plot_param_space(group, measurement=None, *what, **options):
    age = options.get('age', False)
    fitness_func = options.get('fitness', fitnesses.combined_fitness)
    values = group.param_values(*what)
    if age:
        fitness = np.arange(1, len(values)+1)
    else:
        fitness = [fitness_func(item, measurement) for item in group]

    f = _get_graph('param space')
    f.canvas.set_window_title('3-param view for {}'.format(fitness_func.__name__))
    ax = f.gca(projection='3d')
    if measurement is not None:
        sca = ax.scatter(*values.T, c=fitness)
        f.colorbar(sca, shrink=0.5, aspect=10)
    else:
        ax.scatter(*values.T)
    ax.set_xlabel(what[0])
    ax.set_ylabel(what[1])
    if len(what) > 2:
        ax.set_zlabel(what[2])

    history = options.get('history', False)
    if history:
        ax.plot(*values.T, c='k')

    f.canvas.draw()
    f.show()
    return f

def plot_history(groups, measurement=None, *,
                 show_quit=False, labels=None, ymax=None, fitness=None,
                 clear=True,
                 newplot=False):

    if hasattr(groups[0], 'name'):
        groups = groups,

    func = fitness or groups[0].fitness_func

    name = 'fit history {}'.format(measurement.name)
    f = _get_graph(name, clear=clear, newplot=newplot)
    ax = f.gca()

    colors = list('rgbkmc')
    markers = 'x+12348'
    colors = colors[f.plot_counter:] + colors[:f.plot_counter]
    markers = markers[f.plot_counter:] + markers[:f.plot_counter]

    for i, group in enumerate(groups):
        func = fitness or group.fitness_func

        fitnesses = [func(item, measurement) for item in group]
        fitnesses = pd.DataFrame(fitnesses)
        if show_quit:
            quit = fitnesses.fit_finished(fitnesses)

        color = colors[i % len(colors)]
        marker = markers[i % len(markers)]

        label = (labels[i] if labels is not None else
                 '{} {}'.format(group.name, func.__name__))
        if show_quit:
            ax.plot(fitnesses[-quit], color + marker, label=label, picker=5)
            ax.plot(fitnesses[quit], marker=marker, color='0.5', picker=5)
        else:
            ax.plot(fitnesses, color + marker, label=label, picker=5)

    if ymax is not None:
        ax.set_ylim(top=ymax)
    ax.legend(frameon=True, loc='upper right', fontsize=8, numpoints=1)
    ax.set_xlabel('generation')
    ax.set_ylabel(func.__name__)
    f.tight_layout()
    f.canvas.draw()

    def onpick(event):
        thisline = event.artist
        xdata = thisline.get_xdata()
        ind = event.ind
        x = xdata[ind][0]
        sim = groups[0][x]

        texts = []
        if hasattr(sim, 'report'):
            texts.append(sim.report())
        if hasattr(measurement, 'report'):
            texts.append(measurement.report())

        if measurement:
            # FIXME: map from artist to group
            f = plot_together(measurement, sim,
                              labels=[None, '{}: {}'.format(x, sim.name)])
            if hasattr(func, 'report'):
                texts.append(func.report(sim, measurement))
        else:
            plot_together(sim)
        if texts:
            f.axes[0].text(0, 1, '\n\n'.join(texts),
                           verticalalignment='top',
                           transform=ax.transAxes,
                           fontsize=7)

    if hasattr(f, '_pick_event_id'):
        f.canvas.mpl_disconnect(f._pick_event_id)
    f._pick_event_id = f.canvas.mpl_connect('pick_event', onpick)

    f.show()
    return f

def plot_param_view(group, measurement, *what, **options):
    fitness_func = options.get('fitness', fitnesses.combined_fitness)

    values = group.param_values(*what)
    fitness = [fitness_func(item, measurement) for item in group]

    f = _get_graph('param space')
    f.canvas.set_window_title('2-param view for {}'.format(fitness_func.__name__))
    ax = f.gca(projection='3d')
    sca = ax.scatter(values[:, 0], values[:, 1], fitness, c=fitness)
    f.colorbar(sca, shrink=0.5, aspect=10)
    ax.set_xlabel(what[0])
    ax.set_ylabel(what[1])
    ax.set_zlabel("fitness")

    history = options.get('history', False)
    if history:
        ax.plot(*values.T, c='k')

    f.canvas.draw()
    f.show()
    return f

def plot_param_section(group, measurement, *what, regression=False,
                       fitness=None, fitness_name=None,
                       log=False):
    if not what:
        what = group.param_names()
    columns = 1 if len(what) < 6 else 2

    if fitness is None:
        fitness = group.fitness_func
    if fitness_name is None:
        fitness_name = getattr(fitness, '__name__', str(fitness))

    values = group.param_values(*what)
    fitnesses = [fitness(item, measurement) if measurement is not None else fitness(item)
                 for item in group]

    rows = int(math.ceil(values.shape[1] / columns))

    f = _get_graph(' '.join(('param section',
                             getattr(group, 'name', '(no name)'),
                             fitness_name)))
    f.subplots_adjust(left=0.08, bottom=0.06, right=0.96, top=0.97,
                      wspace=0.17, hspace=0.24)

    for n, param in enumerate(what):
        ax = f.add_subplot(rows, columns, (n%rows)*columns + n//rows + 1)
        res = ax.scatter(values.T[n], fitnesses,
                         c=range(len(values)))

        if regression:
            a, b = stats.linregress(values.T[n], fitnesses)[:2]
            x1, x2 = values.T[n].min(), values.T[n].max()
            ax.plot([x1, x2], [a*x1+b, a*x2+b], 'r--')

        if log:
            ax.set_yscale('symlog' if isinstance(log, int) else log)

        if n == (rows - 1) // 2 * columns:
            ax.set_ylabel(fitness_name)
        ax2 = ax.twinx()
        ax2.set_ylabel(what[n])
        ax2.set_yticks([])

    f.colorbar(res, ax=f.axes, shrink=0.5, aspect=10)
    f.canvas.draw()
    f.show()
    return f


def _product(seq):
    return reduce(operator.mul, seq, 1)

def clutter(array):
    if array.shape[0] > array.shape[1]:
        # we want horizontal layouts because they fit better in the window
        return np.inf
    else:
        dd0 = np.diff(array, axis=0) ** 2
        dd1 = np.diff(array, axis=1) ** 2
        return np.nanmean(np.hstack((dd0.flat, dd1.flat)))**0.5

def cbdr(values, func, xnames, yname, order=None, debug=False):
    """We have n dimensions, with a shape like (d0, d1, ..., d(n-1)).
    Each variable has a range... but let's map them to (0,1).
    Then final mapping is:

    X = x'(n-1) + x'(n-3) * d(n-1) + ... + x'(0 or 1) * d(2 or 3)
    Y = x'(n-2) + x'(n-4) * d(n-2) + ... + x'(1 or 0) * d(3 or 2)

    where

    x'(i) = [x(i) - min x(i)] / [max x(i) - min x(i)]

    So the multiplier for x' is

    (1, 1, d(2), d(3), d(4), ..., d(n-1))
    """
    dimsplit = values.shape[1] // 2
    orders = ((order,) if order is not None
              else itertools.permutations(range(values.shape[1])))

    xorig, yorig = utilities.arange_values(values, func)

    best = np.inf
    for perm in orders:
        _xs = utilities.reorder_list(xorig, perm)
        _ys = utilities.reorder_array(yorig, perm)

        _ys_shape = np.array(_ys.shape)
        _finalshape = (_product(_ys_shape[:dimsplit]), _product(_ys_shape[dimsplit:]))
        _final = np.resize(_ys, _finalshape)

        cl = clutter(_final)

        if debug:
            print('{} {} → rms(clutter)={}, {}'
                  .format(perm,
                          '-'.join(xnames[i] for i in perm), cl,
                          '*' if cl < best else ''))
        if cl < best or np.isinf(best):
            xs, ys = _xs, _ys
            best = cl
            order = perm
            finalshape, final = _finalshape, _final
            ys_shape = _ys_shape

    print('Parameters:')
    m = max(len(p) for p in xnames)
    for i in range(len(order)):
        print('(axis {}) {}: {:{}} {}'.format(order[i], '-|'[i < dimsplit], xnames[order[i]], m, xs[i].flatten()))

    f = _get_graph('cbdr')
    f.canvas.set_window_title('cbdr {} × {} → {}'
                              .format('-'.join(xnames[i] for i in order[:dimsplit]),
                                      '-'.join(xnames[i] for i in order[dimsplit:]),
                                      yname))
    ax = f.gca()
    rms = (np.array(func)**2).mean()**0.5
    ax.set_title('{} rms(fitness)={} rms(clutter)={}'.format(yname, rms, best))
    im = ax.imshow(final, interpolation='none', origin='lower')
    ax.set_xticks([])
    ax.set_yticks([])
    f.colorbar(im, shrink=0.5, aspect=10)

    if debug:
        f2 = _get_graph('cbdr - clutter')
        print('final shape', finalshape, final.shape)
        im = f2.add_subplot(2, 1, 1).imshow(np.diff(final, axis=0)**2,
                                            interpolation='none', origin='lower')
        f2.colorbar(im, shrink=0.5, aspect=10)
        im = f2.add_subplot(2, 1, 2).imshow(np.diff(final, axis=1)**2,
                                            interpolation='none', origin='lower')
        f2.colorbar(im, shrink=0.5, aspect=10)
        f2.canvas.draw()
        f2.show()

    for i in range(len(ys_shape)):
        if i < dimsplit:
            size = _product(ys_shape[i+1:dimsplit])
            w, h = 1, size
            pos = (-dimsplit + i) * 2 - 1.5, 0 - .5
            textpos = pos[0] + .5, size - .25
            textopt = dict(verticalalignment='bottom', horizontalalignment='center', rotation=90)
        else:
            size = _product(ys_shape[i+1:])
            w, h = size, 1
            pos = 0 - .5, (-len(ys_shape) + i) * 2 - 1.5
            textpos = size - .25, pos[1] + .5
            textopt = dict(verticalalignment='center')
        # print(i, pos, w, h)
        ax.add_patch(patches.Rectangle(pos, w, h, clip_on=False, alpha=0.3, facecolor='grey'))
        ax.text(textpos[0], textpos[1], xnames[order[i]], **textopt)

    f.canvas.draw()
    f.show()
    return f

def plot_flat(group, measurement, *what, **options):
    if not what:
        what = group.param_names()

    fitness_func = options.pop('fitness', fitnesses.combined_fitness)
    log = options.pop('log', False)

    values = group.param_values(*what)
    fitness = [fitness_func(item, measurement, **opts) for item in group]

    nontrivial = np.ptp(values, axis=0) > 1e-10
    values = values[:, nontrivial]
    what = np.array(what)[nontrivial]
    print(values)
    print(what)
    if log:
        fitness = np.log(fitness)

    return cbdr(values, fitness, what, fitness_func.__name__, **options)

def _make_grid(values, npoints=200):
    # values is (measures × dimensions)
    xi = (np.linspace(dim.min(), dim.max(), npoints)
          for dim in values.T)
    return np.meshgrid(*xi, sparse=True)

def find_min_values(values, fitness):
    df = pd.DataFrame(np.hstack((values, np.array(fitness)[:,None])))
    mins = df.groupby(list(range(values.shape[1]))).min()
    mins.reset_index(inplace=True)
    return mins.values[:, :-1], mins.values[:, -1]

def plot_map(group, measurement, *what, **options):
    fitness_func = options.pop('fitness', fitnesses.combined_fitness)
    log = options.pop('log', False)
    dots = options.pop('dots', False)

    values = group.param_values(*what)
    fitness = [fitness_func(item, measurement, **options) for item in group]

    rms = (np.array(fitness)**2).mean()**0.5
    if log:
        fitness = np.log(fitness)

    yname = fitness_func.__name__
    f = _get_graph('param map')
    f.canvas.set_window_title('params {} × {} → {}'.format(what[0], what[1], yname))

    values, fitness = find_min_values(values, fitness)
    grid_x, grid_y = _make_grid(values)
    points = interpolate.griddata(values, fitness, (grid_x, grid_y), method=method)

    extent = (values[:,0].min(), values[:,0].max(),
              values[:,1].min(), values[:,1].max())

    ax = f.gca()
    ax.set_title('{} rms(fitness)={}'.format(yname, rms))
    ax.set_xlabel(what[0])
    ax.set_ylabel(what[1])
    im = ax.imshow(points,
                   extent=extent,
                   origin='lower', aspect='auto', **options)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    f.colorbar(im, shrink=0.5, aspect=10)

    if dots:
        ax.plot(values[:,0], values[:,1], 'k.', ms=1)

    f.canvas.draw()
    f.show()
    return f
