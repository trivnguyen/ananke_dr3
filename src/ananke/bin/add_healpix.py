#!/usr/bin/env python

import argparse
import os
import time

import h5py
import numpy as np
import healpy as hp

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
    parser.add_argument('--nside', required=True, type=int,
                        help='Nside of Healpix map')
    parser.add_argument('--ijob', type=int, default=0, help='Job index')
    parser.add_argument('--Njob', type=int, default=1, help='Total number of jobs')
    parser.add_argument('--batch-size', required=False, type=int, default=1000000,
                        help='Batch size')
    return parser.parse_args()

def main():
    """ Calculate and write healpix index """
    FLAGS = parse_cmd()

    gal = FLAGS.gal
    lsr = FLAGS.lsr
    rslice = FLAGS.rslice

    ## Start script

    # get file information from galaxy, lsr, and rslice
    in_path = os.path.join(
        config.DR3_BASEDIR, f"{gal}/lsr-{lsr}",
        f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.{FLAGS.ijob}.hdf5")
    out_path = os.path.join(
        config.DR3_BASEDIR, f"{gal}/lsr-{lsr}",
        f"aux-lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.{FLAGS.ijob}.hdf5")

    # create output directory if not already exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Apply G magnitude cut to the mock catalog
    logger.info('Calculating Healpix index:')
    logger.info(f'In  : {in_path}')
    logger.info(f'Dest: {out_path}')

    out_f = h5py.File(out_path, 'w')
    with h5py.File(in_path, 'r') as in_f:
        N = len(in_f['dmod_true'])
        N_batch = (N + FLAGS.batch_size - 1) // FLAGS.batch_size

        for i_batch in range(N_batch):
            logger.info(f'Progress [{i_batch}/{N_batch}]')
            i_start = i_batch * FLAGS.batch_size
            i_stop = i_start + FLAGS.batch_size

            # Load the RA and DEC datasets
            ra = in_f['ra'][i_start: i_stop]
            dec = in_f['dec'][i_start: i_stop]

            # Compute the HEALPIX pixel indices for Nside; nested
            nside = FLAGS.nside
            theta = np.radians(90.0 - dec)
            phi = np.radians(ra)
            pix = hp.ang2pix(nside, theta, phi, nest=True)

            # Add the pixel index dataset to the HDF5 file
            io.append_dataset(out_f, f"pix{nside}", pix)
    out_f.close()

if __name__ == "__main__":
    # run main and keep track of time
    t0 = time.time()
    main()
    t1 = time.time()
    logger.info(f"Total run time: {t1 - t0}")
    logger.info("Done!")