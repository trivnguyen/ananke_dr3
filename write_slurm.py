
''' Script to write and submit jobs '''

import os, sys, stat
import argparse

# Read in command line arguments
def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gal', type=str, required=True, help='galaxy name')
    parser.add_argument('--lsr', type=int, required=True, help='lsr number')
    parser.add_argument('--rslice', type=int, required=True, help='rslice number')
    parser.add_argument('--Njob', type=int, required=True, help='total number of jobs')
    parser.add_argument('-p', '--partition', type=str, default='skx-normal',
                        help='slurm partition')
    parser.add_argument('-A', '--accounting-group', type=str, default='TG-PHY210118',
                        help='accounting group')
    parser.add_argument('-t', '--time', type=str, default='00:30:00',
                        help='wall time of job')
    return parser.parse_args()

FLAGS = parse_cmd()
gal = FLAGS.gal
lsr = FLAGS.lsr
rslice = FLAGS.rslice
Njob = FLAGS.Njob
partition = FLAGS.partition
t = FLAGS.time
account = FLAGS.accounting_group

print(f'Galaxy, LSR, rslice: {gal}, {lsr}, {rslice}')

# Create submit directory based on galaxy, lsr, and rslice
submit_dir = f"slurm_submit/{gal}-lsr-{lsr}-rslice-{rslice}"
os.makedirs(submit_dir, exist_ok=True)

# Submit command
run_cmd = "srun -n1 -N1 python make_catalog.py "\
    f"--gal {gal} --lsr {lsr} --rslice {rslice} "\
    "--err-extrapolate --ijob {} --Njob {}"

all_batch_fn = []
for ijob in range(Njob):
    sbatch_fn = os.path.join(submit_dir, f"submit.{ijob}.sh")
    name = f"{gal}-lsr-{lsr}-rslice-{rslice}-{ijob}-{Njob}"
    run_cmd_ijob = run_cmd.format(ijob, Njob)
    with open(sbatch_fn, 'w') as f:
        f.write('#!/bin/bash\n')
        f.write('#SBATCH -p {}\n'.format(partition))
        f.write('#SBATCH -A {}\n'.format(account))
        f.write('#SBATCH --job-name {}\n'.format(name))
        f.write('#SBATCH --time {}\n'.format(t))
        f.write('#SBATCH -o out.{}.out\n'.format(ijob))
        f.write('#SBATCH -e err.{}.err\n'.format(ijob))
        f.write('#SBATCH --nodes=1\n')
        f.write('#SBATCH --ntasks=1\n')
        f.write('cd {}\n'.format(os.getcwd()))
        f.write(run_cmd_ijob + '\n')
        f.write('exit 0\n')

submit_all = os.path.join(submit_dir, f"submit_all.sh")
with open(submit_all, "w") as f:
    for ijob in range(Njob):
        f.write(f"sbatch submit.{ijob}.sh\n")
os.chmod(submit_all, stat.S_IRWXU)

