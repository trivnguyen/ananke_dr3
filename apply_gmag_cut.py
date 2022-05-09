#!/usr/bin/env python

import os
import sys
import h5py
import argparse
import logging

import astropy
import astropy.units as u

from ananke import io

FLAGS = None
def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--in-file', required=True, help='Path to input file')
    parser.add_argument('--out-file', required=True, help='Path to output file')
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

    # Apply G magnitude cut to the mock catalog

    logger.info('Applying magnitude cut')
    logger.info(f'In  : {FLAGS.in_file}')
    logger.info(f'Dest: {FLAGS.out_file}')

    out_f = h5py.File(FLAGS.out_file, 'w')
    with h5py.File(FLAGS.in_file, 'r') as in_f:
        N = len(in_f['dmod_true'])
        N_batch = (N + FLAGS.batch_size - 1) // FLAGS.batch_size

        for i_batch in range(N_batch):
            logger.info(f'Progress [{i_batch}/{N_batch}]')
            i_start = i_batch * FLAGS.batch_size
            i_stop = i_start + FLAGS.batch_size

            # Get G magnitude
            g_mag = in_f['phot_g_mean_mag_abs'][i_start: i_stop]
            select = (3 <= g_mag) & (g_mag <= 21)
            for key, val in in_f.items():
                io.append_dataset(out_f, key, val[i_start: i_stop][select])
    out_f.close()
    logger.info('Done')


