
import numpy as np
from scipy.interpolate import interp1d

def bminr_to_vmini(bminr, extrapolate=False):
    ''' Convert Gaia G_BP-G_RP to V-I '''
    vmini_max = 5
    vmini_min = -0.4
    vmini = np.linspace(vmini_min, vmini_max, 10000)

    if extrapolate:
        return interp1d(
            vmini_to_bminr(vmini), vmini, kind='nearest',
            fill_value='extrapolate', bounds_error=False)(bminr)
    else:
        return interp1d(
            vmini_to_bminr(vmini), vmini, bounds_error=False)(bminr)

def vmini_to_bminr(vmini, extrapolate=False):
    ''' Convert V-I to Gaia G_BP-G_RP '''
    vmini_max = 5
    vmini_min = -0.4

    if extrapolate:
        if isinstance(vmini, (int, float)):
            vmini = min(vmini, vmini_max)
            vmini = max(vmini, vmini_min)
        else:
            vmini[vmini < vmini_min] = vmini_min
            vmini[vmini > vmini_max] = vmini_max

    return np.where(
        (vmini < vmini_min) | (vmini > vmini_max), np.nan,
        -0.03298 + 1.259 * vmini - 0.1279 * vmini**2 + 0.01631 * vmini**3)

def gminr_to_grvsminr(gminr, extrapolate=False):
    ''' Convert Gaia G-G_RP to Gaia G_RVS-G_RP '''
    gminr_max = 1.7
    gminr_min = -0.15
    gminr_mid = 1.2

    if extrapolate:
        if isinstance(gminr, (int, float)):
            gminr = min(gminr, gminr_max)
            gminr = max(gminr, gminr_min)
        else:
            gminr[gminr < gminr_min] = gminr_min
            gminr[gminr > gminr_max] = gminr_max

    res = np.empty_like(gminr)*np.nan
    # Case 1
    mask = ((gminr > gminr_min) & (gminr < gminr_mid))
    res[mask] = (
        - 0.0397 - 0.2852 * gminr[mask]
        - 0.0330 * gminr[mask]**2 - 0.0867 * gminr[mask]**3)
    # Case 2
    mask = ((gminr > gminr_mid) & (gminr < gminr_max))
    res[mask] = (
        - 4.0618 + 10.0187 * gminr[mask]
        - 9.0532 * gminr[mask]**2 + 2.6089 * gminr[mask]**3)
    return res


