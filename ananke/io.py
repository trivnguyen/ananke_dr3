
import os
import h5py
import logging

LOGGER = logging.getLogger(__name__)

import numpy as np
try:
    import ebf
except ImportError:
    LOGGER.warn('Cannot import ebf')


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
    # # ebf_to_hdf5_split(infile, outfile, keys, 0, 1, batch_size)
    # # Get the total length
    # if isinstance(keys, dict):
    #     test_key = list(keys.keys())[0]
    # else:
    #     test_key = keys[0]
    # num_samples = ebf.getHeader(infile, f'/{test_key}').dim[0]
    # print(num_samples)
    for key in keys:
        print(key)
        if isinstance(keys, dict):
            new_key = keys[key]
        else:
            new_key = key
        data = ebf.read(infile, f'/{key}')
        with h5py.File(outfile, 'a') as f:
            try:
                append_dataset(f, new_key, data)
            except Exception as e:
                pass

# DEPRECATED: Batching with EBF is too unreliable
# def ebf_to_hdf5_split(infile, outfile, keys, i_split=0, n_split=1, batch_size=100000):
#     ''' Convert ebf file to hdf5 file
#     Args:
#     - outfile: [str] path to output hdf5 file
#     - infile: [str] path to input ebf file
#     - keys: [list, dict] list of keys to copy.
#     If given dict, change key name from dict key to dict val
#     - i_split: [int] index of split
#     - n_split: [int] total number of splits
#     - batch_size: [int] batch size for converting large array that is difficult to fit to RAM
#     '''
#     if i_split >= n_split:
#         raise ValueError(f'i_split {i_split} must be smaller than n_split {n_split}')

#     # Get the total length
#     if isinstance(keys, dict):
#         test_key = list(keys.keys())[0]
#     else:
#         test_key = keys[0]
#     num_samples = ebf.getHeader(infile, f'/{test_key}').dim[0]

#     start = int(num_samples / n_split * i_split)
#     stop = int(num_samples / n_split * (i_split + 1))
#     batches = np.arange(start, stop + batch_size, batch_size)
#     batches[-1] = stop

#     for key in keys:
#         LOGGER.info(key)
#         print(key)
#         if isinstance(keys, dict):
#             new_key = keys[key]
#         else:
#             new_key = key
#         for i in range(len(batches)-1):
#             data = ebf.read(infile, f'/{key}', begin=batches[i], end=batches[i+1])
#             with h5py.File(outfile, 'a') as f:
#                 try:
#                     append_dataset(f, new_key, data)
#                 except Exception as e:
#                     pass

