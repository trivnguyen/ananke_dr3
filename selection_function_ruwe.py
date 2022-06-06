#!/usr/bin/env python

import os
import sys
import h5py
import pickle
import argparse
import logging

import numpy as np

import selectionfunctions.cog_ii as CoGII
import selectionfunctions.cog_v as CoGV
from selectionfunctions.config import config
from selectionfunctions.source import Source
from selectionfunctions.map import coord2healpix

from ananke import io

FLAGS = None
def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--in-file', required=True, help='Path to input file')
    parser.add_argument('--out-file', required=True, help='Path to output file')
    parser.add_argument('--random-state', required=True,
                        help='Path to random state. If not exist, create one.')
    parser.add_argument(
        '--selection', required=True, nargs='*',
        help='Selection maps to apply; Available options are [general, astrometry, ruwe1p4, rvs]')
    parser.add_argument(
        '--sf-data-dir', required=True, help='Path to selection function data directory')
    parser.add_argument(
        '--batch-size', required=False, type=int, default=1000000, help='Batch size')

    return parser.parse_args()

def set_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger

def selection_function(
    ra, dec, gmag, rpmag, output, prng,
    sf_subset_map, sf_type, sf_general_map, selec_data={}):
    # Check that the selection is in one of the four options
    if not sf_type in ['general', 'astrometry', 'ruwe1p4', 'rvs']:
        raise ValueError("Selection type unrecognized."/
        "Available options are [general, astrometry, ruwe1p4, rvs]")

    # Pre-compute color needed for selection function
    g_grp_mag = gmag-rpmag

    # Pre-compute the index of data that requires manual adjustment in fitting ruwe1p4 and RVS selection functions
    if sf_type == 'ruwe1p4':
        G_GRP_floor = -1.
        G_GRP_ceil = 7.
        id_G_GRP_ruwe_l = np.where(g_grp_mag < G_GRP_floor)[0]
        id_G_GRP_ruwe_u = np.where(g_grp_mag > G_GRP_ceil)[0]

        logger.info(
            f"{len(id_G_GRP_ruwe_l} sources found to have color redder than RUWE1p4 edge")
        logger.info(
            f"{len(id_G_GRP_ruwe_u} sources found to have color bluer than RUWE1p4 edge")

        # Manually set the out of bound colors to the closest bin value
        g_grp_mag[id_G_GRP_ruwe_l] = G_GRP_floor + 0.1 # Add a margin to prevent numerical error
        g_grp_mag[id_G_GRP_ruwe_u] = G_GRP_ceil - 0.1


    # Set up the source object for selection functions
    source = Source(ra=ra, dec=dec, unit='deg', frame='icrs',
                    photometry={'gaia_g':gmag,'gaia_g_gaia_rp':g_grp_mag})

    # Find the expected number of observaitons if not already found
    if ('n_transit' in selec_data.keys()) == False:
        # Get healpix pixels
        hpxidx = coord2healpix(source.coord, 'icrs', sf_general_map._nside, nest=True)
        # Get number of transits from scanning law. The healpix id has to be in icrs coordinate
        selec_data['n_transit'] = sf_general_map._n_field[hpxidx]

    # Set the key names for the selection probability and selected flag
    col_prob = 'prob_' + sf_type
    col_selected = 'selected_' + sf_type

    # Apply selection functions
    if sf_type == 'general':
        selec_data[col_prob] = sf_general_map(source)
        selec_data[col_selected] = prng.rand(len(selec_data[col_prob]))<selec_data[col_prob]
    # Find the selection probability and use random sampling for
    # whether the object is selected in subsets of the sample
    else:
        selec_data[col_prob] = sf_general_map(source)*sf_subset_map(source)
        selec_data[col_selected] = prng.rand(len(selec_data[col_prob]))<selec_data[col_prob]

    # Remove any RVS sources that fall outside of the applicable color range
    if sf_type == 'rvs':
        G_GRP_floor = -0.6
        G_GRP_ceil = 2.6
        id_G_GRP_rvs = np.where((g_grp_mag < G_GRP_floor) | (g_grp_mag > G_GRP_ceil))[0]

        logger.info(
            f"{len(id_G_GRP_rvs)} sources found to have color redder/bluer than RVS sf edge.")

        selec_data['prob_rvs'][id_G_GRP_rvs] = 0
        selec_data['selected_rvs'][id_G_GRP_rvs] = False

    # Make sure that we remove G < 3 stars as the selection functions are dominated by the prior there
    id_G_mag_u = np.where(gmag < 3)[0]
    selec_data[col_selected][id_G_mag_u] = False

    return selec_data


