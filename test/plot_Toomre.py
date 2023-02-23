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
    """ Read in rslices and plot the Toomre diagram"""
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
            'vx_true', 'vy_true', 'vz_true',
            'parallax_over_error', 'radial_velocity', 'feh'
        )
    else:
        LOGGER.info('Use error-convolved values')
        keys = (
            'l', 'b', 'parallax', 'pml', 'pmb', 'radial_velocity', 'feh',
            'parallax_over_error',
        )

    # Read in data
    data = io.read_rslice(keys, gal, lsr, rslice,
        basedir=envs.DR3_BASEDIR, ijobs=range(Njob))

    # Select only data with POE > 10 and with radial velocity
    select = (
        (~np.isnan(data['radial_velocity']))
        & (data['parallax_over_error'] > 10)
    )
    data = {k: data[k][select] for k in data}

    # Calculate the perpendicular velocity and parallel velocity
    if use_true:
        vperp = np.sqrt(data['vx_true']**2 + data['vz_true']**2)
        vrot = data['vy_true'] + 224.7092
        feh = data['feh']
    else:
        # convert l, b, parallax, proper motions and radial velocity to Cartesian
        LOGGER.info('Convert l, b, parallax, proper motions, and RV to Cartesian')
        galactic = coord.Galactic(
            l=data['l'] * u.deg, b=data['b'] * u.deg,
            distance=coord.Distance(parallax=data['parallax'] * u.mas),
            pm_l_cosb=data['pml'] * u.mas / u.yr, pm_b=data['pmb'] * u.mas / u.yr,
            radial_velocity=data['radial_velocity'] * u.km / u.s
        )
        cartesian_d = galactic.cartesian.differentials['s']
        vx = cartesian_d.d_x.to_value(u.km / u.s)
        vy = cartesian_d.d_y.to_value(u.km / u.s)
        vz = cartesian_d.d_z.to_value(u.km / u.s)
        vperp = np.sqrt(vx**2 + vz**2)
        vrot = vy + 224.7092
        feh = data['feh']

    # Calculate 2D vperp and vrot distribution
    bins = (1000, 500)
    hist_range = ((-500, 500), (0, 500))
    # unweighted
    C, xedges, yedges = np.histogram2d(vrot, vperp, bins, range=hist_range)
    # weighted
    C_feh, xedges, yedges = np.histogram2d(
        vrot, vperp, bins, range=hist_range, weights=feh)
    C_feh = np.where(C > 0, C_feh / C, 0)
    # calculate grid and unit area
    X, Y = np.meshgrid(xedges, yedges)
    dx = xedges[1] - xedges[0]
    dy = yedges[1] - yedges[0]
    dA = dx * dy

    # Plot and save Toomre diagram
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))

    # plot unweighted Toomre diagram
    vmin = 1e0
    vmax = 1e3
    norm = mpl.colors.LogNorm(vmin=vmin, vmax=vmax, clip=False)
    C_new = C.copy() / dA
    C_new[C_new < vmin] = 0
    im = axes[0].pcolormesh(X, Y, C_new.T, norm=norm, shading='auto')
    axes[0].set_xlim(-500, 500)
    axes[0].set_ylim(0, 500)
    axes[0].set_xlabel(r'$V_Y$ [km/s]')
    axes[0].set_ylabel(r'$\sqrt{V_X^2 + V_Z^2}$ [km/s]')
    axes[0].set_xticks([-500, -250, 0, 250, 500])
    axes[0].set_yticks([100, 200, 300, 400])
    cbar = plt.colorbar(
        im, ax=axes[0], label='Counts (km/s)$^{-2}$',
        orientation="horizontal", pad=0.15
    )
    cbar.ax.xaxis.set_tick_params(which='both', direction='out')

    # plot weighted Toomre diagram
    vmin = -2
    vmax = 0.5
    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax, clip=False)
    C_new = C_feh.copy()
    C_new[C_new == 0] = -np.inf
    C_new[C_new < vmin] = vmin
    im = axes[1].pcolormesh(X, Y, C_new.T, cmap='magma', norm=norm, shading='auto')
    axes[1].set_xlim(-500, 500)
    axes[1].set_ylim(0, 500)
    axes[1].set_xlabel(r'$V_Y$ [km/s]')
    axes[1].set_ylabel(r'$\sqrt{V_X^2 + V_Z^2}$ [km/s]')
    axes[1].set_xticks([-500, -250, 0, 250, 500])
    axes[1].set_yticks([100, 200, 300, 400])
    cbar = plt.colorbar(
        im, ax=axes[1], label='mean $[\mathrm{Fe} / \mathrm{H}]$',
        orientation="horizontal", pad=0.15
    )
    cbar.ax.xaxis.set_tick_params(which='both', direction='out')

    if use_true:
        fig.suptitle(f'{gal} lsr-{lsr} rslice {rslice} true')
    else:
        fig.suptitle(f'{gal} lsr-{lsr} rslice {rslice}')

    output = os.path.join(plot_dir, 'toomre')
    if use_true:
        output += '_true'
    fig.savefig(output, dpi=300, bbox_inches='tight')


if __name__ == "__main__":
    FLAGS = parse_cmd()

    # run main and keep track of time
    t0 = time.time()
    main(FLAGS)
    t1 = time.time()

    LOGGER.info(f"Total run time: {t1 - t0}")
    LOGGER.info("Done!")

