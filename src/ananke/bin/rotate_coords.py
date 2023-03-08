#!/usr/bin/env python

import argparse
import h5py
import os
import time

import numpy as np
import astropy.coordinates as coord
import astropy.units as u

from ananke import photometric_utils, io, config
from ananke.logger import logger

FLAGS = None

def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gal', required=True, type=str)
    parser.add_argument('--lsr', required=True, type=int)
    parser.add_argument('--rslice', required=True, type=int)
    parser.add_argument('--ijob', type=int, default=0, help='Job index')
    parser.add_argument('--Njob', type=int, default=1, help='Total number of jobs')
    parser.add_argument('--batch-size', required=False, type=int, default=1000000,
                        help='Batch size')
    return parser.parse_args()

def rotate_coords_ananke(x, lsr):
    """ Rotate coordinate based on LSR """
    # rotation depends on which LSR
    pos_lsr = {
        0: (0.0, 8.2, 0.0),
        1: (-7.1014, -4.1, 0.0),
        2: (7.1014, -4.1, 0.0)
    }

    # rotate coordinate
    phi = np.pi + np.arctan2(pos_lsr[lsr][1], pos_lsr[lsr][0])
    rot = np.array([
        [np.cos(phi), np.sin(phi), 0.0],
        [-np.sin(phi), np.cos(phi), 0.0],
        [0.0, 0.0, 1.0]
    ])
    x_rot = np.dot(x, rot.T)
    return x_rot

def calc_new_coords(data, lsr, indices=(None, None)):
    """ Calculate new astrometric coordinates """
    istart, istop = indices
    px_true = data['px_true'][istart: istop]
    py_true = data['py_true'][istart: istop]
    pz_true = data['pz_true'][istart: istop]
    vx_true = data['vx_true'][istart: istop]
    vy_true = data['vy_true'][istart: istop]
    vz_true = data['vz_true'][istart: istop]

    # rotate coordinate
    px_rot, py_rot, pz_rot = rotate_coords_ananke(
        np.stack([px_true, py_true, pz_true], 1), lsr).T
    vx_rot, vy_rot, vz_rot = rotate_coords_ananke(
        np.stack([vx_true, vy_true, vz_true], 1), lsr).T

    # coordinate conversion
    gc = coord.Galactic(
        u=px_rot * u.kpc, v=py_rot * u.kpc, w=pz_rot * u.kpc,
        U=vx_rot * u.km / u.s, V=vy_rot * u.km / u.s, W=vz_rot * u.km / u.s,
        representation_type=coord.CartesianRepresentation,
        differential_type=coord.CartesianDifferential)
    icrs = gc.transform_to(coord.ICRS())

    # new coordinates
    new_data = {}
    new_data['px_true'] = px_rot
    new_data['py_true'] = py_rot
    new_data['vx_true'] = vx_rot
    new_data['vy_true'] = vy_rot
    new_data['ra_true'] = icrs.ra.to_value(u.deg)
    new_data['dec_true'] = icrs.dec.to_value(u.deg)
    new_data['l_true'] = gc.spherical.lon.to_value(u.deg)
    new_data['b_true'] = gc.spherical.lat.to_value(u.deg)

    return new_data

def main(FLAGS):
    """ Rotate Ananke coordinate """
    gal = FLAGS.gal
    lsr = FLAGS.lsr
    rslice = FLAGS.rslice

    # get file information from galaxy, lsr, and rslice
    in_path = os.path.join(
        config.DR3_PRESF_BASEDIR, f"{gal}/lsr-{lsr}",
        f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.{FLAGS.ijob}.hdf5")

    # Compute new astrometric coordinates
    logger.info("Rotate coordinate")
    logger.info(f"In  : {in_path}")

    with h5py.File(in_path, 'a') as f:
        N = len(f['dmod_true'])
        N_batch = (N + FLAGS.batch_size - 1) // FLAGS.batch_size

        for i_batch in range(N_batch):
            logger.info(f'Progress [{i_batch}/{N_batch}]')
            i_start = i_batch * FLAGS.batch_size
            i_stop = i_start + FLAGS.batch_size
            indices = (i_start, i_stop)
            new_data = calc_new_coords(f, lsr, indices=indices)
            for key in new_data:
                f[key][i_start: i_stop] = new_data[key]

if __name__ == "__main__":
    FLAGS = parse_cmd()

    # run main and keep track of time
    t0 = time.time()
    main(FLAGS)
    t1 = time.time()
    logger.info(f"Total run time: {t1 - t0}")
    logger.info("Done!")

