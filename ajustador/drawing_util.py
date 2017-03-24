import numpy as np
from matplotlib import lines, legend_handler

class HandlerVLineCollection(legend_handler.HandlerLineCollection):
    """
    Handler for vertical line instances.
    """
    def create_artists(self, legend, orig_handle,
                       xdescent, ydescent, width, height, fontsize, trans):

        ydata = np.array([0, height - ydescent], float)
        xdata = (width - xdescent) / 2 * np.ones_like(ydata)
        legline = lines.Line2D(xdata, ydata)

        self.update_prop(legline, orig_handle, legend)
        legline.set_transform(trans)

        return [legline]
