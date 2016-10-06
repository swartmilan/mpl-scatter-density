import numpy as np

import matplotlib.pyplot as plt
import matplotlib.colors as colors

from .histogram2d import histogram2d

# TODO: implement markers using convolution
# from scipy.ndimage import convolve
# kernel = np.array([[0.8, 1.0, 0.8], [1.0, 1.0, 1.0], [0.8, 1.0, 0.8]])

__all__ = ['RasterAxes']


def make_colormap(color):

    r, g, b = colors.colorConverter.to_rgb(color)

    cdict = {'red': [(0.0, 1.0, 1.0),
                     (1.0, r, r)],

             'green': [(0.0, 1.0, 1.0),
                       (1.0, g, g)],

             'blue':  [(0.0, 1.0, 1.0),
                       (1.0, b, b)]}

    return colors.LinearSegmentedColormap('custom', cdict)


def warn_not_implemented(kwargs):
    for kwarg in kwargs:
        print("WARNING: keyword argument %s not implemented in raster scatter" % kwarg)


class RasterizedScatter(object):

    def __init__(self, ax, x, y, color='black', alpha=1.0, colormap=None, norm=None, **kwargs):

        warn_not_implemented(kwargs)

        self._ax = ax
        self._ax.callbacks.connect('ylim_changed', self._update)
        self._ax.figure.canvas.mpl_connect('resize_event', self._update)
        self._ax.figure.canvas.mpl_connect('button_press_event', self._downres)
        self._ax.figure.canvas.mpl_connect('button_release_event', self._upres)

        self.x = x
        self.y = y

        self._color = color
        self._alpha = alpha
        self._colormap = colormap
        self._norm = norm

        self._raster = None
        self._upres()

        self._update(None)

    def set_visible(self, visible):
        self._raster.set_visible(visible)

    def set_offsets(self, coords):
        self.x, self.y = zip(*coords)
        self._update(None)

    def _downres(self, event=None):
        try:
            mode = self._ax.figure.canvas.toolbar.mode
        except AttributeError:
            return
        if mode != 'pan/zoom':
            return
        self._downres = True
        self._update(None)

    def _upres(self, event=None):
        self._downres = False
        self._update(None)

    def set(self, color=None, alpha=None, norm=None, **kwargs):

        warn_not_implemented(kwargs)

        if color is not None:
            self._color = color
            self._raster.set_cmap(make_colormap(self._color))

        if alpha is not None:
            self._alpha = alpha
            self._raster.set_alpha(self._alpha)

        if norm is not None:
            self._norm = norm
            self._raster.set_norm(self._norm)

        if self._color == 'red':
            self._raster.set_zorder(20)

        self._ax.figure.canvas.draw()

    def set_zorder(self, zorder):
        self._raster.set_zorder(zorder)

    def _update(self, event):

        dpi = self._ax.figure.get_dpi()

        autoscale = self._ax.get_autoscale_on()

        if autoscale:
            self._ax.set_autoscale_on(False)

        width = self._ax.get_position().width \
            * self._ax.figure.get_figwidth()
        height = self._ax.get_position().height \
            * self._ax.figure.get_figheight()

        nx = int(round(width * dpi))
        ny = int(round(height * dpi))

        xmin, xmax = self._ax.get_xlim()
        ymin, ymax = self._ax.get_ylim()

        if self._downres:
            array = histogram2d(self.x[::16], self.y[
                                ::16], xmin, xmax, ymin, ymax, nx / 4, ny / 4)
        else:
            array = histogram2d(self.x, self.y, xmin, xmax, ymin, ymax, nx, ny)

        # TODO: required for markers
        # array = ma.array(convolve(array, kernel))

        array[array == 0] = np.nan

        if self._raster is None:
            self._raster = self._ax.imshow(array,
                                           extent=[xmin, xmax, ymin, ymax],
                                           aspect='auto',
                                           cmap=self._colormap or make_colormap(
                                               self._color),
                                           interpolation='nearest',
                                           alpha=self._alpha, origin='lower',
                                           norm=self._norm,
                                           zorder=10)
        else:
            self._raster.set_data(array)
            self._raster.set_extent([xmin, xmax, ymin, ymax])

        if autoscale:
            self._ax.set_autoscale_on(True)

    def remove(self):
        if self._raster is not None:
            self._raster.remove()
            self._raster = None

class RasterAxes(plt.Axes):

    def __init__(self, *args, **kwargs):
        plt.Axes.__init__(self, *args, **kwargs)
        self._scatter_objects = {}

    def rasterized_scatter(self, x, y, color='black', alpha=1.0, **kwargs):
        self.set_xlim(np.min(x), np.max(x))
        self.set_ylim(np.min(y), np.max(y))
        scatter = RasterizedScatter(
            self, x, y, color=color, alpha=alpha, **kwargs)
        self._scatter_objects[id(x)] = scatter
        return scatter
