#!/usr/bin/env python

import os
import sys
import h5py
import argparse
import logging

import numpy as np
import astropy
import astropy.coordinates as coord
import astropy.units as u

from ananke import photometric_utils, errors, io

FLAGS = None
DEFAULT_BASEDIR = "/scratch/05328/tg846280/FIRE_Public_Simulations/ananke_dr3/"

def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gal', required=True, type=str)
    parser.add_argument('--lsr', required=True, type=str)
    parser.add_argument('--rslice', required=True, type=int)
    parser.add_argument('--num-batch', required=False, default=1, type=int)
    parser.add_argument('--use-backup', action='store_true')
    return parser.parse_args()

def set_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger

def rotate_coord_ananke(x, lsr):
    """ Rotate coordinate """

    # rotation depends on which LSR
    if lsr == 'lsr-0':
        pos_lsr = (0.0, 8.2, 0.0)
    elif lsr == 'lsr-1':
        pos_lsr = (-7.1014, -4.1, 0.0)
    elif lsr == 'lsr-2':
        pos_lsr = (7.1014, -4.1, 0.0)
    else:
        raise ValueError(f'lsr must be "lsr-0", "lsr-1", "lsr-2", not {lsr}')

    # rotate coordinate
    phi = np.pi + np.arctan2(pos_lsr[1], pos_lsr[0])
    rot = np.array([
        [np.cos(phi), np.sin(phi), 0.0],
        [-np.sin(phi), np.cos(phi), 0.0],
        [0.0, 0.0, 1.0]
    ])
    x_rot = np.dot(x, rot.T)
    return x_rot

def calc_new_coord(data, lsr, indices=(None, None)):
    """ Calculate new astrometric coordinates """
    istart, istop = indices
    px_true = data['px_true'][istart: istop]
    py_true = data['py_true'][istart: istop]
    pz_true = data['pz_true'][istart: istop]
    vx_true = data['vx_true'][istart: istop]
    vy_true = data['vy_true'][istart: istop]
    vz_true = data['vz_true'][istart: istop]

    # rotate coordinate
    px_rot, py_rot, pz_rot = rotate_coord_ananke(
        np.stack([px_true, py_true, pz_true], 1), lsr).T
    vx_rot, vy_rot, vz_rot = rotate_coord_ananke(
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
    new_data['l_true'] = gc.spherical.lon.to_value(u.deg)
    new_data['ra_true'] = icrs.ra.to_value(u.deg)
    new_data['dec_true'] = icrs.dec.to_value(u.deg)
    new_data['pmra_true'] = icrs.pm_ra_cosdec.to_value(u.mas / u.yr)
    new_data['pmdec_true'] = icrs.pm_dec.to_value(u.mas / u.yr)

    return new_data

if __name__ == '__main__':
    """ Fix all astrometric coordinates and RV """
    FLAGS = parse_cmd()
    LOGGER= set_logger()
    gal = FLAGS.gal
    lsr = FLAGS.lsr
    rslice = FLAGS.rslice
    use_backup = FLAGS.use_backup

    # Input pre-selection function file
    in_file = os.path.join(
        DEFAULT_BASEDIR, f"{gal}_preSF/{lsr}/preSF/"\
        f"{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.hdf5")
    backup_file = os.path.join(
        DEFAULT_BASEDIR, f"backup/{gal}/{lsr}/"\
        f"{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.hdf5")

    # Compute new astrometric coordinates
    LOGGER.info(f"Read from {in_file}...")
    LOGGER.info(f"Write to {backup_file}...")
    if not use_backup:
        with h5py.File(in_file, 'r') as f:
            with h5py.File(backup_file, 'w') as out_f:
                N = len(f['dmod_true'])
                N_batch = FLAGS.num_batch
                batch_size = int(np.ceil(N / N_batch))

                assert batch_size * N_batch >= N

                for i_batch in range(N_batch):
                    LOGGER.info(f'Progress [{i_batch}/{N_batch}]')
                    i_start = i_batch * batch_size
                    i_stop = i_start + batch_size
                    indices = (i_start, i_stop)

                    new_data = calc_new_coord(f, lsr, indices=indices)
                    io.append_dataset_dict(out_f, new_data, overwrite=False)

    # Read backup file and replace field
    with h5py.File(in_file, 'a') as f:
        with h5py.File(backup_file, 'r') as out_f:
            for key in out_f:
                if f.get(key) is not None:
                    del f[key]
                f.create_dataset(key, data=out_f[key][:])

    # Calculate astrometric errors
    LOGGER.info(f"Calculate error")
    with h5py.File(in_file, 'a') as f:
        N = len(f['dmod_true'])
        N_batch = FLAGS.num_batch
        batch_size = int(np.ceil(N / N_batch))

        assert batch_size * N_batch >= N

        for i_batch in range(N_batch):
            LOGGER.info(f'Progress [{i_batch}/{N_batch}]')
            i_start = i_batch * batch_size
            i_stop = i_start + batch_size
            indices = (i_start, i_stop)

            # Calculate astrometric error excluding parallax
            err_data = errors.astrometric.calc_uncertainties(
                f, indices=indices)
            del err_data['parallax']
            del err_data['parallax_over_error']
            del err_data['parallax_error']

            overwrite = True if i_batch==0 else False
            io.append_dataset_dict(f, err_data, overwrite=overwrite)

    LOGGER.info('Done!')

