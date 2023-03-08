
import h5py
import os

import numpy as np

from .logger import logger
try:
    import ebf
except ImportError:
    logger.exception('Cannot import ebf')

def get_rslice_path(gal, lsr, rslice, ijob=None, basedir=None):
    ''' Get the path of an rslice '''
    path = os.path.join(basedir, f'{gal}/lsr-{lsr}')
    if ijob is not None:
        path = os.path.join(
            path,
            f'lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.{ijob}.hdf5'
        )
    else:
        path = os.path.join(
            path,
            f'lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.hdf5'
        )
    if not os.path.exists(path):
        raise FileNotFoundError(f'{path} does not exist.')
    return path

def read_rslice(keys, gal, lsr, rslice, basedir, ijobs=[0, ]):
    ''' Iterate through all indices of an rslice and read data into dict '''
    data = {k: [] for k in keys}
    for i in ijobs:
        path = get_rslice_path(gal, lsr, rslice, i, basedir=basedir)
        with h5py.File(path, 'r') as f:
            for k in keys:
                data[k].append(f[k][:])
    for k in keys:
        data[k] = np.concatenate(data[k])
    return data

def append_dataset(fobj, key, data, overwrite=False):
    ''' Append an hdf5 dataset '''
    if fobj.get(key) is None:
        fobj.create_dataset(key, data=data, maxshape=(None,), chunks=True)
    else:
        if overwrite:
            del fobj[key]
            fobj.create_dataset(key, data=data, maxshape=(None,), chunks=True)
        else:
            dataset = fobj.get(key)
            N = dataset.shape[0]
            N_data = len(data)
            dataset.resize(N + N_data, axis=0)
            dataset[-N_data:] = data

def append_dataset_dict(fobj, data_dict, overwrite=False):
    ''' Append multiple hdf5 dataset '''
    for key, data in data_dict.items():
        append_dataset(fobj, key, data, overwrite)

def ebf_to_hdf5(infile, outfile, keys):
    ''' Convert ebf file to hdf5 file
    Args:
    - outfile: [str] path to output hdf5 file
    - infile: [str] path to input ebf file
    - keys: [list, dict] list of keys to copy.
    If given dict, change key name from dict key to dict val
    '''
    # Get the total number of samples
    if isinstance(keys, dict):
        test_key = list(keys.keys())[0]
    else:
        test_key = keys[0]
    num_samples = ebf.getHeader(infile, f'/{test_key}').dim[0]
    logger.info(f"Total number of samples: {num_samples}")

    # Open output file
    with h5py.File(outfile, 'w') as f:
        # Iterate over all keys
        for key in keys:
            if isinstance(keys, dict):
                new_key = keys[key]
            else:
                new_key = key
            logger.info(f"Copying key {key} to {new_key}")

            # Read data from file
            try:
                data = ebf.read(infile, f'/{key}')
            except:
                data = np.zeros(num_samples)
            try:
                append_dataset(f, new_key, data)
            except Exception as e:
                pass
