
import numpy as np
from .. import photometric_utils

def rv_uncertainties(grvs, teff):
    """
    Calculate RV errors and error correction factor from G and G_RVS.
    Implementing calculation from communication with Robyn Sanderson
    For Teff < 6500:
        0.12 + 6 * exp(0.9 * (G_RVS - 14))
    For Teff >= 6500:
        0.4 + 20 * exp(0.8 * (G_RVS - 12.75))
    """
    rv_error = np.where(
        teff < 6750, 0.12 + 6.0 * np.exp(0.9*(grvs - 14.0)),
        0.4 + 20.0 * np.exp(0.8*(grvs - 12.75)))

    grvs_min = 8.0
    grvs[grvs < grvs_min] = grvs_min
    rv_error_corr = np.where(
        grvs > 12.0, 16.554 - 2.4899 * grvs + 0.09933 * grvs**2,
        0.318 + 0.3884 * grvs - 0.02778 * grvs**2)

    return rv_error, rv_error_corr

def calc_uncertainties(
    data, indices=(None, None), extrapolate=False):
    """
    Calculate all spectroscopic uncertainties and error-convolved data
    """
    i_start, i_stop = indices
    g_mag_true = data['phot_g_mean_mag_true'][i_start: i_stop]
    rp_mag_true = data['phot_rp_mean_mag_true'][i_start: i_stop]
    rv = data['radial_velocity_true'][i_start:i_stop]
    teff = 10**data['logteff'][i_start:i_stop]

    # Calculate G_RVS from G and R and calculate RV error from G_RVS and Teff
    grvs_true = photometric_utils.gminr_to_grvsminr(
        g_mag_true - rp_mag_true, extrapolate=extrapolate) + rp_mag_true
    rv_error, rv_error_corr = rv_uncertainties(grvs_true, teff)

    err_data = {}
    err_data['radial_velocity'] = np.random.normal(rv, rv_error)
    err_data['radial_velocity_error'] = rv_error
    err_data['radial_velocity_error_corr_factor'] = rv_error_corr

    return err_data

