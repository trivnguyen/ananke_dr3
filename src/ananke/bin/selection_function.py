#!/usr/bin/env python

import argparse
import h5py
import os
import sys
import time

import numpy as np

from ananke import io, config, selection
from ananke.logger import logger

FLAGS = None
def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gal', required=True, type=str)
    parser.add_argument('--lsr', required=True, type=str)
    parser.add_argument('--rslice', required=True, type=int)
    parser.add_argument('--which', type=str, default='both')
    return parser.parse_args()

def main(FLAGS):
    """ Apply selection function and return new files """
    gal = FLAGS.gal
    lsr = FLAGS.lsr
    rslice = FLAGS.rslice

    # get file information from galaxy, lsr, and rslice
    in_path = os.path.join(
        config.DR3_PRESF_BASEDIR, f"{gal}/lsr-{lsr}",
        f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.{FLAGS.ijob}.hdf5")
    out_path = os.path.join(
        config.DR3_BASEDIR, f"{gal}/lsr-{lsr}",
        f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.{FLAGS.ijob}.hdf5")

    # create output directory if not already exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    logger.info(f"In    : {in_path}")
    logger.info(f"Dest  : {out_path}")

    if FLAGS.which in ('both', 'general'):
        logger.info("Apply general selection function")
        with h5py.File(in_path, 'r') as in_f:
            # get selection mask
            select = selection.calc_general_select(in_f)
            logger.info("Number of stars selected: {} / {}".format(
                select.sum(), len(select)))
            # write to file
            with h5py.File(out_path, 'w') as out_f:
                # copying headers
                out_f.attrs.update(dict(in_f.attrs))
                out_f.attrs.update(dict(num_select_general=select.sum()))
                # copying all keys and apply selection function
                for key in in_f:
                    logger.info(f"Copying key: {key}")
                    data = in_f[key][:][select]
                    out_f.create_dataset(key, data=data)

    if FLAGS.which in ('both', 'rvs'):
        logger.info("Apply RVS selection function")
        with h5py.File(out_path, 'a') as out_f:
            # get RVS selection mask
            select = selection.calc_rvs_select(out_f)
            logger.info("Number of RVS stars selected: {} / {}".format(
                select.sum(), len(select)))
            out_f.attrs.update(dict(num_select_rv=select.sum()))

            rv  = out_f['radial_velocity'][:]
            rv_error = out_f['radial_velocity_error'][:]
            rv_error_corr = out_f['radial_velocity_error_corr_factor'][:]

            del out_f["radial_velocity"]
            del out_f["radial_velocity_error"]
            del out_f["radial_velocity_error_corr_factor"]

            rv[~select] = np.nan
            rv_error[~select] = np.nan
            rv_error_corr[~select] = np.nan
            out_f.create_dataset("radial_velocity", data=rv)
            out_f.create_dataset("radial_velocity_error", data=rv_error)
            out_f.create_dataset("radial_velocity_error_corr_factor",
                                 data=rv_error_corr)

if __name__ == "__main__":
    FLAGS = parse_cmd()

    # run main and keep track of time
    t0 = time.time()
    main(FLAGS)
    t1 = time.time()
    logger.info(f"Total run time: {t1 - t0}")
    logger.info("Done!")

