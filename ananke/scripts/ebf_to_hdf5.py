#!/usr/bin/env python

import os
import sys
import argparse
import logging
import time

from .. import ebf_conversion, io, envs

def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gal', required=True, type=str,
                         help='Galaxy name of run')
    parser.add_argument('--lsr', required=True, type=int,
                        help='LSR number of run')
    parser.add_argument('--rslice', required=True, type=int,
                        help='Radial slice of run')
    # DEPRECATED: batching with EBF is too unreliable
    # parser.add_argument('--ijob', type=int, default=0, help='Job index')
    # parser.add_argument('--Njob', type=int, default=1, help='Total number of jobs')
    # parser.add_argument('--batch-size', required=False, type=int, default=1000000,
                        # help='Batch size')
    return parser.parse_args()

def set_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger

def main(FLAGS, LOGGER=None):
    """ Convert EBF format into HDF5 format """
    gal = FLAGS.gal
    lsr = FLAGS.lsr
    rslice = FLAGS.rslice

    if LOGGER is None:
        LOGGER = set_logger()

    ## Start script
    # get file information from galaxy, lsr, and rslice
    ebf_path = os.path.join(
        envs.EBF_BASEDIR, f"{gal}/lsr-{lsr}",
        f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced.ebf")
    ebf_ext_path = os.path.join(
        envs.EBF_BASEDIR, f"{gal}/lsr-{lsr}",
        f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced.ext.ebf")
    hdf5_path = os.path.join(
        envs.HDF5_BASEDIR, f"{gal}/lsr-{lsr}",
        f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.hdf5")

    # create output directory if not already exists
    os.makedirs(os.path.dirname(hdf5_path), exist_ok=True)

    LOGGER.info("Convert EBF into HDF5")
    LOGGER.info(f"EBF path     : {ebf_path}")
    LOGGER.info(f"EBF ext path : {ebf_ext_path}")
    LOGGER.info(f"HDF5 path    : {hdf5_path}")
    LOGGER.info(f"Batch size   : {FLAGS.batch_size}")

    # overwrite HDF5 file if exist
    if os.path.exists(hdf5_path):
        LOGGER.warn("Overwrite HDF5 file")
        os.remove(hdf5_path)

    # NOTE: there was an issue with the EBF file if i=0 and N=1
    # so this has to be called as a special case and not using ebf_to_hdf5_split
    io.ebf_to_hdf5(
        ebf_path, hdf5_path, ebf_conversion.ALL_MOCK_KEYS,
        FLAGS.batch_size)
    io.ebf_to_hdf5(
        ebf_ext_path, hdf5_path, ebf_conversion.ALL_EXT_KEYS,
        FLAGS.batch_size)
    # else:
    #     io.ebf_to_hdf5_split(
    #         ebf_path, hdf5_path, ebf_conversion.ALL_MOCK_KEYS,
    #         FLAGS.ijob, FLAGS.Njob, FLAGS.batch_size)
    #     io.ebf_to_hdf5_split(
    #         ebf_ext_path, hdf5_path, ebf_conversion.ALL_EXT_KEYS,
    #         FLAGS.ijob, FLAGS.Njob, FLAGS.batch_size)

if __name__ == "__main__":
    FLAGS = parse_cmd()
    LOGGER = set_logger()

    # run main and keep track of time
    t0 = time.time()
    main(FLAGS, LOGGER)
    t1 = time.time()

    LOGGER.info(f"Total run time: {t1 - t0}")
    LOGGER.info("Done!")

