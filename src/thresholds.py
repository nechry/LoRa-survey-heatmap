""" Thresholds Generator for HeatMap Generator. """
# pylint: disable=R0801
import sys
import argparse
import logging
import json
from collections import defaultdict

from heatmap import HeatMapGenerator

FORMAT = "[%(asctime)s %(levelname)s] %(message)s"
logging.basicConfig(level=logging.WARNING, format=FORMAT)
logger = logging.getLogger()

# pylint: disable=too-few-public-methods


class ThresholdGenerator:
    """Class ThresholdGenerator for HeatMap Generator.

    This class is responsible for generating thresholds for the
    HeatMap Generator.
    It provides a method to generate thresholds based on a list
    of titles.

    Attributes:
        None

    Methods:
        generate(titles): Generates thresholds based on the
        given list of titles.

    """

    def generate(self, titles):
        """Generate thresholds based on the given list of titles.

        Args:
            titles (list): A list of titles.

        Returns:
            None

        """
        logger.info('Generating thresholds')
        res = defaultdict(dict)
        items = [HeatMapGenerator(image_path=None,
                                  survey_path=title,
                                  cname=None,
                                  show_points=False,
                                  contours=5,
                                  thresholds=None)
                 .load_data() for title in titles]

        for key in HeatMapGenerator.graphs:
            res[key]['min'] = min(
                min(value for value in x[key] if value is not None)
                for x in items
            )
            res[key]['max'] = max(
                max(value for value in x[key] if value is not None)
                for x in items
            )
        with open('thresholds.json', 'w', encoding="utf-8") as fh:
            fh.write(json.dumps(res))
        logger.info('Wrote: thresholds.json')


def parse_args(argv):
    """
    parse arguments/options

    this uses the new argparse module instead of optparse
    see: <https://docs.python.org/2/library/argparse.html>
    """
    p = argparse.ArgumentParser(
        description='LoRa survey heatmap threshold generator'
    )
    p.add_argument('-v', '--verbose',
                   dest='verbose',
                   action='count',
                   default=0,
                   help='verbose output.')
    p.add_argument(
        'TITLE', type=str, help='Title for survey (and data filename)',
        nargs='+'
    )
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
        "%(name)s.%(funcName)s() ] %(message)s")


def set_log_level_format(level, formatstring):
    """
    Set logger level and fmt.

    :param level: logging level; see the :py:mod:`logging` constants.
    :type level: int
    :param formatstring: logging format string
    :type formatstring: str
    """
    formatter = logging.Formatter(fmt=formatstring)
    logger.handlers[0].setFormatter(formatter)
    logger.setLevel(level)


def main():
    """ main entry"""
    args = parse_args(sys.argv[1:])

    # set logging level
    if args.verbose > 1:
        set_log_debug()
    elif args.verbose == 1:
        set_log_info()

    ThresholdGenerator().generate(args.TITLE)


if __name__ == '__main__':
    main()
