#!/usr/bin/env python

import os
import sys
import argparse
import logging
import time
from collections import OrderedDict

import ananke.scripts.ebf_to_hdf5
import ananke.scripts.gmag_cut
import ananke.scripts.rotate_coords
import ananke.scripts.calc_props
import ananke.scripts.selection_function

ALL_PIPELINES = OrderedDict([
    ("ebf_to_hdf5", ananke.scripts.ebf_to_hdf5),
    ("gmag_cut", ananke.scripts.gmag_cut),
    ("rotate_coords", ananke.scripts.rotate_coords),
    ("calc_props", ananke.scripts.calc_props),
    ("selection_function", ananke.scripts.selection_function),
])

def set_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger

def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pipeline', required=False, type=str,
                        help='Pipeline to run')
    parser.add_argument('--gal', required=True, type=str,
                         help='Galaxy name of run')
    parser.add_argument('--lsr', required=True, type=int,
                        help='LSR number of run')
    parser.add_argument('--rslice', required=True, type=int,
                        help='Radial slice of run')
    parser.add_argument('--ijob', type=int, default=0, help='Job index')
    parser.add_argument('--Njob', type=int, default=1, help='Total number of jobs')
    parser.add_argument('--ext-extrapolate', required=False, action='store_true',
                        help='Enable to extrapolate for extinction calculation')
    parser.add_argument('--err-extrapolate', required=False, action='store_true',
                        help='Enable to extrapolate for error calculation')
    parser.add_argument('--ext-var', required=False, default='bminr',
                        choices=('bminr', 'logteff'),
                        help='Variable to calculate extinction coefficient')
    parser.add_argument('--which', type=str, default='both')
    parser.add_argument('--batch-size', required=False, type=int, default=1000000,
                        help='Batch size')
    return parser.parse_args()

if __name__ == "__main__":
    """ Run all pipelines """
    FLAGS = parse_cmd()
    LOGGER = set_logger()

    if FLAGS.pipeline is not None:
        LOGGER.info("Running pipeline: {}".format(FLAGS.pipeline))
        if FLAGS.pipeline not in ALL_PIPELINES:
            raise KeyError("Pipeline {} does not exist".format(FLAGS.pipeline))

        t0 = time.time()
        ALL_PIPELINES[FLAGS.pipeline].main(FLAGS, LOGGER)
        t1 = time.time()
        total_dt = t1 - t0
    else:
        LOGGER.info("Running all pipelines")
        LOGGER.info("---------------------")
        total_dt = 0
        for pipeline in ALL_PIPELINES:
            LOGGER.info("Running: {}".format(pipeline))
            LOGGER.info("----------------------------------")
            t0 = time.time()
            ALL_PIPELINES[pipeline].main(FLAGS, LOGGER)
            t1 = time.time()
            total_dt += t1 - t0
            LOGGER.info(f"Pipeline run time: {t1 - t0}")

    LOGGER.info(f"Total run time: {total_dt}")
    LOGGER.info("Done!")

