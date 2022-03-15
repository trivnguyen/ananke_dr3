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
    parser.add_argument('--mock-file', required=True, help='Path to mock file')
    parser.add_argument('--ext-file', required=True, help='Path to extinction file')
    parser.add_argument('--out-file', required=True, help='Path to output file')
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


if __name__ == '__main__':
    """ Converting ebf file into multiple hdf5 files """
    FLAGS = parse_cmd()

    logger = set_logger()

    logger.info('Create mock catalog with settings:')
    logger.info(f'Job: [{FLAGS.ijob} / {FLAGS.Njob}]')
    logger.info(f'Batch size: {FLAGS.batch_size}')
    logger.info(f'Mock file      : {FLAGS.mock_file}')
    logger.info(f'Extinction file: {FLAGS.ext_file}')
    logger.info(f'Output file    : {FLAGS.out_file}')

    if os.path.exists(FLAGS.out_file):
        logger.warning(f'Overwriting {FLAGS.out_file}')
        os.remove(FLAGS.out_file)

    # Converting EBF to HDF5
    logger.info('Convert EBF to HDF5')
    io.ebf_to_hdf5_split(
        FLAGS.mock_file, FLAGS.out_file, conversion.ALL_MOCK_KEYS,
        FLAGS.ijob, FLAGS.Njob, FLAGS.batch_size)
    io.ebf_to_hdf5_split(
        FLAGS.ext_file, FLAGS.out_file, conversion.ALL_EXT_KEYS,
        FLAGS.ijob, FLAGS.Njob, FLAGS.batch_size)

    # Read in and calculate extinction magnitude
    logger.info('Calculate extra coordinates, extincted magnitudes, and errors')
    with h5py.File(FLAGS.out_file, 'a') as f:
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
            data = extinction.calc_extinction(f, indices=indices)
            io.append_dataset_dict(f, data, overwrite=False)

            # calculate error
            data = errors.calc_errors(f, indices=indices)
            io.append_dataset_dict(f, data, overwrite=False)

    logger.info('Done')

