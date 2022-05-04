
_DEFAULT_BANDS = ('g', 'bp', 'rp')

_DEFAULT_LAWS_TEFF = {
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

_DEFAULT_LAWS_BMINR = {
    'g':  [0.995969721536602,-0.159726460302015,0.0122380738156057,
           0.00090726555099859,-0.0377160263914123,0.00151347495244888,
           -2.52364537395142e-05,0.0114522658102451,-0.000936914989014318,
           -0.000260296774134201],
    'bp': [1.15363197483424,-0.0814012991657388,-0.036013023976704,
           0.0192143585568966,-0.022397548243016,0.000840562680547171,
           -1.31018008013549e-05,0.00660124080271006,-0.000882247501989453,
           -0.000111215755291684],
    'rp': [0.66320787941067,-0.0179847164933981,0.000493769449961458,
           -0.00267994405695751,-0.00651422146709376,3.30179903473159e-05,
           1.57894227641527e-06,-7.9800898337247e-05,0.000255679812110045,
           1.10476584967393e-05]
}

def abs_to_app(abs_mag, dmod):
    ''' Convert abs magnitude to apparent magnitude given distance modulus '''
    return abs_mag + dmod

def app_to_ext(mag, band, a_0, X, ext_var):
    ''' Convert apparent magnitude to extincted magnitude given A0 and Teff/BP-RP '''
    # Check which extinction law to use
    if ext_var == 'teff':
        X_min = 3500./5040.
        X_max = 10000./5040.

        # Normalize Teff and set the extinction law coeff.
        X = X/5040
        coeff = _DEFAULT_LAWS_TEFF[band]
    elif ext_var == 'bminr':
        X_min = -0.06
        X_max = 2.5

        # Set the extinction law coeff.
        coeff = _DEFAULT_LAWS_BMINR[band]

    k_mag = coeff[0] + coeff[1] * X + coeff[2] * X**2 + coeff[3] * X**3 + \
            coeff[4] * a_0 + coeff[5] * a_0**2 + coeff[6] * a_0**3 + \
            coeff[7] * X * a_0 + coeff[8] * a_0 * X**2 + coeff[9] * X * a_0**2
    return np.where((X < X_min) | (X > X_max), np.nan,
                    mag + k_mag*a_0)

def calc_extinction(data, bands=_DEFAULT_BANDS, indices=(None, None), ext_var='bminr'):
    ''' Calculate all extincted magnitude '''

    i_start, i_stop = indices

    # read distance modulus
    dmod = data['dmod_true'][i_start: i_stop]
    N_batch = len(dmod)

    # iterate over all bands
    ext_data = {}
    for band in bands:
        # Calculate unextincted apparent magnitude
        phot_mean_mag_abs = data[f'phot_{band}_mean_mag_abs'][i_start: i_stop]
        phot_mean_mag_int = abs_to_app(phot_mean_mag_abs, dmod)

        # Calculate extincted apparent magnitude
        a_0 = data['A0'][i_start: i_stop]
        if ext_var == 'teff':
            teff = data['teff'][i_start:i_stop]
            phot_mean_mag_true = app_to_ext(phot_mean_mag_int, band, a_0, teff, ext_var)
        elif ext_var == 'bminr':
            bp_mag_true = data['phot_bp_mean_mag_true'][i_start: i_stop]
            rp_mag_true = data['phot_rp_mean_mag_true'][i_start: i_stop]
            phot_mean_mag_true = app_to_ext(phot_mean_mag_int, band, a_0, bp_mag_true-rp_mag_true, ext_var)

        # Store the results
        ext_data[f'phot_{band}_mean_mag_int'] = phot_mean_mag_int
        ext_data[f'phot_{band}_mean_mag_true'] = phot_mean_mag_true

    return ext_data
