#!/usr/bin/env python

import argparse
import time
from collections import OrderedDict

import ebf_to_hdf5
import split_hdf5
import gmag_cut
import rotate_coords
import calc_props
import selection_function

from ananke.logger import logger

ALL_PIPELINES = OrderedDict([
    ("ebf_to_hdf5", ebf_to_hdf5),
    ("split_hdf5", split_hdf5),
    ("gmag_cut", gmag_cut),
    ("rotate_coords", rotate_coords),
    ("calc_props", calc_props),
    ("selection_function", selection_function),
])

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
    parser.add_argument('--batch-size', required=False, type=int, default=10000000,
                        help='Batch size')
    return parser.parse_args()

if __name__ == "__main__":
    """ Run all pipelines """
    FLAGS = parse_cmd()

    if FLAGS.pipeline is not None:
        logger.info("Running pipeline: {}".format(FLAGS.pipeline))
        if FLAGS.pipeline not in ALL_PIPELINES:
            raise KeyError("Pipeline {} does not exist".format(FLAGS.pipeline))

        t0 = time.time()
        ALL_PIPELINES[FLAGS.pipeline].main(FLAGS)
        t1 = time.time()
        total_dt = t1 - t0
    else:
        logger.info("Running all pipelines")
        logger.info("---------------------")
        total_dt = 0
        for pipeline in ALL_PIPELINES:
            # skipping this because EBF is unreliable and cannot be parallelized
            if pipeline == "ebf_to_hdf5":
                continue
            logger.info("Running: {}".format(pipeline))
            logger.info("----------------------------------")
            t0 = time.time()
            ALL_PIPELINES[pipeline].main(FLAGS, logger)
            t1 = time.time()
            total_dt += t1 - t0
            logger.info(f"Pipeline run time: {t1 - t0}")

    logger.info(f"Total run time: {total_dt}")
    logger.info("Done!")
