
import astropy.coordinates as coord
import astropy.units as u

def icrs_to_gal(data, postfix='', indices=(None, None)):
    """ Convert ICRS coordinate to Galactic """
    i_start, i_stop  = indices

    if postfix != '':
        postfix = '_' + postfix

    ra = data[f'ra{postfix}'][i_start: i_stop] * u.deg
    dec = data[f'dec{postfix}'][i_start: i_stop] * u.deg
    #parallax = data[f'parallax{postfix}'][i_start: i_stop] * u.mas
    #distance = parallax.to_value(u.kpc, equivalencies=u.parallax())
    pmra = data[f'pmra{postfix}'][i_start: i_stop] * u.mas / u.yr
    pmdec = data[f'pmdec{postfix}'][i_start: i_stop] * u.mas / u.yr
    #radial_velocity = data[f'radial_velocity{postfix}'][i_start: i_stop] * u.km / u.s

    #icrs = coord.ICRS(
    #    ra=ra, dec=dec, distance=distance, pm_ra_cosdec=pmra, pm_dec=pmdec,
    #    radial_velocity=radial_velocity)
    icrs = coord.ICRS(ra=ra, dec=dec, pm_ra_cosdec=pmra, pm_dec=pmdec)
    gc = icrs.transform_to(coord.Galactic())

    coord_data = {}
    coord_data[f'l{postfix}'] = gc.l.to_value(u.deg)
    coord_data[f'b{postfix}'] = gc.b.to_value(u.deg)
    coord_data[f'pml{postfix}'] = gc.pm_l_cosb.to_value(u.mas/u.yr)
    coord_data[f'pmb{postfix}'] = gc.pm_b.to_value(u.mas/u.yr)

    return coord_data

def cat_to_gal(data, postfix='', indices=(None, None)):
    """ Compute galactic coordinate from catalog coordinate """
    i_start, i_stop = indices

    if postfix != '':
        postfix = '_' + postfix

    px = data[f'px{postfix}'][i_start: i_stop] * u.kpc
    py = data[f'py{postfix}'][i_start: i_stop] * u.kpc
    pz = data[f'pz{postfix}'][i_start: i_stop] * u.kpc
    vx = data[f'vz{postfix}'][i_start: i_stop] * u.km / u.s
    vy = data[f'vy{postfix}'][i_start: i_stop] * u.km / u.s
    vz = data[f'vz{postfix}'][i_start: i_stop] * u.km / u.s
    gc = coord.Galactic(
        u=px, v=py, w=pz, U=vx, V=vy, W=vz,
        representation_type=coord.CartesianRepresentation,
        differential_type=coord.CartesianDifferential)

    coord_data = {}
    coord_data[f'l{postfix}'] = gc.spherical.lon.to_value(u.deg)
    coord_data[f'b{postfix}'] = gc.spherical.lat.to_value(u.deg)
    coord_data[f'pml{postfix}'] = gc.sphericalcoslat.differentials['s'].d_lon_coslat.to_value(u.mas/u.yr)
    coord_data[f'pmb{postfix}'] = gc.sphericalcoslat.differentials['s'].d_lat.to_value(u.mas/u.yr)
    coord_data[f'radial_velocity{postfix}'] = gc.sphericalcoslat.differentials['s'].d_distance.to_value(u.km/u.s)

    return coord_data

def calc_coords(data, indices=(None, None)):
    """ Calculate all missing coordinates """
    i_start, i_stop = indices

    coord_data = {}

    # calculate parallax
    dmod = data['dmod_true'][i_start: i_stop]
    parallax = coord.Distance(distmod=dmod, unit=u.kpc).parallax.to_value(u.mas)
    coord_data['parallax_true'] = parallax

    # calculate galactic proper motion and radial velocity
    px = data['px_true'][i_start: i_stop] * u.kpc
    py = data['py_true'][i_start: i_stop] * u.kpc
    pz = data['pz_true'][i_start: i_stop] * u.kpc
    vx = data['vz_true'][i_start: i_stop] * u.km / u.s
    vy = data['vy_true'][i_start: i_stop] * u.km / u.s
    vz = data['vz_true'][i_start: i_stop] * u.km / u.s
    gc = coord.Galactic(
        u=px, v=py, w=pz, U=vx, V=vy, W=vz,
        representation_type=coord.CartesianRepresentation,
        differential_type=coord.CartesianDifferential)
    coord_data['pml_true'] = gc.sphericalcoslat.differentials['s'].d_lon_coslat.to_value(u.mas/u.yr)
    coord_data['pmb_true'] = gc.sphericalcoslat.differentials['s'].d_lat.to_value(u.mas/u.yr)
    coord_data['radial_velocity_true'] = gc.sphericalcoslat.differentials['s'].d_distance.to_value(u.km/u.s)

    # calculate proper motion in ICRS
    icrs = gc.transform_to(coord.ICRS())
    coord_data['pmra_true'] = icrs.pm_ra_cosdec.to_value(u.mas/u.yr)
    coord_data['pmdec_true'] = icrs.pm_dec.to_value(u.mas/u.yr)

    return coord_data

