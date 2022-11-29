
''' Script to write and submit jobs '''

import os
import sys
import argparse

# Read in command line arguments
def parse_cmd():
    parser = argparse.ArgumentParser()
    parser.add_argument('gal', type=str, help='galaxy name')
    parser.add_argument('lsr', type=int, help='lsr number')
    parser.add_argument('rslice', type=int, help='rslice number')
    parser.add_argument('-p', '--partition', type=str, default='skx-normal',
                        help='slurm partition')
    parser.add_argument('-A', '--accounting-group', type=str, default='TG-PHY210118',
                        help='accounting group')
    parser.add_argument('-t', '--time-catalog', dest='t', type=str, default='2:00:00',
                        help='time of job')
    return parser.parse_args()

FLAGS = parse_cmd()
gal = FLAGS.gal
lsr = FLAGS.lsr
rslice = FLAGS.rslice
partition = FLAGS.partition
t = FLAGS.t
account = FLAGS.accounting_group
name = f"{gal}-lsr-{lsr}-rslice-{rslice}"

submit_dir = f"slurm_submit/fix_rv/{gal}-lsr-{lsr}-rslice-{rslice}"
os.makedirs(submit_dir, exist_ok=True)

print(f'Galaxy, LSR, rslice: {gal}, {lsr}, {rslice}')

# Define input and output paths
run_cmd = "srun -n1 -N1 python fix_rv.py "\
    f"--gal {gal} --lsr lsr-{lsr} --rslice {rslice}"

# Create sbatch file to submit make_catalog
sbatch_fn = os.path.join(submit_dir, "submit.sh")

with open(sbatch_fn, 'w') as f:
    f.write('#!/bin/bash\n')
    f.write('#SBATCH -p {}\n'.format(partition))
    f.write('#SBATCH -A {}\n'.format(account))
    f.write('#SBATCH --job-name {}\n'.format(name))
    f.write('#SBATCH --time {}\n'.format(t))
    f.write('#SBATCH -o submit.out\n')
    f.write('#SBATCH -e submit.err\n')
    f.write('#SBATCH --nodes=1\n')
    f.write('#SBATCH --ntasks=1\n')
    f.write('cd {}\n'.format(os.getcwd()))
    f.write(run_cmd + '\n')
    f.write('exit 0\n')

