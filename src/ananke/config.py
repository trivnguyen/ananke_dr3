
import configparser
import os

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "config.ini"))

BASEDIR = config.get('ENVIRONMENT_VARIABLES', 'BASEDIR')
EBF_BASEDIR = config.get('ENVIRONMENT_VARIABLES', 'EBF_BASEDIR')
HDF5_BASEDIR = config.get('ENVIRONMENT_VARIABLES', 'HDF5_BASEDIR')
DR3_PRESF_BASEDIR = config.get('ENVIRONMENT_VARIABLES', 'DR3_PRESF_BASEDIR')
DR3_BASEDIR = config.get('ENVIRONMENT_VARIABLES', 'DR3_BASEDIR')

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
    'gaiadr3nowdnodust_gmag': 'phot_g_mean_mag_abs',
    'gaiadr3nowdnodust_g_bpmag': 'phot_bp_mean_mag_abs',
    'gaiadr3nowdnodust_g_rpmag': 'phot_rp_mean_mag_abs',
    'smass': 'mini',
    'mact': 'mact',
    'mtip': 'mtip',
    'age': 'age',
    'teff': 'logteff',  # teff column in EBF is actually logteff
    'grav': 'logg',
    'lum': 'lum',
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
}
