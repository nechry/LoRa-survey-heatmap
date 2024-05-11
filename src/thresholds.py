import sys
import argparse
import logging
import json
from collections import defaultdict

from lora_survey_heatmap.heatmap import heatmap

FORMAT = "[%(asctime)s %(levelname)s] %(message)s"
logging.basicConfig(level=logging.WARNING, format=FORMAT)
logger = logging.getLogger()


class ThresholdGenerator(object):

    def generate(self, titles):
        logger.info('Generating thresholds')
        res = defaultdict(dict)
        items = [HeatMapGenerator(None, t).load_data() for t in titles]
        for key in HeatMapGenerator.graphs.keys():
            res[key]['min'] = min([
                min(value for value in x[key] if value is not None) for x in items
            ])
            res[key]['max'] = max([
                max(value for value in x[key] if value is not None) for x in items
            ])
        with open('thresholds.json', 'w') as fh:
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
    p.add_argument('-v', '--verbose', dest='verbose', action='count', default=0,
                   help='verbose output. specify twice for debug-level output.')
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

    ThresholdGenerator().generate(args.TITLE)


if __name__ == '__main__':
    main()
