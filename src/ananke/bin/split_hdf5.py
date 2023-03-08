#!/usr/bin/env python

import argparse
import h5py
import os
import time

from ananke import config
from ananke.logger import logger

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
    return parser.parse_args()

def main(FLAGS):
    """ Split HDF5 file into multiple files """
    gal = FLAGS.gal
    lsr = FLAGS.lsr
    rslice = FLAGS.rslice
    ijob = FLAGS.ijob
    Njob = FLAGS.Njob

    in_path = os.path.join(
        config.HDF5_BASEDIR, f"{gal}/lsr-{lsr}/",
        f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.hdf5")
    out_path = os.path.join(
        config.HDF5_BASEDIR, f"{gal}/lsr-{lsr}/",
        f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.{ijob}.hdf5")

    f_out = h5py.File(out_path, 'w')
    with h5py.File(in_path, 'r') as f_in:
        num_samples = len(f_in['dmod_true'])
        start = int(num_samples / Njob * ijob)
        stop = int(num_samples / Njob * (ijob + 1))
        for key in f_in.keys():
            f_out.create_dataset(key, data=f_in[key][start: stop])
    f_out.close()

if __name__ == "__main__":
    FLAGS = parse_cmd()

    # run main and keep track of time
    t0 = time.time()
    main(FLAGS)
    t1 = time.time()
    logger.info(f"Total run time: {t1 - t0}")
    logger.info("Done!")
