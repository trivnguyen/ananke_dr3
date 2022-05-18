#!/usr/bin/env python

import os
import sys
import h5py
import argparse
import logging

import astropy
import astropy.units as u

from ananke import coordinates, conversion, errors, extinction, io

FLAGS = None
def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--in-file', required=True, help='Path to output file')
    parser.add_argument('--extrapolate', required=False, action='store_true',
                        help='Enable to extrapolate')
    parser.add_argument('--extinction-var', required=False, default='bminr', choices=('bminr', 'log_teff'),
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


if __name__ == '__main__':
    """ Converting ebf file into multiple hdf5 files """
    FLAGS = parse_cmd()

    logger = set_logger()

    # Read in and calculate extinction magnitude
    logger.info('Calculate extra coordinates, extincted magnitudes, and errors')
    with h5py.File(FLAGS.in_file, 'a') as f:
        N = len(f['dmod_true'])
        N_batch = (N + FLAGS.batch_size - 1) // FLAGS.batch_size

        for i_batch in range(N_batch):
            logger.info(f'Progress [{i_batch}/{N_batch}]')
            i_start = i_batch * FLAGS.batch_size
            i_stop = i_start + FLAGS.batch_size
            indices = (i_start, i_stop)

            # coordinate conversion
            data = coordinates.calc_coords(f, indices=indices)
            io.append_dataset_dict(f, data, overwrite=False)

            # calculate extinction
            data = extinction.calc_extinction(
                f, indices=indices, ext_var=FLAGS.extinction_var,
                extrapolate=FLAGS.extrapolate)
            io.append_dataset_dict(f, data, overwrite=False)

            # calculate error
            data = errors.calc_errors(f, indices=indices)
            io.append_dataset_dict(f, data, overwrite=False)

    logger.info('Done')

