import numpy as np

from matplotlib import pyplot as plt
plt.ion()

Erests = np.r_[-0.080:-0.039:0.005]
Eleaks = np.r_[-0.075:-0.029:0.005]
f, ax = plt.subplots(Erests.size, Eleaks.size, sharex=True, sharey=True)

for i, Erest in enumerate(Erests):
    for j, Eleak in enumerate(Eleaks):
        try:
            dat = np.load('vm_Erest={:.3f}_Eleak={:.3f}.npy'.format(Erest, Eleak))
        except FileNotFoundError:
            continue
        t = np.linspace(0, 0.45, dat.size)
        ax[i,j].plot(t, dat)
        if i == 0:
            ax[i,j].xaxis.set_label_position("top")
            ax[i,j].set_xlabel('{}{:.3f}'.format('Eleak=' if j==0 else '', Eleak))
        if j == Eleaks.size - 1:
            ax[i,j].yaxis.set_label_position("right")
            ax[i,j].set_ylabel('{}{:.3f}'.format('Erest=' if i==Erest.size-1 else '', Erest))
