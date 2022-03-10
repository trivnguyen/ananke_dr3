#!/usr/bin/env python

# Import libraries
import os
import sys
import h5py
import argparse

import numpy as np
import pickle

from selectionfunctions.config import config
import selectionfunctions.cog_ii as CoGII
import selectionfunctions.cog_v as CoGV
from selectionfunctions.source import Source
from selectionfunctions.map import coord2healpix

from ananke import io

FLAGS = None
def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--in-file', required=True, help='Path to input file')
    parser.add_argument('--out-file', required=True, help='Path to output file')
    parser.add_argument('--random-state', required=True, nargs=2, metavar=('save/load', 'path'), 
                        help='Save or load random state with path to file')
    parser.add_argument('--selection', required=True, nargs='*', 
                        help='Selection maps to apply; Availabel options are [general, astrometry, ruwe1p4, rvs]')
    parser.add_argument('--batch-size', required=False, type=int, default=1000000,
                        help='Batch size')
    
    return parser.parse_args()


def selection_function(ra, dec, gmag, rpmag, output, prng, sf_subset_map, sf_type, sf_general_map, selec_data = {}):
    # Check that the selection is in one of the four options
    assert sf_type in ['general', 'astrometry', 'ruwe1p4', 'rvs'], "Selection type unrecognized. Availabel options are [general, astrometry, ruwe1p4, rvs]"
    
    # Pre-compute color needed for selection function
    g_grp_mag = gmag-rpmag

    # Pre-compute the index of data that requires manual adjustment in fitting ruwe1p4 and RVS selection functions
    if sf_type == 'ruwe1p4':
        G_GRP_floor = -1.
        G_GRP_ceil = 7.
        id_G_GRP_ruwe_l = np.where(g_grp_mag < G_GRP_floor)[0]
        id_G_GRP_ruwe_u = np.where(g_grp_mag > G_GRP_ceil)[0]
        print(len(id_G_GRP_ruwe_l),"sources found to have color redder than ruwe1p4 sf edge.")
        print(len(id_G_GRP_ruwe_u),"sources found to have color bluer than ruwe1p4 sf edge.")
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
    # Find the selection probability and use random sampling for whether the object is selected in subsets of the sample
    else:
        selec_data[col_prob] = sf_general_map(source)*sf_subset_map(source)
        selec_data[col_selected] = prng.rand(len(selec_data[col_prob]))<selec_data[col_prob]
    
    # Remove any RVS sources that fall outside of the applicable color range
    if sf_type == 'rvs':
        G_GRP_floor = -0.6
        G_GRP_ceil = 2.6
        id_G_GRP_rvs = np.where((g_grp_mag < G_GRP_floor) | (g_grp_mag > G_GRP_ceil))[0]
        print(len(id_G_GRP_rvs),"sources found to have color redder/bluer than RVS sf edge.")
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
    
    # Define the path to selection function maps
    config['data_dir'] = '../selectionfunction_data/' # Change this line to where you want to store the selection function maps

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
        print(f"Loading {j_subset} selection function...")
        sf_subset_maps.append(CoGV.subset_sf(map_fname=j_subset+'_cogv.h5', nside=32,
                                             basis_options={'needlet':'chisquare', 'p':1.0, 'wavelet_tol':1e-2},
                                             spherical_basis_directory='SphericalBasis'))
    
    # Overwrite file
    if os.path.exists(FLAGS.out_file):
        os.remove(FLAGS.out_file)
    
    # Open the files for read/write
    f = h5py.File(FLAGS.in_file, 'r')
    fo = h5py.File(FLAGS.out_file, 'a')
    N = len(f['dmod_true'])
    print(f'Total number of sources:{N}')
    N_batch = (N + FLAGS.batch_size - 1) // FLAGS.batch_size


    # Save or load the random state
    if FLAGS.random_state[0] == 'save':
        print("Saving random state")
        prng = np.random.RandomState()
        state = prng.get_state()
        with open(FLAGS.random_state[1], 'wb') as frand: 
            pickle.dump(state, frand)
    elif FLAGS.random_state[0] == 'load':
        print('Loading random state')
        with open(FLAGS.random_state[1], 'rb') as frand:
            state = pickle.load(frand)
        prng = np.random.RandomState()
        prng.set_state(state)
    else:
        print('Unexpected save/load instruction for random state')
        sys.exit()
    
    
    # Apply selection function
    for i_batch in range(N_batch):
        print(f'[{i_batch}/{N_batch}]')

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
            # Reset the random state to what it is at the beginning of this batch to guarantee consistent selection across subsets
            prng.set_state(state_tmp)
            selec_data = selection_function(ra, dec, gmag, rpmag, fo, prng, 
                                            sf_subset_maps[j_subset], sf_type = FLAGS.selection[j_subset], sf_general_map, selec_data)
        # Reduce the size to only those selected for good ...
        # Count how many are left for this batch [xx: TBD]
        N_batch_selected = len(ra[selec_data['selected_ruwe1p4']])
        print(f'Number of selected sources for this batch {N_batch_selected}')
        # Include the original and selection data columns
        data_slice = {}

        # Create an index list for identifying what stars are selected
        index_selec = np.arange(i_start, i_start+len(selec_data[xx]))
        data_slice['index_in_mock'] = index_selec[selec_data[xx]]

        for key in data.keys():
            data_slice[key] = data[key][i_start: i_stop][selec_data[xx]]

        for key in selec_data.keys():
            data_slice[key] = selec_data[key][selec_data[xx]]
        io.append_dataset_dict(output, data_slice, overwrite=False)
        
    
    f.close()
    fo.close()