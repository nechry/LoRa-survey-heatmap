"""Module providing the Heat Map Generator."""

import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
import numpy
from matplotlib import cm
from matplotlib import pyplot as pp
from matplotlib.colors import ListedColormap
# from matplotlib.offsetbox import AnchoredText
# from matplotlib.patheffects import withStroke
from matplotlib.font_manager import FontManager
from pylab import imread
from scipy.interpolate import Rbf

FORMAT = "[%(asctime)s %(levelname)s] %(message)s"
logging.basicConfig(level=logging.WARNING, format=FORMAT)
logger = logging.getLogger()


# pylint: disable=too-many-instance-attributes
class HeatMapGenerator:
    """Class HeatMapGenerator for generating HeatMap from survey data."""

    graphs = {
        'sensor_rssi': ['Received Signal Strength Indication', 'dBm'],
        'sensor_snr':  ['Signal-to-Noise Ratio', 'dB'],
        'gateway_rssi': ['Received Signal Strength Indication', 'dBm'],
        'gateway_snr':  ['Signal-to-Noise Ratio', 'dB'],
    }
    # pylint: disable=too-many-arguments
    def __init__(
            self, image_path, survey_path, cname,
            show_points=False, contours=False, thresholds=None):
        self._ap_names = {}
        self._layout = None
        self._image_width = 0
        self._image_height = 0
        self._corners = [(0, 0), (0, 0), (0, 0), (0, 0)]

        self._file_name = os.path.abspath(survey_path)
        self._path = os.path.dirname(self._file_name)
        self._title = Path(self._file_name).stem
        self._cmap = self.get_colormap(cname)
        self._contours = contours
        self._show_points = show_points
        logger.info(
            'Initialized HeatMapGenerator; title=%s, file=%s, cname=%s',  self._title,
            self._file_name, cname)
        with open(self._file_name, 'r', encoding='utf-8') as fh:
            self._data = json.loads(fh.read())
        if 'survey_points' not in self._data:
            logger.error("Error: No survey points found in %s",
                         self._file_name)
            sys.exit(0)
        logger.info('Loaded %d survey points',
                    len(self._data['survey_points']))
        if image_path is None:
            if 'img_path' not in self._data:
                logger.error("No image path found in %f", self._file_name)
                sys.exit(1)
            self._image_path = os.path.abspath(self._data['img_path'])
        else:
            self._image_path = os.path.abspath(image_path)

        self.thresholds = {}
        if thresholds is not None:
            logger.info('Loading thresholds from: %s', thresholds)
            with open(thresholds, "r", encoding="utf-8") as threshold:
                self.thresholds = json.loads(threshold.read())
            logger.debug('Thresholds: %s', self.thresholds)

        font_list = sorted(matplotlib.font_manager.get_font_names())
        logger.debug('Available fonts: %s', font_list)

    def get_colormap(self, cname):
        """
        Get colormap from matplotlib.cm or custom colormap.

        Parameters:
        - cname (str): The name of the colormap to retrieve.

        Returns:
        - colormap: The colormap object.

        """
        multi_string = cname.split('//')
        if len(multi_string) == 2:
            cname = multi_string[0]
            steps = int(multi_string[1])
            num = 256
            colormap = cm.get_cmap(cname, num)
            new_colors = colormap(numpy.linspace(0, 1, num))
            rgba = numpy.array([0, 0, 0, 1])
            interval = int(num/steps) if steps > 0 else 0
            for i in range(0, num, interval):
                new_colors[i] = rgba
            print(new_colors)
            return ListedColormap(new_colors)
        return pp.get_cmap(cname)

    def load_data(self):
        """Load data from survey file."""
        a = defaultdict(list)
        for row in self._data['survey_points']:
            a['x'].append(row['x'])
            a['y'].append(row['y'])
            a['label'].append(row['label'])
            a['sensor_rssi'].append(row['result']['rssi'])
            a['sensor_snr'].append(row['result']['snr'])
            a['gateway_rssi'].append(row['result']['gateway_rssi'])
            a['gateway_snr'].append(row['result']['gateway_snr'])
        return a

    def _load_image(self):
        self._layout = imread(self._image_path)
        self._image_width = len(self._layout[0])
        self._image_height = len(self._layout) - 1
        self._corners = [
            (0, 0), (0, self._image_height),
            (self._image_width, 0), (self._image_width, self._image_height)
        ]
        logger.info(
            'Loaded image with width=%d height=%d',
            self._image_width, self._image_height
        )

    def generate(self):
        """Generate heatmap.

        This method generates a heatmap based on the loaded image and data.
        It performs the following steps:
        1. Loads the image using the _load_image method.
        2. Loads the data using the load_data method.
        3. Appends the x and y coordinates of the corners to the data.
        4. Appends None to the 'label' field of the data.
        5. Sets any None values in the data to 0.
        6. Appends the minimum value of each data field to the data.
        7. Calculates the number of x and y points for the heatmap 
        grid based on the image dimensions.
        8. Generates the x and y coordinates for the heatmap grid using numpy.linspace.
        9. Flattens the grid coordinates.
        10. Iterates over the graphs and plots each one using the _plot method.
        11. Logs any errors that occur during plotting.

        Note: This method assumes that the necessary data and image 
        have been loaded before calling generate.
        """
        self._load_image()
        a = self.load_data()
        for x, y in self._corners:
            a['x'].append(x)
            a['y'].append(y)
            for k in a.keys():
                if k in ['x', 'y', 'label']:
                    continue
                a['label'].append(None)
                a[k] = [0 if x is None else x for x in a[k]]
                a[k].append(min(a[k]))
        num_x = int(self._image_width / 4)
        num_y = int(num_x / (self._image_width / self._image_height))
        x = numpy.linspace(0, self._image_width, num_x)
        y = numpy.linspace(0, self._image_height, num_y)
        gx, gy = numpy.meshgrid(x, y)
        gx, gy = gx.flatten(), gy.flatten()
        for k, title in self.graphs.items():
            try:
                logger.info(title)
                self._plot(a, k, title[0], title[1], gx, gy, num_x, num_y)
            # pylint: disable=broad-exception-caught
            except Exception as e:
                logger.error(e)
                logger.warning('Cannot create %s plot: insufficient data', k)

    # def _add_inner_title(self, ax, title, loc, size=None, **kwargs):
    #     logger.info('add_inner_title')
    #     if size is None:
    #         size = dict(size=pp.rcParams['legend.fontsize'])
    #     at = AnchoredText(
    #         title, loc=loc, prop=size, pad=0., borderpad=0.5, frameon=False,
    #         **kwargs
    #     )
    #     at.set_zorder(200)
    #     ax.add_artist(at)
    #     at.txt._text.set_path_effects(
    #         [withStroke(foreground="w", linewidth=3)]
    #     )
    #     return at

    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    def _plot(self, a, key, title, unit, gx, gy, num_x, num_y):
        if key not in a:
            logger.info("Skipping %s due to insufficient data", key)
            return
        if not len(a['x']) == len(a['y']) == len(a[key]):
            logger.info("Skipping %s because data has holes", key)
            return
        logger.info('Plotting: %s', key)
        pp.rcParams['figure.figsize'] = (
            self._image_width / 100, self._image_height / 100
        )
        fig, ax = pp.subplots()
        ax.set_title(title, fontname="DejaVu Sans", fontsize=10)
        if 'min' in self.thresholds.get(key, {}):
            vmin = self.thresholds[key]['min']
            logger.info('Using min threshold from thresholds: %s', vmin)
        else:
            vmin = min(a[key])
            logger.info('Using calculated min threshold: %s', vmin)

        if 'max' in self.thresholds.get(key, {}):
            vmax = self.thresholds[key]['max']
            logger.info('Using max threshold from thresholds: %s', vmax)
        else:
            vmax = max(a[key])
            logger.info('Using calculated max threshold: %s', vmax)

        logger.info("%s has range [%s,%s]", key, vmin, vmax)
        # Interpolate the data only if there is something to interpolate
        if vmin != vmax:
            rbf = Rbf(
                a['x'], a['y'], a[key], function='linear'
            )
            z = rbf(gx, gy)
            z = z.reshape((num_y, num_x))
        else:
            # Uniform array with the same color everywhere
            # (avoids interpolation artifacts)
            z = numpy.ones((num_y, num_x))*vmin
        # Render the interpolated data to the plot
        ax.axis('off')

        # begin color mapping
        norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax, clip=True)
        mapper = cm.ScalarMappable(norm=norm, cmap=self._cmap)
        # end color mapping

        image = ax.imshow(
            z,
            extent=(0, self._image_width, self._image_height, 0),
            alpha=0.4, zorder=100,
            cmap=self._cmap, vmin=vmin, vmax=vmax
        )

        # Draw contours if requested and meaningful in this plot
        if self._contours is not None and vmin != vmax:
            contours = ax.contour(z, colors='k', linewidths=0.5, levels=self._contours,
                            extent=(0, self._image_width,
                                    self._image_height, 0),
                            alpha=0.3, zorder=150, origin='upper')
            ax.clabel(contours, inline=1, fontsize=6)

        cbar = fig.colorbar(image, orientation="vertical", shrink=0.84,
                            aspect=20, pad=0.02, use_gridspec=True, label=unit)
        # change the tick label size of colorbar
        image.figure.axes[1].tick_params(axis="y", labelsize=4)

        # Print only one ytick label when there is only one value to be shown
        if vmin == vmax:
            cbar.set_ticks([vmin])

        # Draw floor plan itself to the lowest layer with full opacity
        ax.imshow(self._layout, interpolation='bicubic', zorder=1, alpha=1)

        if (self._show_points):
            labelsize = FontManager.get_default_size() * 0.4
            # begin plotting points
            for idx in range(0, len(a['x'])):
                if (a['x'][idx], a['y'][idx]) in self._corners:
                    continue
                ax.plot(
                    a['x'][idx], a['y'][idx], zorder=200,
                    marker='o', markeredgecolor='black', markeredgewidth=0.2,
                    markerfacecolor=mapper.to_rgba(a[key][idx]), markersize=8
                )
                ax.text(
                    a['x'][idx], a['y'][idx] - 13,
                    a['label'][idx], fontsize=labelsize,
                    horizontalalignment='center'
                )
            # end plotting points

        filename = os.path.join(self._path, F"{self._title}_{key}.png" )
        logger.info('Writing plot to: %s', filename)
        pp.savefig(filename, dpi=300)
        pp.close('all')


