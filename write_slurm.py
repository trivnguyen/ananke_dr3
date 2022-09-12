
''' Script to write and submit jobs '''

import os
import sys

# Read in command line arguments
gal, lsr, rslice = sys.argv[1:]
name = f"{gal}-lsr-{lsr}-rslice-{rslice}"

print(f'Galaxy, LSR, rslice: {gal}, {lsr}, {rslice}')

# Define input and output paths
base_dir = f"/scratch/05328/tg846280/FIRE_Public_Simulations/ananke_dr3/"
ebf_dir = os.path.join(base_dir, f"{gal}_ebf/lsr-{lsr}")
sf_data_dir = os.path.join(base_dir, "selectionfunction_data")

submit_dir = f"slurm_submit/{gal}-lsr-{lsr}-rslice-{rslice}"
os.makedirs(submit_dir, exist_ok=True)

### Write batch script for make catalog job
# path to mock catalog and extinction file
ext_file = os.path.join(
    ebf_dir, f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced.ext.ebf")
mock_file = os.path.join(
    ebf_dir, f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced.ebf")

# path to cache and output
out_file = os.path.join(
    base_dir, f"{gal}/lsr-{lsr}/preSF",
    f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.hdf5"
)
cache_file = os.path.join(
    base_dir, f"{gal}/lsr-{lsr}/hdf5",
    f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.hdf5"
)

# Command
run_cmd = "srun -n1 -N1 python make_catalog.py "\
    f"--out-file {out_file} --mock-file {mock_file} --ext-file {ext_file} "\
    f"--cache-file {cache_file} --ext-var bminr --ext-extrapolate "\
    "--err-extrapolate --ijob 0 --Njob 1"

# Create sbatch file to submit make_catalog
sbatch_fn = os.path.join(submit_dir, "make_catalog.sh")
with open(sbatch_fn, 'w') as f:
    f.write('#!/bin/bash\n')
    f.write('#SBATCH -p skx-normal\n')
    f.write('#SBATCH -A TG-AST140023\n')
    f.write('#SBATCH --job-name {}\n'.format(name))
    f.write('#SBATCH --time 16:00:00\n')
    f.write('#SBATCH --mail-type begin\n')
    f.write('#SBATCH --mail-type end\n')
    f.write('#SBATCH --mail-user tnguy@mit.edu\n')
    f.write('#SBATCH -o make_catalog.out\n')
    f.write('#SBATCH -e make_catalog.err\n')
    f.write('#SBATCH --nodes=1\n')
    f.write('#SBATCH --ntasks=1\n')
    f.write('mkdir -p {}\n'.format(os.path.dirname(cache_file)))
    f.write('mkdir -p {}\n'.format(os.path.dirname(out_file)))
    f.write('cd {}\n'.format(os.getcwd()))
    f.write(run_cmd + '\n')
    f.write('exit 0\n')

### Write catalog for selection function script
out_file = os.path.join(
    base_dir, f"{gal}/lsr-{lsr}/",
    f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.hdf5"
)
in_file = os.path.join(
    base_dir, f"{gal}/lsr-{lsr}/preSF",
    f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.hdf5"
)
random_state = os.path.join(
    base_dir, f"{gal}/lsr-{lsr}/random_states",
    f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced-gcat-dr3.pkl")

run_cmd = "srun -n1 -N1 python selection_function_ruwe.py "\
    f"--in-file {in_file} --out-file {out_file} --random-state {random_state} "\
    f"--sf-data-dir {sf_data_dir} --selection ruwe1p4"

# Create sbatch file to submit make_catalog
sbatch_fn = os.path.join(submit_dir, "selection_fn.sh")
with open(sbatch_fn, 'w') as f:
    f.write('#!/bin/bash\n')
    f.write('#SBATCH -p skx-normal\n')
    f.write('#SBATCH -A TG-AST140023\n')
    f.write('#SBATCH --job-name {}\n'.format(name))
    f.write('#SBATCH --time 4:00:00\n')
    f.write('#SBATCH --mail-type begin\n')
    f.write('#SBATCH --mail-type end\n')
    f.write('#SBATCH --mail-user tnguy@mit.edu\n')
    f.write('#SBATCH -o selection_fn.out\n')
    f.write('#SBATCH -e selection_fn.err\n')
    f.write('#SBATCH --nodes=1\n')
    f.write('#SBATCH --ntasks=1\n')
    f.write('cd {}\n'.format(os.getcwd()))
    f.write(run_cmd + '\n')
    f.write('exit 0\n')

### Write submit script
submit_fn = os.path.join(submit_dir, "submit_all.submit")
with open(submit_fn, 'w') as f:
    f.write('#! /bin/bash\n')
    f.write('sbatch make_catalog.sh\n')
    f.write('sbatch --dependency=singleton selection_fn.sh\n')
os.chmod(submit_fn, 0o744)
