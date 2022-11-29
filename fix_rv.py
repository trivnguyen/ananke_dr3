#!/usr/bin/env python

import os
import sys
import h5py
import argparse
import logging

import numpy as np
import astropy
import astropy.units as u

from ananke import photometric_utils

FLAGS = None
DEFAULT_BASEDIR = "/scratch/05328/tg846280/FIRE_Public_Simulations/ananke_dr3/"

def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gal', required=True, type=str)
    parser.add_argument('--lsr', required=True, type=str)
    parser.add_argument('--rslice', required=True, type=int)
    parser.add_argument('--err-extrapolate', required=False, action='store_true',
                        help='Enable to extrapolate for error calculation')
    return parser.parse_args()

def set_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger

def calc_spectroscopic_errors(
        data, indices=(None, None), extrapolate=True):
    ''' Caculate spectroscopic error and error-convoled data '''
    i_start, i_stop = indices
    g_mag_true = data['phot_g_mean_mag_true'][i_start: i_stop]
    rp_mag_true = data['phot_rp_mean_mag_true'][i_start: i_stop]
    rv = data['radial_velocity_true'][i_start:i_stop]
    teff = 10**data['teff'][i_start:i_stop]

    # No PyGaia function for this yet; implementing calculation from Robyn's communication
    # rv_error = np.zeros_like(rv)
    # Calculate GRVS-G from G-GRP, error for RV
    grvs_true = photometric_utils.gminr_to_grvsminr(
        g_mag_true - rp_mag_true, extrapolate=extrapolate) + rp_mag_true
    rv_error = np.where(
        teff < 6500, 0.12 + 6.0 * np.exp(0.9*(grvs_true - 14.0)),
        0.4 + 20.0 * np.exp(0.8*(grvs_true - 12.75)))

#     # Calculate RV error correction
#     grvs_min = 8.0
#     grvs_true[grvs_true < grvs_min] = grvs_min
#     rv_error_corr = np.where(
#         grvs_true > 12.0, 16.554 - 2.4899 * grvs_true + 0.09933 * grvs_true**2,
#         0.318 + 0.3884 * grvs_true - 0.02778 * grvs_true**2)

    err_data = {}
    err_data['radial_velocity'] = np.random.normal(rv, rv_error)
    err_data['radial_velocity_error'] = rv_error
#     err_data['radial_velocity_error_corr_factor'] = rv_error_corr
    return err_data


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

    with h5py.File(in_file,'a') as f:
        # Calculate new RV errors
        logger.info('Calculate new RV errors')
        data = calc_spectroscopic_errors(
            f, indices=(None, None), extrapolate=True)

        logger.info('Replacing fields')
        try:
            del f['radial_velocity']
            del f['radial_velocity_error']
        except:
            logger.info('Error deleting')

        f.create_dataset('radial_velocity', data=data['radial_velocity'])
        f.create_dataset('radial_velocity_error', data=data['radial_velocity_error'])

    logger.info('Done')

