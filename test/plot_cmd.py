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
    parser.add_argument(
        '--mode', required=False, default='error', type=str,
        choices=('error', 'true', 'int'),
        help='Magnitude type to plot')

    return parser.parse_args()


def main(FLAGS):
    """ Read in rslices and plot the Color Magnitude Diagram """
    gal = FLAGS.gal
    lsr = FLAGS.lsr
    rslice =FLAGS.rslice
    Njob = FLAGS.Njob
    mode = FLAGS.mode
    plot_dir = os.path.join(
        utils.TEST_PLOT_BASEDIR, f'{gal}/lsr-{lsr}/rslice-{rslice}')
    os.makedirs(plot_dir, exist_ok=True)

    if mode == 'true':
        LOGGER.info('Use true magnitudes')
        keys = (
            'phot_g_mean_mag_true', 'phot_bp_mean_mag_true', 'phot_rp_mean_mag_true',
            'parallax_over_error', 'parallax_true'
        )
    elif mode == 'error':
        LOGGER.info('Use error-convolved magnitudes')
        keys = (
            'phot_g_mean_mag', 'phot_bp_mean_mag', 'phot_rp_mean_mag',
            'parallax_over_error', 'parallax'
        )
    elif mode == 'int':
        LOGGER.info('Use intrinsic values')
        # by default, intrinsic value used true parallax
        keys = (
            'phot_g_mean_mag_int', 'phot_bp_mean_mag_int', 'phot_rp_mean_mag_int',
            'parallax_over_error', 'parallax_true'
        )

    # Read in data
    data = io.read_rslice(keys, gal, lsr, rslice,
        basedir=envs.DR3_BASEDIR, ijobs=range(Njob))

    # Select only data with POE > 10
    select = (data['parallax_over_error'] > 10)
    data = {k: data[k][select] for k in data}


    # Calculate the extincted, absolute magnitude
    if mode == 'true':
        # compute distance modulus and true magnitude
        dmod = coord.Distance(parallax=data['parallax_true'] * u.mas).distmod.value
        G_abs = data['phot_g_mean_mag_true'] - dmod
        Gbp_abs = data['phot_bp_mean_mag_true'] - dmod
        Grp_abs = data['phot_rp_mean_mag_true'] - dmod
    elif mode == 'error':
        dmod = coord.Distance(parallax=data['parallax'] * u.mas).distmod.value
        G_abs = data['phot_g_mean_mag'] - dmod
        Gbp_abs = data['phot_bp_mean_mag'] - dmod
        Grp_abs = data['phot_rp_mean_mag'] - dmod
    elif mode == 'int':
        dmod = coord.Distance(parallax=data['parallax_true'] * u.mas).distmod.value
        G_abs = data['phot_g_mean_mag_int'] - dmod
        Gbp_abs = data['phot_bp_mean_mag_int'] - dmod
        Grp_abs = data['phot_rp_mean_mag_int'] - dmod

    # Plot color-magnitude diagram
    fig, ax = plt.subplots(1, figsize=(8, 8))
    norm = mpl.colors.LogNorm(vmin=1, vmax=1e3)
    _, _, _, im = ax.hist2d(
        Gbp_abs - Grp_abs, G_abs, bins=1000,
        range=((-0.5, 5), (-7, 15)),
        cmin=1, norm=norm, cmap='magma')
    ax.invert_yaxis()
    ax.set_xlabel(r'$G_{BP} - G_{RP}$')
    ax.set_ylabel(r'$M_G$')
    cbar = plt.colorbar(im, ax=ax, label='counts $\mathrm{mag}^{-2}$')

    if mode == 'true':
        fig.suptitle(f'{gal} lsr-{lsr} rslice {rslice} extincted true')
    elif mode == 'error':
        fig.suptitle(f'{gal} lsr-{lsr} rslice {rslice} extincted')
    elif mode == 'int':
        fig.suptitle(f'{gal} lsr-{lsr} rslice {rslice} intrinsic')

    output = os.path.join(plot_dir, 'cmd')
    if mode == 'true':
        output += '_true'
    elif mode == 'int':
        output += '_int'
    fig.savefig(output, dpi=300, bbox_inches='tight')

if __name__ == "__main__":
    FLAGS = parse_cmd()

    # run main and keep track of time
    t0 = time.time()
    main(FLAGS)
    t1 = time.time()

    LOGGER.info(f"Total run time: {t1 - t0}")
    LOGGER.info("Done!")