def parse_args(argv):
    """
    parse arguments/options

    this uses the new argparse module instead of optparse
    see: <https://docs.python.org/2/library/argparse.html>
    """
    p = argparse.ArgumentParser(description='LoRa survey heatmap generator')
    p.add_argument('-v', '--verbose', dest='verbose', action='count', default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('-c', '--colormap', type=str, dest='CNAME', action='store',
                   default="RdYlBu_r",
                   help='If specified, a valid matplotlib colormap name.')
    p.add_argument('-n', '--contours', type=int, dest='N', action='store',
                   default=None,
                   help='If specified, N contour lines will be added to the graphs')
    p.add_argument('-p', '--picture', dest='IMAGE', type=str, action='store',
                   default=None, help='Path to background image')
    p.add_argument(
        'FILE', type=str, help='Filename for survey'
    )
    p.add_argument('-s', '--show-points', dest='show_points', action='count',
                   default=0, help='show measurement points in file')
    p.add_argument('-t', '--thresholds', dest='thresholds', action='store',
                   type=str, help='thresholds JSON file path')
    args = p.parse_args(argv)
    return args


def set_log_info():
    """set logger level to INFO"""
    set_log_level_format(logging.INFO,
                         '%(asctime)s %(levelname)s:%(name)s:%(message)s')


def set_log_debug():
    """set logger level to DEBUG, and debug-level output format"""
    set_log_level_format(
        logging.DEBUG,
        "%(asctime)s [%(levelname)s %(filename)s:%(lineno)s - "
        "%(name)s.%(funcName)s() ] %(message)s"
    )


def set_log_level_format(level, formatstring):
    """
    Set logger level and format.

    :param level: logging level; see the :py:mod:`logging` constants.
    :type level: int
    :param formatstring: logging formatter format string
    :type formatstring: str
    """
    formatter = logging.Formatter(fmt=formatstring)
    logger.handlers[0].setFormatter(formatter)
    logger.setLevel(level)


def main():
    """ main entry """
    args = parse_args(sys.argv[1:])

    # set logging level
    if args.verbose > 1:
        set_log_debug()
    elif args.verbose == 1:
        set_log_info()

    print(args)
    HeatMapGenerator(
        image_path=args.IMAGE,
        survey_path=args.FILE,
        cname=args.CNAME,
        show_points=args.show_points > 0,
        contours=args.N,
        thresholds=args.thresholds
    ).generate()


if __name__ == '__main__':
    main()
