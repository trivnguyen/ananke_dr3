#!/usr/bin/env python

import os
import sys
import argparse
import logging
import time

import numpy as np
import astropy.units as u
import astropy.coordinates as coord
import matplotlib as mpl
import matplotlib.pyplot as plt

plt.style.use('/scratch/05328/tg846280/FIRE_Public_Simulations/matplotlib_style/ananke.mplstyle')

from ananke import io, envs
import utils

FLAGS = None
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
LOGGER.addHandler(stream_handler)

def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gal', required=True, type=str)
    parser.add_argument('--lsr', required=True, type=str)
    parser.add_argument('--rslice', required=True, type=int)
    parser.add_argument('--Njob', required=False, type=int, default=1,
                        help='Number of indices.')
    parser.add_argument('--use-true', action='store_true',
                        help='Enable to use true coordinates.')
    return parser.parse_args()


def main(FLAGS):
    """ Read in rslices and plot the coordinate distribution """
    gal = FLAGS.gal
    lsr = FLAGS.lsr
    rslice =FLAGS.rslice
    Njob = FLAGS.Njob
    use_true = FLAGS.use_true
    plot_dir = os.path.join(
        utils.TEST_PLOT_BASEDIR, f'{gal}/lsr-{lsr}/rslice-{rslice}')
    os.makedirs(plot_dir, exist_ok=True)

    if use_true:
        LOGGER.info('Use true values')
        keys = (
            'px_true', 'py_true', 'pz_true', 'vx_true', 'vy_true', 'vz_true'
        )
    else:
        LOGGER.info('Use error-convolved values')
        keys = (
            'l', 'b', 'parallax', 'pml', 'pmb', 'radial_velocity'
        )

    # read in data
    data = io.read_rslice(keys, gal, lsr, rslice,
        basedir=envs.DR3_BASEDIR, ijobs=range(Njob))

    if use_true:
        px = data['px_true']
        py = data['py_true']
        pz = data['pz_true']
        vx = data['vx_true']
        vy = data['vy_true']
        vz = data['vz_true']
    else:
        # convert l, b, parallax, proper motions and radial velocity to Cartesian
        # first, select only stars with radial velocity
        select = (~np.isnan(data['radial_velocity']))
        data = {k: data[k][select] for k in data}

        LOGGER.info('Convert l, b, parallax, proper motions, and RV to Cartesian')
        galactic = coord.Galactic(
            l=data['l'] * u.deg, b=data['b'] * u.deg,
            distance=coord.Distance(parallax=data['parallax'] * u.mas),
            pm_l_cosb=data['pml'] * u.mas / u.yr, pm_b=data['pmb'] * u.mas / u.yr,
            radial_velocity=data['radial_velocity'] * u.km / u.s
        )
        cartesian = galactic.cartesian
        cartesian_d = cartesian.differentials['s']
        px = cartesian.x.to_value(u.kpc)
        py = cartesian.y.to_value(u.kpc)
        pz = cartesian.z.to_value(u.kpc)
        vx = cartesian_d.d_x.to_value(u.km / u.s)
        vy = cartesian_d.d_y.to_value(u.km / u.s)
        vz = cartesian_d.d_z.to_value(u.km / u.s)

    # plot and save position distributions
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True, sharex=True)
    bins = 50
    axes[0].hist(px, bins, histtype='step', lw=2)
    axes[1].hist(py, bins, histtype='step', lw=2)
    axes[2].hist(pz, bins, histtype='step', lw=2)
    axes[0].set_xlabel(r'$x [\mathrm{kpc}]$')
    axes[1].set_xlabel(r'$y [\mathrm{kpc}]$')
    axes[2].set_xlabel(r'$z [\mathrm{kpc}]$')
    axes[0].set_ylabel(r'frequency')
    if use_true:
        fig.suptitle(f'{gal} lsr-{lsr} rslice {rslice} true')
    else:
        fig.suptitle(f'{gal} lsr-{lsr} rslice {rslice}')

    output = os.path.join(plot_dir, 'pos_dist')
    if use_true:
        output += '_true'
    fig.savefig(output, dpi=300, bbox_inches='tight')

    # plot and save velocity distributions
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True, sharex=True)
    bins = 50
    axes[0].hist(vx, bins, histtype='step', lw=2)
    axes[1].hist(vy, bins, histtype='step', lw=2)
    axes[2].hist(vz, bins, histtype='step', lw=2)
    axes[0].set_xlabel(r'$v_x [\mathrm{km/s}]$')
    axes[1].set_xlabel(r'$v_y [\mathrm{km/s}]$')
    axes[2].set_xlabel(r'$v_z [\mathrm{km/s}]$')
    axes[0].set_ylabel(r'frequency')
    if use_true:
        fig.suptitle(f'{gal} lsr-{lsr} rslice {rslice} true')
    else:
        fig.suptitle(f'{gal} lsr-{lsr} rslice {rslice}')

    output = os.path.join(plot_dir, 'vel_dist')
    if use_true:
        output += '_true'
    fig.savefig(os.path.join(plot_dir, output), dpi=300, bbox_inches='tight')


if __name__ == "__main__":
    FLAGS = parse_cmd()

    # run main and keep track of time
    t0 = time.time()
    main(FLAGS)
    t1 = time.time()

    LOGGER.info(f"Total run time: {t1 - t0}")
    LOGGER.info("Done!")

