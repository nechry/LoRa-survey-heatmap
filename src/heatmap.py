import os
import sys
import argparse
import logging
import json
import numpy

from collections import defaultdict
import numpy as np
import matplotlib.cm as cm
import matplotlib.pyplot as pp
from scipy.interpolate import Rbf
from pylab import imread
# from matplotlib.offsetbox import AnchoredText
# from matplotlib.patheffects import withStroke
from matplotlib.font_manager import FontManager
from matplotlib.colors import ListedColormap
import matplotlib

from pathlib import Path


FORMAT = "[%(asctime)s %(levelname)s] %(message)s"
logging.basicConfig(level=logging.WARNING, format=FORMAT)
logger = logging.getLogger()


class HeatMapGenerator(object):

    graphs = {
        'sensor_rssi': ['Received Signal Strength Indication', 'dBm'],
        'sensor_snr':  ['Signal-to-Noise Ratio', 'dB'],
        'gateway_rssi': ['Received Signal Strength Indication', 'dBm'],
        'gateway_snr':  ['Signal-to-Noise Ratio', 'dB'],
    }

    def __init__(
            self, image_path, survey_path, show_points, cname, contours, thresholds=None):
        self._ap_names = {}
        self._layout = None
        self._image_width = 0
        self._image_height = 0
        self._corners = [(0, 0), (0, 0), (0, 0), (0, 0)]

        self._file_name = os.path.abspath(survey_path)

        self._path = os.path.dirname(self._file_name)
        self._title = Path(self._file_name).stem
        self._show_points = show_points
        self._cmap = self.get_colormap(cname)
        self._contours = contours
        logger.info(
            'Initialized HeatMapGenerator; title=%s, file=%s, cname=%s',  self._title, self._file_name, cname
        )
        with open(self._file_name, 'r',encoding='utf-8') as fh:
            self._data = json.loads(fh.read())
        if 'survey_points' not in self._data:
            logger.error(
                'No survey points found in {}'.format(self._file_name))
            exit()
        logger.info('Loaded %d survey points',
                    len(self._data['survey_points']))
        if image_path is None:
            if 'img_path' not in self._data:
                logger.error(
                    'No image path found in {}'.format(self._file_name))
                exit(1)
            self._image_path = os.path.abspath(self._data['img_path'])
        else:
            self._image_path = os.path.abspath(image_path)

        self.thresholds = {}
        if thresholds is not None:
            logger.info('Loading thresholds from: %s', thresholds)
            with open(thresholds, 'r') as fh:
                self.thresholds = json.loads(fh.read())
            logger.debug('Thresholds: %s', self.thresholds)
            
        font_list = sorted(matplotlib.font_manager.get_font_names())
        logger.debug('Available fonts: %s', font_list)

    def get_colormap(self, cname):
        multi_string = cname.split('//')
        if len(multi_string) == 2:
            cname = multi_string[0]
            steps = int(multi_string[1])
            N = 256
            colormap = cm.get_cmap(cname, N)
            new_colors = colormap(np.linspace(0, 1, N))
            rgba = np.array([0, 0, 0, 1])
            interval = int(N/steps) if steps > 0 else 0
            for i in range(0, N, interval):
                new_colors[i] = rgba
            print(new_colors)
            return ListedColormap(new_colors)
        else:
            return pp.get_cmap(cname)

    def load_data(self):
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
        x = np.linspace(0, self._image_width, num_x)
        y = np.linspace(0, self._image_height, num_y)
        gx, gy = np.meshgrid(x, y)
        gx, gy = gx.flatten(), gy.flatten()
        for k, ptitle in self.graphs.items():
            try:
                logger.info(ptitle)
                self._plot(a, k, ptitle[0], ptitle[1], gx, gy, num_x, num_y)
            except Exception as e:
                logger.error(e)
                logger.warning(
                    'Cannot create {} plot: insufficient data'.format(k))

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

    def _plot(self, a, key, title, unit, gx, gy, num_x, num_y):
        if key not in a:
            logger.info("Skipping {} due to insufficient data".format(key))
            return
        if not len(a['x']) == len(a['y']) == len(a[key]):
            logger.info("Skipping {} because data has holes".format(key))
            return
        logger.info('Plotting: %s', key)
        pp.rcParams['figure.figsize'] = (
            self._image_width / 100, self._image_height / 100
        )
        fig, ax = pp.subplots()
        ax.set_title(title, fontname = "DejaVu Sans", fontsize = 10)
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

        logger.info("{} has range [{},{}]".format(key, vmin, vmax))
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
            CS = ax.contour(z, colors='k', linewidths=0.5, levels=self._contours,
                            extent=(0, self._image_width,
                                    self._image_height, 0),
                            alpha=0.3, zorder=150, origin='upper')
            ax.clabel(CS, inline=1, fontsize=6)
        
        
        cbar = fig.colorbar(image, orientation="vertical", shrink=0.84, aspect=20, pad=0.02, use_gridspec=True,label=unit)        
        # change the tick label size of colorbar
        image.figure.axes[1].tick_params(axis="y", labelsize=4)
        
        # Print only one ytick label when there is only one value to be shown
        if vmin == vmax:
            cbar.set_ticks([vmin])

        # Draw floor plan itself to the lowest layer with full opacity
        ax.imshow(self._layout, interpolation='bicubic', zorder=1, alpha=1)
        
        if(self._show_points):
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

        filename = os.path.join(self._path, '%s_%s.png' % (self._title, key))
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
    p.add_argument('-c', '--cmap', type=str, dest='CNAME', action='store',
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
    p.add_argument('-s', '--show-points', dest='showpoints', action='count',
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


def set_log_level_format(level, format):
    """
    Set logger level and format.

    :param level: logging level; see the :py:mod:`logging` constants.
    :type level: int
    :param format: logging formatter format string
    :type format: str
    """
    formatter = logging.Formatter(fmt=format)
    logger.handlers[0].setFormatter(formatter)
    logger.setLevel(level)


def main():
    args = parse_args(sys.argv[1:])

    # set logging level
    if args.verbose > 1:
        set_log_debug()
    elif args.verbose == 1:
        set_log_info()

    showpoints = True if args.showpoints > 0 else False
    HeatMapGenerator(args.IMAGE, args.FILE, showpoints, args.CNAME,
                     args.N, thresholds=args.thresholds).generate()


if __name__ == '__main__':
    main()
