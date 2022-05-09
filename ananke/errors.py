
import numpy as np
import astropy.units as u
from scipy.interpolate import interp1d

import pygaia
from pygaia.errors import astrometric, photometric, spectroscopic

from . import coordinates

_DEFAULT_RELEASE = 'dr3'

def bminr_to_vmini(bminr):
    ''' Convert Gaia G_BP-G_RP to V-I '''
    vmini_max = 5
    vmini_min = -0.4
    vmini = np.linspace(vmini_min, vmini_max, 1000)
    return interp1d(vmini_to_bminr(vmini), vmini, bounds_error=False)(bminr)

def vmini_to_bminr(vmini):
    ''' Convert V-I to Gaia G_BP-G_RP '''
    vmini_max = 5
    vmini_min = -0.4
    return np.where((vmini < vmini_min) | (vmini > vmini_max), np.nan,
                    -0.03298 + 1.259 * vmini - 0.1279 * vmini**2 + 0.01631 * vmini**3)

def gminr_to_grvsminr(gminr):
    ''' Convert Gaia G-G_RP to Gaia G_RVS-G_RP '''
    gminr_max = 1.7
    gminr_min = -0.15
    gminr_mid = 1.2
    res = np.empty_like(gminr)*np.nan
    # Case 1
    mask = ((gminr > gminr_min) & (gminr < gminr_mid))
    res[mask] = -0.0397 - 0.2852 * gminr[mask] - 0.0330 * gminr[mask]**2 - 0.0867 * gminr[mask]**3
    # Case 2
    mask = ((gminr > gminr_mid) & (gminr < gminr_max))
    res[mask] = -4.0618 + 10.0187 * gminr[mask] - 9.0532 * gminr[mask]**2 + 2.6089 * gminr[mask]**3
    return res

def calc_photometric_errors(data, indices=(None, None)):
    ''' Compute photometric errors and compute the error-convolved magnitudes '''
    i_start, i_stop = indices
    g_mag_true = data['phot_g_mean_mag_true'][i_start: i_stop]
    bp_mag_true = data['phot_bp_mean_mag_true'][i_start: i_stop]
    rp_mag_true = data['phot_rp_mean_mag_true'][i_start: i_stop]

    err_data = {}

    # calculate V-I and G, Grp, Gbp error
    vmini_true = bminr_to_vmini(bp_mag_true - rp_mag_true)
    g_mag_error = photometric.g_magnitude_uncertainty(g_mag_true)
    bp_mag_error = photometric.bp_magnitude_uncertainty(g_mag_true, vmini_true)
    rp_mag_error = photometric.rp_magnitude_uncertainty(g_mag_true, vmini_true)

    err_data['phot_g_mean_mag_error'] = g_mag_error
    err_data['phot_bp_mean_mag_error'] = bp_mag_error
    err_data['phot_rp_mean_mag_error'] = rp_mag_error
    err_data['phot_g_mean_mag'] = np.random.normal(g_mag_true, g_mag_error)
    err_data['phot_bp_mean_mag'] = np.random.normal(bp_mag_true, bp_mag_error)
    err_data['phot_rp_mean_mag'] = np.random.normal(rp_mag_true, rp_mag_error)
    err_data['vmini_true'] = vmini_true

    return err_data