if __name__ == '__main__':
    ''' Make a synthetic survey from an extincted mock and selection functions '''

    # Parse cmd
    FLAGS = parse_cmd()
    logger = set_logger()

    # Define the path to selection function maps
    config['data_dir'] = FLAGS.sf_data_dir

    # Fetch data
    print("Fetching data...")
    CoGII.fetch()
    CoGV.fetch(version='cog_v', subset='astrometry')
    CoGV.fetch(version='cog_v', subset='ruwe1p4')
    CoGV.fetch(version='cog_v', subset='rvs')

    # Load the general map
    print("Loading general selection function...")
    sf_general_map = CoGII.dr3_sf(version='modelAB',crowding=True)

    sf_subset_maps = []
    # Load the necessary subset maps
    for j_subset in FLAGS.selection:
        if j_subset == 'general':
            continue
        logger.info(f"Loading {j_subset} selection function...")
        sf_subset_maps.append(CoGV.subset_sf(
            map_fname=j_subset+'_cogv.h5', nside=32,
            basis_options={'needlet':'chisquare', 'p':1.0, 'wavelet_tol':1e-2},
            spherical_basis_directory='SphericalBasis'))

    # Overwrite file
    if os.path.exists(FLAGS.out_file):
        os.remove(FLAGS.out_file)

    # Open the files for read/write
    f = h5py.File(FLAGS.in_file, 'r')
    fo = h5py.File(FLAGS.out_file, 'a')
    N = len(f['dmod_true'])
    N_batch = (N + FLAGS.batch_size - 1) // FLAGS.batch_size

    logger.info(f'Total number of sources:{N}')

    # Save or load the random state
    if os.path.exists(FLAGS.random_state):
        logger.info(f"Random state found. Reading from: {FLAGS.random_state}")
        with open(FLAGS.random_state, 'rb') as frand:
            state = pickle.load(frand)
        prng = np.random.RandomState()
        prng.set_state(state)
    else:
        logger.info(f"Cannot find random state. Creating one")
        prng = np.random.RandomState()
        state = prng.get_state()
        with open(FLAGS.random_state, 'wb') as frand:
            pickle.dump(state, frand)

    # Apply selection function
    logger.info("Start selection function:")
    for i_batch in range(N_batch):
        logger.info(f'Batch: [{i_batch}/{N_batch}]')

        i_start = i_batch * FLAGS.batch_size
        i_stop = i_start + FLAGS.batch_size

        # read ra, dec, g mag, and rp mag
        ra = f['ra_true'][i_start: i_stop]
        dec = f['dec_true'][i_start: i_stop]
        gmag = f['phot_g_mean_mag'][i_start: i_stop]
        rpmag = f['phot_rp_mean_mag'][i_start: i_stop]

        selec_data = {}
        state_tmp = prng.get_state()
        for j_subset in range(len(FLAGS.selection)):
            # Reset the random state to what it is at the beginning of this batch
            # to guarantee consistent selection across subsets
            prng.set_state(state_tmp)
            selec_data = selection_function(
                ra=ra, dec=dec, gmag=gmag, rpmag=rpmag, output=fo, prng=prng,
                sf_subset_map=sf_subset_maps[j_subset], sf_type=FLAGS.selection[j_subset],
                sf_general_map=sf_general_map, selec_data=selec_data)

        # Reduce the size to only those selected for good ...
        # Count how many are left for this batch [xx: TBD]
        N_batch_selected = len(ra[selec_data['selected_ruwe1p4']])
        logger.info(f'Number of selected sources for this batch {N_batch_selected}')

        # Include the original and selection data columns
        data_slice = {}

        # Create an index list for identifying what stars are selected
        index_selec = np.arange(i_start, i_start+len(selec_data['selected_ruwe1p4']))
        data_slice['index_in_mock'] = index_selec[selec_data['selected_ruwe1p4']]

        for key in f.keys():
            data_slice[key] = f[key][i_start: i_stop][selec_data['selected_ruwe1p4']]

        for key in selec_data.keys():
            data_slice[key] = selec_data[key][selec_data['selected_ruwe1p4']]
        io.append_dataset_dict(fo, data_slice, overwrite=False)

    f.close()
    fo.close()
