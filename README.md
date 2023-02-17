# Converting Ananke DR2 to Ananke DR3

To start, clone to repo and install the dependencies using:
```
git clone https://github.com/trivnguyen/ananke_dr3.git
pip install -r requirements.txt
```

There are two steps for running Ananke DR3 pipeline
1. Convert EBF format into HDF5 format
2. Run Ananke DR3 pipeline using `make_catalog.py`

## Converting EBF format into HDF5 format
Because the main Ananke DR3 pipeline reads in HDF5 format, we need to convert
Galaxia's output in EBF format into HDF5 format.

This can be done by calling:
```
python make_catalog.py --pipeline ebf_to_hdf5 --gal GALAXY --lsr LSR --rslice RSLICE
```
where `GALAXY` is the name of the galaxy (i.e. `m12i`, `m12f` or `m12m`), `LSR`
is the index of the Local Standard of Rest in DR2, and `RSLICE` is the number of radial slices (rslice).
For example, if you want to convert m12f, lsr 1, and rslice 8, into HDF5, simply run:
```
$ python make_catalog.py --gal m12f --lsr 1 --rslice 8
```

For smaller rslices (e.g. m12i, lsr 0, rslice 0), the run time is about 1-2 hours.
For larger rslices, the run time might be about 2-4 hours.

## Run Ananke DR3 pipeline
The main Ananke DR3 pipeline allows you to divide an rslice into multiple parts.
These parts may be run in parallel, which saves a lot of computational time.
To run the main Ananke pipeline, call:
```
python make_catalog.py --gal GALAXY --lsr LSR --rslice RSLICE --ijob IJOB --Njob NJOB
```
where NJOB is the total number of jobs and IJOB is the index of the job
(ranging from 0 to NJOB-1). Note that the main pipeline should be run
*after the EBF to HDF5 conversion is done*.

To make it easier to run multiple jobs on Stampede2 (which does not allow job array),
we provide `write_slurm.py` to write job submission for SLURM.

To submit a SLURM script for a given galaxy, lsr, and rslice, simply run:
```
$ python write_slurm.py --gal GAL --lsr LSR --rslice RSLICE --Njob NJOB --time TIME
$ cd slurm_submit/GAL-lsr-LSR-rslice-RSLICE
$ ./submit_all.submit
```
This will submit NJOB jobs. TIME is the alloc time for **each job**,
**NOT** the total wall time of all jobs.
The default alloc time is 30 minutes per job.

The default partition is `skx-normal`, which uses the SkyLake node.
To change the partition, use `-p` or `--partition`
(e.g. `python write_slurm.py --gal m12f --lsr 1 --rslice 8 --partition=normal`).
