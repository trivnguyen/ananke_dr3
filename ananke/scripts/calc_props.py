#!/usr/bin/env python

import os
import sys
import h5py
import argparse
import logging

from .. import coordinates, errors, extinction, io, flags, envs

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
    parser.add_argument('--ext-extrapolate', required=False, action='store_true',
                        help='Enable to extrapolate for extinction calculation')
    parser.add_argument('--err-extrapolate', required=False, action='store_true',
                        help='Enable to extrapolate for error calculation')
    parser.add_argument('--ext-var', required=False, default='bminr',
                        choices=('bminr', 'logteff'),
                        help='Variable to calculate extinction coefficient')
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
    """ Calculate catalog properties """
    gal = FLAGS.gal
    lsr = FLAGS.lsr
    rslice = FLAGS.rslice
    if LOGGER is None:
        LOGGER = set_logger()

    # get file information from galaxy, lsr, and rslice
    in_path = os.path.join(
        envs.DR3_PRESF_BASEDIR, f"{gal}/lsr-{lsr}",
        f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.{FLAGS.ijob}.hdf5")

    # Read in and calculate extinction magnitude
    LOGGER.info("Calculate extra coordinates, extincted magnitudes, and errors")
    LOGGER.info(f"In: {in_path}")

    with h5py.File(in_path, 'a') as f:
        # Add header
        f.attrs.update({
            "ext-extrapolate": FLAGS.ext_extrapolate,
            "err-extrapolate": FLAGS.err_extrapolate,
            "ext-var": FLAGS.ext_var,
        })

        N = len(f['dmod_true'])
        N_batch = (N + FLAGS.batch_size - 1) // FLAGS.batch_size

        for i_batch in range(N_batch):
            LOGGER.info(f'Progress [{i_batch}/{N_batch}]')
            i_start = i_batch * FLAGS.batch_size
            i_stop = i_start + FLAGS.batch_size
            indices = (i_start, i_stop)

            # coordinate conversion
            data = coordinates.calc_coords(f, indices=indices)
            io.append_dataset_dict(f, data, overwrite=False)

            # calculate extinction
            data = extinction.calc_extinction(
                f, indices=indices, ext_var=FLAGS.ext_var,
                extrapolate=FLAGS.ext_extrapolate)
            io.append_dataset_dict(f, data, overwrite=False)

            # calculate error
            data = errors.calc_errors(
                f, indices=indices, extrapolate=FLAGS.err_extrapolate)
            data['bp_rp'] = data['phot_bp_mean_mag'] - data['phot_rp_mean_mag']
            data['bp_g'] = data['phot_bp_mean_mag'] - data['phot_g_mean_mag']
            data['g_rp'] = data['phot_g_mean_mag'] - data['phot_rp_mean_mag']
            io.append_dataset_dict(f, data, overwrite=False)

            # calculate flags
            data = flags.calc_flags(
                f, indices=indices, ext_var=FLAGS.ext_var,
                ext_extrapolate=FLAGS.ext_extrapolate,
                err_extrapolate=FLAGS.err_extrapolate)
            io.append_dataset_dict(f, data, overwrite=False)

