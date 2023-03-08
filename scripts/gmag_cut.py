#!/usr/bin/env python

import os
import sys
import h5py
import argparse
import logging
import time

from ananke import extinction, io, envs

FLAGS = None

def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gal', required=True, type=str,
                         help='Galaxy name of run')
    parser.add_argument('--lsr', required=True, type=int,
                        help='LSR number of run')
    parser.add_argument('--rslice', required=True, type=int,
                        help='Radial slice of run')
    parser.add_argument('--ijob', type=int, default=0, help='Job index')
    parser.add_argument('--Njob', type=int, default=1, help='Total number of jobs')
    parser.add_argument('--batch-size', required=False, type=int, default=1000000,
                        help='Batch size')
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
    """ Apply Gmag cut """
    gal = FLAGS.gal
    lsr = FLAGS.lsr
    rslice = FLAGS.rslice

    if LOGGER is None:
        LOGGER = set_logger()

    ## Start script
    # keep track of time
    t0 = time.time()

    # get file information from galaxy, lsr, and rslice
    in_path = os.path.join(
        envs.HDF5_BASEDIR, f"{gal}/lsr-{lsr}",
        f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.{FLAGS.ijob}.hdf5")
    out_path = os.path.join(
        envs.DR3_PRESF_BASEDIR, f"{gal}/lsr-{lsr}",
        f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.{FLAGS.ijob}.hdf5")

    # create output directory if not already exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Apply G magnitude cut to the mock catalog
    LOGGER.info('Applying magnitude cut:')
    LOGGER.info(f'In  : {in_path}')
    LOGGER.info(f'Dest: {out_path}')

    out_f = h5py.File(out_path, 'w')
    with h5py.File(in_path, 'r') as in_f:
        N = len(in_f['dmod_true'])
        N_batch = (N + FLAGS.batch_size - 1) // FLAGS.batch_size

        for i_batch in range(N_batch):
            LOGGER.info(f'Progress [{i_batch}/{N_batch}]')
            i_start = i_batch * FLAGS.batch_size
            i_stop = i_start + FLAGS.batch_size

            # Get G magnitude
            g_mag_abs = in_f['phot_g_mean_mag_abs'][i_start: i_stop]
            dmod_true = in_f['dmod_true'][i_start: i_stop]
            g_mag_int = extinction.abs_to_app(g_mag_abs, dmod_true)
            select = (3 <= g_mag_int) & (g_mag_int <= 21)
            for key, val in in_f.items():
                io.append_dataset(out_f, key, val[i_start: i_stop][select])
    out_f.close()

if __name__ == "__main__":
    FLAGS = parse_cmd()
    LOGGER = set_logger()

    # run script and print out time
    t0 = time.time()
    main(FLAGS, LOGGER)
    t1 = time.time()

    LOGGER.info(f"Total run time: {t1 - t0}")
    LOGGER.info("Done!")

