#!/usr/bin/env python

import argparse
import subprocess


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
    parser.add_argument('--mock-file', required=False, help='Path to mock file')
    parser.add_argument('--ext-file', required=False, help='Path to extinction file')
    parser.add_argument('--cache-file', required=False, help='Path to cache file')
    parser.add_argument('--out-file', required=True, help='Path to output file')
    parser.add_argument('--ijob', type=int, default=0, help='Job index')
    parser.add_argument('--Njob', type=int, default=1, help='Total number of jobs')
    parser.add_argument('--extrapolate', required=False, action='store_true',
                        help='Enable to extrapolate')
    parser.add_argument('--extinction-var', required=False, default='bminr', choices=('bminr', 'log_teff'),
                        help='Variable to calculate extinction coefficient')
    parser.add_argument('--batch-size', required=False, type=int, default=1000000,
                        help='Batch size')
    parser.add_argument('--skip-converting', action='store_true',
                        help='Skip converting from ebf to hdf5')
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
    if FLAGS.cache_file is None:
        temp_file = f'{FLAGS.out_file}.temp'
    else:
        temp_file = FLAGS.cache_file

    # Convert ebf to HDF5
    if not FLAGS.skip_converting:
        cmd = 'python convert_ebf_to_hdf5.py'\
            ' --mock-file {} --ext-file {} --out-file {} --ijob {} --Njob {} --batch-size {}'
        cmd = cmd.format(FLAGS.mock_file, FLAGS.ext_file, temp_file,
                         FLAGS.ijob, FLAGS.Njob, FLAGS.batch_size)
        logger.info(f'Running {cmd}')
        subprocess.check_call(cmd.split(' '))
    else:
        logger.info(f'Skip converting')

    # Convert ebf to HDF5
    cmd = 'python apply_gmag_cut.py --in-file {} --out-file {}'
    cmd = cmd.format(temp_file, FLAGS.out_file)
    logger.info(f'Running {cmd}')
    subprocess.check_call(cmd.split(' '))

    # Convert ebf to HDF5
    cmd = 'python calculate_properties.py --in-file {} --extinction-var {}'
    if FLAGS.extrapolate:
        cmd += ' --extrapolate'
    cmd = cmd.format(FLAGS.out_file, FLAGS.extinction_var)
    logger.info(f'Running {cmd}')
    subprocess.check_call(cmd.split(' '))

