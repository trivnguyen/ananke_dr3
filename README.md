# Converting Ananke DR2 to Ananke DR3

To start, clone to repo and install the dependencies using:
```
git clone https://github.com/trivnguyen/ananke_dr3.git
pip install -r requirements.txt
```

To submit a SLURM script for a given galaxy, lsr, and rslice, use `write_slurm.py`
For example, to submit a job for M12f, LSR 1, rslice 8, run:
```
python write_slurm.py m12f 1 8
cd slurm_submit/m12f-lsr-1-rslice-8
./submit_all.submit
```
This will submit two jobs. The first job creates a catalog from the `.ebf` file.
The second job applies the selection function and is dependent on the first job.
The default partition is `skx-normal`, which uses the SkyLake node.
To change the partition, use `-p` or `--partition`
(e.g. `python write_slurm.py m12f 1 8 --partition=normal`).
The default alloc time for each job is 16 hours for the first job and 4 hours for the second job.
To change the alloc time, use `-t1` or `--time-catalog` for the first job and `-t2` or `--time-sf`
for the second job (e.g. `python write slurm.py m12f 1 8 -t1 1:00:00 --time-sf=2:00:00`).
The time format uses the SLURM convention.

