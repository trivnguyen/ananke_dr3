#!/usr/bin/env python

import os
import sys
import h5py
import argparse
import logging

import astropy
import astropy.units as u

from ananke import coordinates, errors, extinction, io, flags

FLAGS = None
DEFAULT_BASEDIR = "/scratch/05328/tg846280/FIRE_Public_Simulations/ananke_dr3/"

def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gal', required=True, type=str)
    parser.add_argument('--lsr', required=True, type=str)
    parser.add_argument('--rslice', required=True, type=int)
    parser.add_argument('--ext-extrapolate', required=False, action='store_true',
                        help='Enable to extrapolate for extinction calculation')
    parser.add_argument('--err-extrapolate', required=False, action='store_true',
                        help='Enable to extrapolate for error calculation')
    parser.add_argument('--ext-var', required=False, default='bminr',
                        choices=('bminr', 'log_teff'),
                        help='Variable to calculate extinction coefficient')
    return parser.parse_args()

def set_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger


if __name__ == '__main__':
    """ Converting ebf file into multiple hdf5 files """
    FLAGS = parse_cmd()
    gal = FLAGS.gal
    lsr = FLAGS.lsr
    rslice = FLAGS.rslice
    logger = set_logger()

    in_file = os.path.join(
        DEFAULT_BASEDIR, f"{gal}_preSF/{lsr}/preSF/"\
        f"{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.hdf5")

    logger.info(f"Reading from {in_file}")

    # Read in and calculate extinction magnitude
    with h5py.File(in_file, 'a') as f:
        logger.info("Calculate new photometric errors")
        data = errors.photometric.calc_uncertainties(
            f, indices=(None, None), extrapolate=FLAGS.err_extrapolate)
        data['bp_rp'] = data['phot_bp_mean_mag'] - data['phot_rp_mean_mag']
        data['bp_g'] = data['phot_bp_mean_mag'] - data['phot_g_mean_mag']
        data['g_rp'] = data['phot_g_mean_mag'] - data['phot_rp_mean_mag']

        logger.info("Replacing fields")

        for key in data:
            logger.info(key)
            if f.get(key) is not None:
                del f[key]
            f.create_dataset(key, data=data[key])

    logger.info('Done')

