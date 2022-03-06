
_DEFAULT_BANDS = ('g', 'bp', 'rp')

def abs_to_app(abs_mag, dmod):
    ''' Convert abs magnitude to apparent magnitude given distance modulus '''
    return abs_mag + dmod

def app_to_ext(mag, a_mag):
    ''' Convert apparent magnitude to extincted magnitude given extincted magnitude '''
    return mag + a_mag

def calc_extinction(data, bands=_DEFAULT_BANDS, indices=(None, None)):
    ''' Calculate all extincted magnitude '''

    i_start, i_stop = indices

    # read distance modulus
    dmod = data['dmod_true'][i_start: i_stop]
    N_batch = len(dmod)

    # iterate over all bands
    ext_data = {}
    for band in ('g', 'bp','rp'):
        phot_mean_mag_abs = data[f'phot_{band}_mean_mag_abs'][i_start: i_stop]
        a_val = data[f'a_{band}_val'][i_start: i_stop]
        phot_mean_mag_int = abs_to_app(phot_mean_mag_abs, dmod)
        phot_mean_mag_true = app_to_ext(phot_mean_mag_int, a_val)

        ext_data[f'phot_{band}_mean_mag_true'] = phot_mean_mag_int
        ext_data[f'phot_{band}_mean_mag_int'] = phot_mean_mag_true

    return ext_data
