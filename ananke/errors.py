
import numpy as np
from scipy.interpolate import interp1d
import astropy.units as u

import pygaia
from pygaia.errors import astrometric, photometric, spectroscopic

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
    uas_to_deg = u.uas.to(u.deg)   # covnersion from micro-arcsec to degree
    g_mag = data['phot_g_mean_mag_true'][i_start: i_stop]
    ra_true = data['ra_true'][i_start: i_stop]
    dec_true = data['dec_true'][i_start: i_stop]
    parallax_true = data['parallax_true'][i_start: i_stop]
    pmra_true = data['pmra_true'][i_start: i_stop]
    pmdec_true = data['pmdec_true'][i_start: i_stop]

    err_data = {}

    # calculate position error and convert to Ananke unit
    ra_cosdec_error, dec_error = astrometric.position_uncertainty(g_mag, release=release)
    parallax_error = astrometric.parallax_uncertainty(g_mag, release=release) * uas_to_mas
    ra_error = np.abs(ra_cosdec_error / np.cos(dec_true)) * uas_to_deg
    dec_error = dec_error * uas_to_deg

    err_data['ra'] = np.random.normal(ra_true, ra_error)
    err_data['dec'] = np.random.normal(dec_true, dec_error)
    err_data['parallax'] = np.random.normal(parallax_true, parallax_error)
    err_data['ra_error'] = ra_error
    err_data['dec_error'] = dec_error
    err_data['parallax_error'] = parallax_error
    err_data['parallax_over_error'] = err_data['parallax'] / parallax_error

    # calculate proper motion error and convert to Ananke unit
    # note that pmra includes a factor cos(dec), i.e. pmra = pmra * cos(dec)
    pmra_error, pmdec_error = astrometric.position_uncertainty(g_mag, release=release)
    pmra_error = pmra_error * uas_to_mas
    pmdec_error = pmdec_error * uas_to_mas

    err_data['pmra'] = np.random.normal(pmra_true, pmra_error)
    err_data['pmdec'] = np.random.normal(pmdec_true, pmdec_error)
    err_data['pmra_error'] = pmra_error
    err_data['pmdec_error'] = pmdec_error

    return err_data

def calc_spectroscopic_errors(data, indices=(None, None)):
    ''' Caculate spectroscopic error and error-convoled data '''
    i_start, i_stop = indices
    rv = data['radial_velocity_true'][i_start:i_stop]

    err_data = {}
    rv_error = np.zeros_like(rv)

    err_data['radial_velocity'] = np.random.normal(rv, rv_error)
    err_data['radial_velocity_error'] = rv_error

    return err_data

