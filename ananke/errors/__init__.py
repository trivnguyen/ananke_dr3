
from . import astrometric
from . import photometric
from . import spectroscopic

def calc_errors(data, indices=(None, None), extrapolate=False):
    """ Calculate all errors """

    err_data = {}
    err_data.update(
        photometric.calc_uncertainties(data, indices, extrapolate=extrapolate))
    err_data.update(
        astrometric.calc_uncertainties(data, indices))
    err_data.update(
        spectroscopic.calc_uncertainties(data, indices, extrapolate=extrapolate))

    return err_data

