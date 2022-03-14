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
    parser.add_argument('--mock-file', required=True, help='Path to mock file')
    parser.add_argument('--ext-file', required=True, help='Path to extinction file')
    parser.add_argument('--out-file', required=True, help='Path to output file')
    parser.add_argument('--ijob', type=int, default=0, help='Job index')
    parser.add_argument('--Njob', type=int, default=1, help='Total number of jobs')
    parser.add_argument('--batch-size', required=False, type=int, default=1000000,
                        help='Batch size')
    return parser.parse_args()


if __name__ == '__main__':
    """ Converting ebf file into multiple hdf5 files """
    FLAGS = parse_cmd()

    if os.path.exists(FLAGS.out_file):
        os.remove(FLAGS.out_file)

    io.ebf_to_hdf5_split(
        FLAGS.mock_file, FLAGS.out_file, conversion.ALL_MOCK_KEYS,
        FLAGS.ijob, FLAGS.Njob, FLAGS.batch_size)
    io.ebf_to_hdf5_split(
        FLAGS.ext_file, FLAGS.out_file, conversion.ALL_EXT_KEYS,
        FLAGS.ijob, FLAGS.Njob, FLAGS.batch_size)

    # Read in and calculate extinction magnitude
    print('Calculate extra coordinates, extincted magnitudes, and errors')
    with h5py.File(FLAGS.out_file, 'a') as f:
        N = len(f['dmod_true'])
        N_batch = (N + FLAGS.batch_size - 1) // FLAGS.batch_size

        for i_batch in range(N_batch):
            print(f'[{i_batch}/{N_batch}]')
            i_start = i_batch * FLAGS.batch_size
            i_stop = i_start + FLAGS.batch_size
            indices = (i_start, i_stop)

            # coordinate conversion
            #print('calculate coordinates')
            data = coordinates.calc_coords(f, indices=indices)
            io.append_dataset_dict(f, data, overwrite=False)

            # calculate extinction
            #print('calculate extincted magnitude')
            data = extinction.calc_extinction(f, indices=indices)
            io.append_dataset_dict(f, data, overwrite=False)

            # calculate error
            # print('calculate error')
            data = errors.calc_errors(f, indices=indices)
            io.append_dataset_dict(f, data, overwrite=False)

            # calculate the error-convolved angle and proper motion in Galactic coord
            # NOTE: this does NOT return the error in Galactic coord
            #data = coordinates.icrs_to_gal(f, postfix='', indices=(i_start, i_stop))
            #io.append_dataset_dict(f, data, overwrite=False)

    print('Done')

