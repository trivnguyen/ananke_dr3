
_DEFAULT_BANDS = ('g', 'bp', 'rp')

_DEFAULT_LAWS = {
    'g':  [0.259021858973784, 0.93676111876298, -0.43744649958549203,
           0.0783508476444952, -0.0013612743323522401, 0.000797222688660053,
           -2.52364537395233e-05, -0.029981504413869, 0.005555060174347979,
           0.000402778419603886],
    'bp': [0.8880889146966658, 0.11318390480077001, 0.0846337732558566,
           -0.0371265818793239, -0.00296140793334905, 0.000538660562947277,
           -1.3101800801351199e-05, -0.0164152179931537, 0.00323902299833464,
           0.000169011297620409],
    'rp': [0.38271966845463296, 0.505895415656219, -0.314981478333036,
           0.0665302085130136, -0.0038378046816949798, 6.50490784002505e-05,
           1.57894227640801e-06, -0.00348740736346628, 0.0011087715942676801,
           -1.8313141658225e-05]
}

def abs_to_app(abs_mag, dmod):
    ''' Convert abs magnitude to apparent magnitude given distance modulus '''
    return abs_mag + dmod

def app_to_ext(mag, band, a_0, teff, extinction_laws=_DEFAULT_LAWS):
    ''' Convert apparent magnitude to extincted magnitude given A0 and Teff '''
    teff_min = 3500
    teff_max = 10000
    
    # Normalize Teff and set the extinction law coeff.
    X = teff/5040
    coeff = extinction_laws[band]
    
    k_mag = coeff[0] + coeff[1] * X + coeff[2] * X**2 + coeff[3] * X**3 + \
            coeff[4] * a_0 + coeff[5] * a_0**2 + coeff[6] * a_0**3 + \
            coeff[7] * X * a_0 + coeff[8] * a_0 * X**2 + coeff[9] * X * a_0**2
    return np.where((teff < teff_min) | (teff > teff_max), np.nan,
                    mag + k_mag*a_0)

def calc_extinction(data, bands=_DEFAULT_BANDS, indices=(None, None)):
    ''' Calculate all extincted magnitude '''

    i_start, i_stop = indices

    # read distance modulus
    dmod = data['dmod_true'][i_start: i_stop]
    N_batch = len(dmod)

    # iterate over all bands
    ext_data = {}
    for band in bands:
        phot_mean_mag_abs = data[f'phot_{band}_mean_mag_abs'][i_start: i_stop]
        a_0 = data['a0'][i_start: i_stop]
        teff = data['teff'][i_start:i_stop]
        phot_mean_mag_int = abs_to_app(phot_mean_mag_abs, dmod)
        phot_mean_mag_true = app_to_ext(phot_mean_mag_int, band, a_0, teff)

        ext_data[f'phot_{band}_mean_mag_int'] = phot_mean_mag_int
        ext_data[f'phot_{band}_mean_mag_true'] = phot_mean_mag_true

    return ext_data