def calc_astrometric_errors(data, indices=(None, None), release=_DEFAULT_RELEASE):
    ''' Compute astrometric errors and compute the error-convolved data '''
    i_start, i_stop = indices
    uas_to_mas = u.uas.to(u.mas)   # conversion from micro-arcsec to milli-arcsec
    uas_to_deg = u.uas.to(u.deg)   # conversion from micro-arcsec to degree
    g_mag = data['phot_g_mean_mag_true'][i_start: i_stop]
    ra_true = data['ra_true'][i_start: i_stop]
    dec_true = data['dec_true'][i_start: i_stop]
    parallax_true = data['parallax_true'][i_start: i_stop]
    pmra_true = data['pmra_true'][i_start: i_stop]
    pmdec_true = data['pmdec_true'][i_start: i_stop]

    err_data = {}

    # calculate parallax error
    parallax_error = astrometric.parallax_uncertainty(g_mag, release=release) * uas_to_mas

    # calculate RA and Dec error
    ra_cosdec_error, dec_error = astrometric.position_uncertainty(g_mag, release=release)
    cosdec = np.cos(np.deg2rad(dec_true))
    sindec = np.sin(np.deg2rad(dec_true))
    ra_error = np.sqrt(
        (ra_cosdec_error**2 + dec_error**2 * sindec**2) / cosdec**2)
    ra_cosdec_error = ra_cosdec_error * uas_to_deg
    dec_error = dec_error * uas_to_deg
    ra_error = ra_error * uas_to_deg

    err_data['ra'] = np.random.normal(ra_true, ra_error)
    err_data['dec'] = np.random.normal(dec_true, dec_error)
    err_data['parallax'] = np.random.normal(parallax_true, parallax_error)
    err_data['ra_error'] = ra_error
    err_data['dec_error'] = dec_error
    err_data['ra_cosdec_error'] = ra_cosdec_error
    err_data['parallax_error'] = parallax_error
    err_data['parallax_over_error'] = err_data['parallax'] / parallax_error

    # calculate proper motion error in ICRS coord and convert to Ananke unit
    # note that pmra includes a factor cos(dec), i.e. pmra = pmra * cos(dec)
    pmra_error, pmdec_error = astrometric.position_uncertainty(g_mag, release=release)
    pmra_error = pmra_error * uas_to_mas
    pmdec_error = pmdec_error * uas_to_mas

    err_data['pmra'] = np.random.normal(pmra_true, pmra_error)
    err_data['pmdec'] = np.random.normal(pmdec_true, pmdec_error)
    err_data['pmra_error'] = pmra_error
    err_data['pmdec_error'] = pmdec_error

    # calculate the error-convolved angle and proper motion in Galactic coord
    # NOTE: this does NOT return the error
    err_data.update(coordinates.icrs_to_gal(err_data, postfix=''))

    return err_data

def calc_spectroscopic_errors(data, indices=(None, None)):
    ''' Caculate spectroscopic error and error-convoled data '''
    i_start, i_stop = indices
    g_mag_true = data['phot_g_mean_mag_true'][i_start: i_stop]
    rp_mag_true = data['phot_rp_mean_mag_true'][i_start: i_stop]
    rv = data['radial_velocity_true'][i_start:i_stop]
    teff = data['teff'][i_start:i_stop]

    # No PyGaia function for this yet; implementing calculation from Robyn's communication
    # rv_error = np.zeros_like(rv)
    # Calculate GRVS-G from G-GRP, error for RV, and the correction factor
    grvs_true = gminr_to_grvsminr(g_mag_true - rp_mag_true) + rp_mag_true
    rv_error = np.where(teff < 6500, 0.12 + 6.0 * np.exp(0.9*(grvs_true - 14.0)),
                        0.4 + 20.0 * np.exp(0.8*(grvs_true - 12.75)))
    grvs_min = 8.0
    grvs_true[grvs_true < grvs_min] = grvs_min
    rv_error_corr = np.where(grvs_true > 12.0, 16.554 - 2.4899 * grvs_true + 0.09933 * grvs_true**2,
                             0.318 + 0.3884 * grvs_true - 0.02778 * grvs_true**2)

    err_data = {}
    err_data['radial_velocity'] = np.random.normal(rv, rv_error)
    err_data['radial_velocity_error'] = rv_error
    err_data['radial_velocity_error_corr_factor'] = rv_error_corr
    return err_data

def calc_errors(data, indices=(None, None), release=_DEFAULT_RELEASE):
    ''' Calculate all errors '''
    err_data = {}
    err_data.update(calc_photometric_errors(data, indices))
    err_data.update(calc_astrometric_errors(data, indices, release=release))
    err_data.update(calc_spectroscopic_errors(data, indices))
    return err_data




