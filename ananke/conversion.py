
from astropy.coordinates import Distance

ALL_MOCK_KEYS = {
    'parentid': 'parentid',
    'partid': 'partid',
    'ra': 'ra_true',
    'dec': 'dec_true',
    'glon': 'l_true',
    'glat': 'b_true',
    'px': 'px_true',
    'py': 'py_true',
    'pz': 'pz_true',
    'vx': 'vx_true',
    'vy': 'vy_true',
    'vz': 'vz_true',
    'dmod': 'dmod_true',
    'gaia_gmag': 'phot_g_mean_mag_abs',
    'gaia_g_bpmag': 'phot_bp_mean_mag_abs',
    'gaia_g_rpmag': 'phot_rp_mean_mag_abs',
    'mact': 'mact',
    'mtip': 'mtip',
    'age': 'age',
    'grav': 'logg',
    'feh': 'feh',
    'alpha': 'alpha',
    'carbon': 'carbon',
    'helium': 'helium',
    'nitrogen': 'nitrogen',
    'sulphur': 'sulphur',
    'oxygen': 'oxygen',
    'silicon': 'silicon',
    'calcium': 'calcium',
    'magnesium': 'magnesium',
    'neon': 'neon',
}

ALL_EXT_KEYS = {
    'lognh': 'lognh',
    'a0': 'A0',
    'ebv': 'ebv',
    'a_g_val': 'a_g_val',
    'a_g_bp_val': 'a_bp_val',
    'a_g_rp_val': 'a_rp_val',
    'bp_g_true': 'bp_g_true',
    'bp_g_int': 'bp_g_int',
    'bp_rp_true': 'bp_rp_true',
    'bp_rp_int': 'bp_rp_int',
    'g_rp_true': 'g_rp_true',
    'g_rp_int': 'g_rp_int',
    'e_bp_min_rp_val': 'e_bp_min_rp_val',
}

def calc_coords(data, indices=(None, None)):
    """ Compute missing coordinates """
    i_start, i_stop = indices

    coord_data = {}

    # calculate parallax
    dmod = data['dmod_true'][i_start: i_stop]
    parallax = Distance(distmod=dmod, unit='kpc').parallax.value
    coord_data['parallax_true'] = parallax

    # calculate proper motion and radial velocity
    #coord_data['pmra_true'] = None
    #coord_data['pmdec_true'] = None
    #coord_data['radial_velocity_true'] = None

    return coord_data






