
import os
try:
    import ebf
except ImportError:
    print('Cannot import ebf')
import h5py
import numpy as np

def append_dataset(fobj, key, data, overwrite=False):
    ''' Append an hdf5 dataset '''
    dataset = fobj.get(key)
    if dataset is None:
        fobj.create_dataset(key, data=data, maxshape=(None,), chunks=True)
    else:
        if overwrite:
            del dataset
            fobj.create_dataset(key, data=data, maxshape=(None,), chunks=True)
        else:
            N = dataset.shape[0]
            N_data = len(data)
            dataset.resize(N + N_data, axis=0)
            dataset[-N_data:] = data

def append_dataset_dict(fobj, data_dict, overwrite=False):
    ''' Append multiple hdf5 dataset '''
    for key, data in data_dict.items():
        append_dataset(fobj, key, data, overwrite)

def ebf_to_hdf5(infile, outfile, keys, batch_size=100000):
    ''' Convert ebf file to hdf5 file
    Args:
    - outfile: [str] path to output hdf5 file
    - infile: [str] path to input ebf file
    - keys: [list, dict] list of keys to copy.
    If given dict, change key name from dict key to dict val
    - batch_size: [int] batch size for converting large array that is difficult to fit to RAM
    '''
    ebf_to_hdf5_split(infile, outfile, keys, 0, 1, batch_size)

def ebf_to_hdf5_split(infile, outfile, keys, i_split=0, n_split=1, batch_size=100000):
    ''' Convert ebf file to hdf5 file
    Args:
    - outfile: [str] path to output hdf5 file
    - infile: [str] path to input ebf file
    - keys: [list, dict] list of keys to copy.
    If given dict, change key name from dict key to dict val
    - i_split: [int] index of split
    - n_split: [int] total number of splits
    - batch_size: [int] batch size for converting large array that is difficult to fit to RAM
    '''
    if i_split >= n_split:
        raise ValueError(f'i_split {i_split} must be smaller than n_split {n_split}')

    print('converting')
    print(f'input file: {infile}')
    print(f'output file: {outfile}')

    # Get the total length
    if isinstance(keys, dict):
        test_key = list(keys.keys())[0]
    else:
        test_key = keys[0]
    num_samples = ebf.getHeader(infile, f'/{test_key}').dim[0]

    start = int(num_samples / n_split * i_split)
    stop = int(num_samples / n_split * (i_split + 1))
    batches = np.arange(start, stop + batch_size, batch_size)
    batches[-1] = stop

    for key in keys:
        if isinstance(keys, dict):
            new_key = keys[key]
        else:
            new_key = key
        for i in range(len(batches)-1):
            data = ebf.read(infile, f'/{key}', begin=batches[i], end=batches[i+1])
            with h5py.File(outfile, 'a') as f:
                try:
                    append_dataset(f, new_key, data)
                except:
                    print(new_key, data, batch)
    print('Done')

