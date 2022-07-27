from scipy.interpolate import griddata
import numpy as np

d = np.genfromtxt('../data/nodustWD_mass_bound_valid.csv', delimiter=',', names=True)

def feh_to_Z(feh, solar_Z = 0.0152):
    """ Convert [Fe/H] to Z """
    return 10**(feh)*solar_Z

def flag_WD(data, indices=(None, None)):
    """ Set the flag for potential WD """
    i_start, i_stop = indices
    Z = feh_to_Z(data['feh'][i_start: i_stop])
    logage = data['age'][i_start: i_stop]
    Mini = data['mini'][i_start: i_stop]

    Mini_bounds = griddata((d['Z'], d['logage']), d['mass_bound'], (Z, logage), method='linear', fill_value=np.nan)
    
    flag_data = {}

    with np.errstate(invalid='ignore'):
        flag_data['flag_WD'] = np.where((Mini > Mini_bounds), 1, 0)
    
    return flag_data

def calc_flags(data, indices=(None, None)):
    ''' Calculate all flags '''
    flag_data = {}
    flag_data.update(flag_WD(data, indices))
    return flag_data