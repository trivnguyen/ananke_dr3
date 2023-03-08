
import numpy as np
import astropy.units as u
import pygaia
from pygaia.errors import astrometric

from .. import coordinates

_DEFAULT_RELEASE = 'dr3'

def calc_uncertainties(
        data, indices=(None, None), release=_DEFAULT_RELEASE):
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
    parallax_error = astrometric.parallax_uncertainty(
        g_mag, release=release) * uas_to_mas

    # calculate RA and Dec error
    ra_cosdec_error, dec_error = astrometric.position_uncertainty(
        g_mag, release=release)
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

