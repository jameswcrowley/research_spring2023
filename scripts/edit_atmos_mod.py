import numpy as np
import pandas as pd

sir_atmos_header = ['log(tau)', 'T', 'elec_P', 'microturb_v', 'B', 'LOS_v', 'gamma', 'phi', 'z', 'P_g', 'rho']

B_indices = (42, 48)
gamma_indices = (62, 68)
phi_indices = (70, 76)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path_to_mod',
                        dest='path_to_mod',
                        type=str,
                        required=True,
                        help='path to atmos mod file, including the file')
    parser.add_argument('--overwrite',
                        dest='overwrite',
                        type=bool,
                        required=True)
    parser.add_argument('--B',
                        dest='B',
                        type=int,
                        required=True)
    parser.add_argument('--gamma',
                        dest='gamma',
                        type=int,
                        required=True)
    parser.add_argument('--phi',
                        dest='phi',
                        type=int,
                        required=True)

    arg = parser.parse_args()

    path_to_mod = arg.path_to_mod
    overwrite = arg.overwrite # not yet functional... working on it.
    B = arg.B
    gamma = arg.gamma
    phi = arg.phi

    # ------ Reading In: ------
    with open(path_to_mod, 'r+') as f:
        line_num = 0
        lines = []
        for line in file:
            if line_num == 0:
                header = line
                lines.append(header)
                line_num += 1
            else:
                line_old = line

                line_new = line_old[:B_indices[0]]\
                           + B + line_old[B_indices[1]:gamma_indices[0]]\
                           + gamma + line_old[gamma_indices[1]:phi_indices[0]]\
                           + phi + line_old[phi_indices[1]:]

                lines.append(line_new)
        f.writelines(lines)
    f.close()


if __name__ == '__main__':
    main()