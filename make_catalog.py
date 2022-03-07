#!/usr/bin/env python

import os
import h5py
import argparse

import astropy
import astropy.units as u

from ananke import coordinates, conversion, errors, extinction, io

FLAGS = None
def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ext-file')
    parser.add_argument('--mock-file')
    parser.add_argument('--out-file')
    parser.add_argument('--batch-size', required=False, type=int, default=100000,
                        help='Batch size')
    return parser.parse_args()

if __name__ == '__main__':
    ''' Make a reduced mock catalog from a mock catalog file and an extinction file '''

    # Parse cmd
    FLAGS = parse_cmd()
    FLAGS.mock_file = "/scratch/07561/tg868605/gaia_mocks/m12i/test/lsr-2-rslice-0.m12i-res7100-md-sliced.ebf"
    FLAGS.ext_file = "/scratch/07561/tg868605/gaia_mocks/m12i/test/lsr-2-rslice-0.m12i-res7100-md-sliced.ext.ebf"
    FLAGS.out_file = 'test.hdf5'

    # Overwrite file
    if os.path.exists(FLAGS.out_file):
        os.remove(FLAGS.out_file)

    # First, convert the mock and extinct ebf file into a single hdf5 file
    io.ebf_to_hdf5(FLAGS.mock_file, FLAGS.out_file, keys=conversion.ALL_MOCK_KEYS,
                   batch_size=FLAGS.batch_size, overwrite=False)
    io.ebf_to_hdf5(FLAGS.ext_file, FLAGS.out_file, keys=conversion.ALL_EXT_KEYS,
                   batch_size=FLAGS.batch_size, overwrite=False)

    # Read in and calculate extinction magnitude
    with h5py.File(FLAGS.out_file, 'a') as f:
        N = len(f['dmod_true'])
        N_batch = (N + FLAGS.batch_size - 1) // FLAGS.batch_size

        for i_batch in range(N_batch):
            print(f'[{i_batch}/{N_batch}]')

            i_start = i_batch * FLAGS.batch_size
            i_stop = i_start + FLAGS.batch_size

            # coordinate conversion
            #print('calculate coordinates')
            data = coordinates.calc_coords(f, indices=(i_start, i_stop))
            io.append_dataset_dict(f, data, overwrite=False)

            # calculate extinction
            #print('calculate extincted magnitude')
            data = extinction.calc_extinction(f, indices=(i_start, i_stop))
            io.append_dataset_dict(f, data, overwrite=False)

            # calculate error
            # print('calculate error')
            data = {}
            data.update(errors.calc_astrometric_errors(f, indices=(i_start, i_stop)))
            data.update(errors.calc_photometric_errors(f, indices=(i_start, i_stop)))
            data.update(errors.calc_spectroscopic_errors(f, indices=(i_start, i_stop)))
            io.append_dataset_dict(f, data, overwrite=False)

