#!/usr/bin/env python

import argparse
import os
import sys
import time

from ananke import io, config
from ananke.logger import logger

def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gal', required=True, type=str,
                         help='Galaxy name of run')
    parser.add_argument('--lsr', required=True, type=int,
                        help='LSR number of run')
    parser.add_argument('--rslice', required=True, type=int,
                        help='Radial slice of run')
    return parser.parse_args()

def main(FLAGS):
    """ Convert EBF format into HDF5 format """
    gal = FLAGS.gal
    lsr = FLAGS.lsr
    rslice = FLAGS.rslice

    ## Start script
    # get file information from galaxy, lsr, and rslice
    ebf_path = os.path.join(
        config.EBF_BASEDIR, f"{gal}/lsr-{lsr}",
        f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced.ebf")
    ebf_ext_path = os.path.join(
        config.EBF_BASEDIR, f"{gal}/lsr-{lsr}",
        f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced.ext.ebf")
    hdf5_path = os.path.join(
        config.HDF5_BASEDIR, f"{gal}/lsr-{lsr}",
        f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.hdf5")

    # create output directory if not already exists
    os.makedirs(os.path.dirname(hdf5_path), exist_ok=True)

    logger.info("Convert EBF into HDF5")
    logger.info(f"EBF path     : {ebf_path}")
    logger.info(f"EBF ext path : {ebf_ext_path}")
    logger.info(f"HDF5 path    : {hdf5_path}")

    # overwrite HDF5 file if exist
    if os.path.exists(hdf5_path):
        logger.warn("Overwrite HDF5 file")
        os.remove(hdf5_path)

    # convert EBF format to HDF5 format
    io.ebf_to_hdf5(
        ebf_path, hdf5_path, config.ALL_MOCK_KEYS)
    io.ebf_to_hdf5(
        ebf_ext_path, hdf5_path, config.ALL_EXT_KEYS)

if __name__ == "__main__":
    FLAGS = parse_cmd()

    # run main and keep track of time
    t0 = time.time()
    main(FLAGS)
    t1 = time.time()

    logger.info(f"Total run time: {t1 - t0}")
    logger.info("Done!")

