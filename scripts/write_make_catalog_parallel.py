
import os
import sys

gal = sys.argv[1]
lsr = sys.argv[2]
rslice = sys.argv[3]

print(gal, lsr, rslice)

sim_dir = f'/scratch/07561/tg868605/gaia_mocks/{gal}/lsr_{lsr}'
out_dir = f'/scratch/08317/tg876168/{gal}/lsr_{lsr}_rslice{rslice}'
submit_dir = f'submit_{gal}_lsr{lsr}_rslice{rslice}'

os.makedirs(out_dir, exist_ok=True)
os.makedirs(submit_dir, exist_ok=True)

mock_file = f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced.ebf"
ext_file = f"lsr-{lsr}-rslice-{rslice}.{gal}-res7100-md-sliced.ext.ebf"
out_file_temp = "lsr-{}-rslice-{}.{}-res7100-md-sliced-gcat-dr3.{}.hdf5"

Njob = 10
cmd_template = 'srun -n1 -N1 python make_catalog_parallel.py --out-file {} --mock-file {} --ext-file {} --ijob {} --Njob {}'

sbatch_files = []
for ijob in range(Njob):
    print(ijob)
    out_file = os.path.join(out_dir, out_file_temp.format(lsr, rslice, gal, ijob))
    print(out_file)
    mock_file = os.path.join(sim_dir, mock_file)
    ext_file = os.path.join(sim_dir, ext_file)
    cmd = cmd_template.format(out_file, mock_file, ext_file, ijob, Njob)

    log_out_fn = f'out-{ijob}.out'
    log_err_fn = f'err-{ijob}.err'

    # Create sbatch file and write
    sbatch_fn = f'submit-{ijob}.submit'
    sbatch_files.append(sbatch_fn)
    sbatch_fn = os.path.join(submit_dir, sbatch_fn)

    with open(sbatch_fn, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('#SBATCH -p normal\n')
        f.write('#SBATCH -A TG-AST140023\n')
        f.write('#SBATCH --job-name make_catalog\n')
        f.write('#SBATCH --time 1:00:00\n')
        f.write('#SBATCH --mail-type begin\n')
        f.write('#SBATCH --mail-type end\n')
        f.write('#SBATCH --mail-user tnguy@mit.edu\n')
        f.write('#SBATCH -o {}\n'.format(log_out_fn))
        f.write('#SBATCH -e {}\n'.format(log_err_fn))
        f.write('#SBATCH --nodes=1\n')
        f.write('#SBATCH --ntasks=1\n')
        f.write('cd $WORK/FIRE/ananke_dr3\n')
        f.write(cmd + '\n')
        f.write('exit 0\n')

# script to submit all jobs
submit_file = os.path.join(submit_dir, 'submit.sh')
with open(submit_file, 'w') as f:
    for sbatch_fn in sbatch_files:
        f.write('sbatch {}\n'.format(sbatch_fn))
os.chmod(submit_file, 0o744)

