import data_utils as du
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--zip_name',
                        dest='zip_name',
                        type=str,
                        required=True,
                        help='zip name.')
    parser.add_argument('--zip_filepath',
                        dest='zip_filepath',
                        type=str,
                        required=True,
                        help='zip name.')
    parser.add_argument('--assembled_filepath',
                        dest='assembled_filepath',
                        type=str,
                        required=True,
                        help='Path to save assembled fits.')
    parser.add_argument('--remove_zip',
                        dest='remove_zip',
                        type=str,
                        required=False,
                        help='do you want to remove zip?')

    arg = parser.parse_args()

    zip_name = arg.zip_name
    zip_filepath = arg.zip_filepath
    assembled_filepath = arg.assembled_filepath

    # ------ Assembling: ------
    du.unzip(zip_name=zip_name, assembled_filepath=assembled_filepath, path_to_zip=zip_filepath, remove_zips=False)
    print('Assembled and normalized correctly.')

if __name__ == '__main__':
    main()
