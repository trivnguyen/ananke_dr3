
import numpy as np
import scipy.interpolate as interpolate
import pandas as pd

_NOBS = {'G': 200, 'RP': 20, 'BP': 20}
_SPLINE_CSV = "ananke/data/LogErrVsMagSpline.csv"

def init_spline(spline_csv, band):
    """ Initialize spline function from CSV table

    Parameters
    ----------
    spline_csv: str
        path to CSV table with spline coefficients
    band: str
        name of GAIA passband. Must be "G", "g", "RP", "rp", "BP", "bp".

    Returns
    -------
    splines:
        Cubic spline interpolation function

    """
    df = pd.read_csv(spline_csv)
    band = band.upper()
    col_knots, col_coeff = f'knots_{band}', f'coeff_{band}'

    return interpolate.BSpline(
        df[col_knots].dropna(), df[col_coeff].dropna(), 3, extrapolate=False)

def mag_uncertainties(band, mag, nobs=0, spline_csv=_SPLINE_CSV):
    """
    Estimate the mag uncertainties given mag

    Parameters
    ----------
    band : str
        name of the GAI band for which the uncertainties should be estimated (case-insentive)
    mag: ndarray, float
        magnitude
    nobs : ndarray, int
        number of observations for which the uncertainties should be estimated.
        Must be a scalar integer value or an array of integer values.
    Returns
    -------
    u_mag: ndarray, float
        magnitude uncertainty
    """

    if isinstance(mag, (list, tuple, float, int)):
        mag = np.array([mag])
    if isinstance(nobs, int):
        nobs = np.repeat(nobs, len(mag))

    band = band.upper()
    if band not in ['G', 'BP', 'RP']:
        raise ValueError(f'Unknown band: {band}')

    # initialize spline
    spline = init_spline(spline_csv, band)

    # if magnitude is outside [4, 21], set to nearest bound
    #mag[mag <= 4] = 4.02
    #mag[mag >= 21.] = 20.98
    #mag = np.where((4. <= mag) & (mag <= 21.), mag, np.nan)

    # compute log error
    log_u_mag = np.where(
        nobs > 0,
        spline(mag) - np.log10(np.sqrt(nobs) / np.sqrt(_NOBS[band])),
        spline(mag),
    )
    u_mag = 10**log_u_mag
    return u_mag

def calc_uncertainties(data, indices=(None, None), extrapolate=False):
    """
    Calculate and return all magnitude errors and error-convolved magnitudes
    """
    i_start, i_stop = indices
    g_mag_true = data['phot_g_mean_mag_true'][i_start: i_stop]
    bp_mag_true = data['phot_bp_mean_mag_true'][i_start: i_stop]
    rp_mag_true = data['phot_rp_mean_mag_true'][i_start: i_stop]

    # calculate G, BP and RP errors
    g_mag_error = mag_uncertainties('G', g_mag_true)
    bp_mag_error = mag_uncertainties("BP", bp_mag_true)
    rp_mag_error = mag_uncertainties("RP", rp_mag_true)

    err_data = {}
    err_data['phot_g_mean_mag_error'] = g_mag_error
    err_data['phot_bp_mean_mag_error'] = bp_mag_error
    err_data['phot_rp_mean_mag_error'] = rp_mag_error
    err_data['phot_g_mean_mag'] = np.random.normal(g_mag_true, g_mag_error)
    err_data['phot_bp_mean_mag'] = np.random.normal(bp_mag_true, bp_mag_error)
    err_data['phot_rp_mean_mag'] = np.random.normal(rp_mag_true, rp_mag_error)

    return err_data

