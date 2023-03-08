
import numpy as np
from . import photometric_utils

def calc_general_select(data):
    A0 = data['A0'][:]
    G = data['phot_g_mean_mag'][:]
    BP = data['phot_bp_mean_mag'][:]
    RP = data['phot_rp_mean_mag'][:]

    select = (
        (A0 <= 20)
        & (3 < G) & (G < 21)
        & (~np.isnan(BP)) & (~np.isnan(RP))
    )
    return select

def calc_rvs_select(data, extrapolate=True):
    G = data['phot_g_mean_mag'][:]
    RP = data['phot_rp_mean_mag'][:]
    Teff = 10**data['logteff'][:]
    Grvs = photometric_utils.gminr_to_grvsminr(
        G - RP, extrapolate=extrapolate) + RP

    select = np.zeros_like(G, dtype=bool)
    mask = (Grvs <= 12)
    select[mask] = (3600 < Teff[mask]) & (Teff[mask] < 14500)
    mask = (12 < Grvs) & (Grvs < 14)
    select[mask] = (3100 < Teff[mask]) & (Teff[mask] < 6750)
    return select

