
import numpy as np
from scipy.interpolate import griddata

from . import photometric_utils

_WD_TABLE = np.genfromtxt(
    'ananke/data/nodustWD_mass_bound_valid.csv',
    delimiter=',', names=True)

def feh_to_Z(feh, solar_Z=0.0152):
    """ Convert [Fe/H] to Z """
    return 10**(feh)*solar_Z

def flag_WD(data, indices=(None, None)):
    """ Set the flag for potential WD """
    i_start, i_stop = indices
    Z = feh_to_Z(data['feh'][i_start: i_stop])
    logage = data['age'][i_start: i_stop]
    Mini = data['mini'][i_start: i_stop]

    Mini_bounds = griddata(
        (_WD_TABLE['Z'], _WD_TABLE['logage']), _WD_TABLE['mass_bound'],
        (Z, logage), method='linear', fill_value=np.nan)

    with np.errstate(invalid='ignore'):
        return np.where((Mini > Mini_bounds), '1', '0')


def flag_photo_err_extrapolate(data, indices=(None, None), extrapolate=False):
    """ Set the flag for extrapolated photometric error calculation """
    if not extrapolate:
        i_start, i_stop = indices
        N_star = len(data['ra'][i_start: i_stop])
        return np.array(['0']*N_star)
    else:
        i_start, i_stop = indices

        bp_mag_true = data['phot_bp_mean_mag_true'][i_start: i_stop]
        rp_mag_true = data['phot_rp_mean_mag_true'][i_start: i_stop]
        bminr = bp_mag_true - rp_mag_true

        vmini_max = 5
        vmini_min = -0.4
        bminr_max = photometric_utils.vmini_to_bminr(
            vmini_max,extrapolate=extrapolate)
        bminr_min = photometric_utils.vmini_to_bminr(
            vmini_min,extrapolate=extrapolate)

        return np.where((bminr < bminr_min) | (bminr > bminr_max), '1', '0')

def flag_spect_err_extrapolate(data, indices=(None, None), extrapolate=False):
    """ Set the flag for extrapolated spectroscopic error calculation """
    if not extrapolate:
        i_start, i_stop = indices
        N_star = len(data['ra'][i_start: i_stop])
        return np.array(['0']*N_star)
    else:
        i_start, i_stop = indices

        gminr_max = 1.7
        gminr_min = -0.15

        g_mag_true = data['phot_g_mean_mag_true'][i_start: i_stop]
        rp_mag_true = data['phot_rp_mean_mag_true'][i_start: i_stop]
        gminr = g_mag_true - rp_mag_true

        return np.where((gminr < gminr_min) | (gminr > gminr_max), '1', '0')

def flag_extinct_extrapolate(data, ext_var, indices=(None, None), extrapolate=False):
    """ Set the flag for extrapolated extinction law """
    if not extrapolate:
        i_start, i_stop = indices
        N_star = len(data['ra'][i_start: i_stop])
        return np.array(['0']*N_star)
    else:
        i_start, i_stop = indices

        if ext_var == 'teff':
            X = data['teff'][i_start:i_stop]
            X_min = 3500./5040.
            X_max = 10000./5040.

        elif ext_var == 'bminr':
            X = (data['phot_bp_mean_mag_abs'][i_start: i_stop]
                - data['phot_rp_mean_mag_abs'][i_start: i_stop])
            X_min = -0.06
            X_max = 2.5

        return np.where((X < X_min) | (X > X_max), '1', '0')

def calc_flags(data, indices=(None, None), ext_var='bminr',
               ext_extrapolate=False, err_extrapolate=False):
    """ Calculate all flags and combine into a bit mask """
    flag_data = {}

    # Bit 0: Extinction extrapolation flag
    flag0 = flag_extinct_extrapolate(data, ext_var, indices, ext_extrapolate)
    # Bit 1: Photometric error extrapolation flag
    flag1 = flag_photo_err_extrapolate(data, indices, err_extrapolate)
    # Bit 2: Spectroscopic error extrapolation flag
    flag2 = flag_spect_err_extrapolate(data, indices, err_extrapolate)
    # Bit 3: WD flag
    flag3 = flag_WD(data, indices)

    # Combine bits
    flag_data['flags'] = [
        int(i + j + k + l,2) for i, j, k, l in zip(flag3, flag2, flag1, flag0)]

    return flag_data

