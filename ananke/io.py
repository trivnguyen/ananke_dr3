
import os
import ebf
import h5py

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

def ebf_to_hdf5(infile, outfile, keys, batch_size=100000, overwrite=False):
    ''' Convert ebf file to hdf5 file
    Args:
    - outfile: [str] path to output hdf5 file
    - infile: [str] path to input ebf file
    - keys: [list, dict] list of keys to copy.
    If given dict, change key name from dict key to dict val
    - batch: [int] batch size for converting large array that is difficult to fit to RAM
    - overwrite: [bool] if true, overwrite any existing field
    '''

    print('converting')
    print(f'input file: {infile}')
    print(f'output file: {outfile}')

    for key in keys:
        if isinstance(keys, dict):
            new_key = keys[key]
        else:
            new_key = key
        for data in ebf.iterate(infile, f'/{key}', batch_size):
            with h5py.File(outfile, 'a') as f:
                append_dataset(f, new_key, data, overwrite=overwrite)
    print('Done')

