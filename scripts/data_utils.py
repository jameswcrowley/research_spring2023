import numpy as np
import astropy.io.fits as fits
import os
import re
import zipfile
import shutil
import matplotlib.pyplot as plt
import glob
from math import ceil


def hinode_assemble(output_name, steps, input_filepath='.', output_filepath='.', correct=True, normalize=True,
                    lambda_length=112):
    """
        Hinode Assemble: Finds all fits scans in a specified folder, assembles, corrects, and normalizes.
                _____________
                Inputs: 1. output_name: the name of the saved fits file
                        2. steps: # of steps per scan. For time series datasets.
                        3. input_filepath: the filepath to the fits slit scans. default = '.'
                        4. output_filepath: where to put saved fits file. default = '.'
                        5. correct: boolean, do you want to correct for "overspill" of counts in some Hinode datasets?
                        6. normalize: boolean, divide all stokes vectors by the mean of the stokes I continuum
                        7. lambda_length: wavelength axis: 60 for cutting first line, 112 for both lines.
                _____________
                Outputs: saves an assembled fits file: corrected, normalized, and in SIR format.
                         Shape is (stokes, llambda, x, y) for single datasets and
                         (stokes, llambda, x, y, time) for time series.
        """

    filenames = []
    input_format = '.fits'

    correct_mod = ''
    normalize_mod = ''
    stacked_mod = ''

    for file in sorted(os.listdir(input_filepath)):
        if file.endswith(input_format):
            filenames.append(file)
    print(str(len(filenames)) + ' slits to assemble.')

    stokes = fits.open(input_filepath + filenames[0])[0].data
    SLITSIZE = stokes.shape[1]
    print('Slitlength = ', SLITSIZE)
    stokes = stokes.reshape(1, 4, SLITSIZE, 112)

    filenames = filenames[1:]
    for name in filenames:
        stokes_temp = fits.open(input_filepath + name)[0].data
        stokes_temp = stokes_temp.reshape(1, 4, SLITSIZE, 112)
        stokes = np.concatenate((stokes, stokes_temp), axis=0)

    stokes = np.swapaxes(np.swapaxes(stokes, 0, 3), 0, 1)
    stokes = stokes[:, :lambda_length, :, :]
    # correct:
    if correct:
        correct_mod = 'c.'
        stokes_new = np.zeros(stokes.shape)
        for i in range(stokes.shape[2]):
            for j in range(stokes.shape[3]):
                for l in range(stokes.shape[1]):
                    # stokes I should never be negative, if it is, we need to correct spillover counts:
                    if stokes[0, l, i, j] < 0:
                        stokes_new[0, l, i, j] = stokes[0, l, i, j] + 65536
                    else:
                        stokes_new[0, l, i, j] = stokes[0, l, i, j]
        stokes = stokes_new
    # normalize:
    if normalize:
        normalize_mod = 'n.'
        continuum = np.mean(stokes[0, :10, :, :])
        stokes = np.true_divide(stokes, continuum)

    if steps is not None:
        stacked_mod = 'stacked.'
        shape = list(stokes.shape)
        print(shape)
        x = shape.pop(3)  # get rid of old x-coordinate
        shape.insert(3, steps)  # inserts number of time steps

        num_time_steps = ceil(x / steps)
        shape.append(num_time_steps)
        print(shape)
        stokes_stacked = np.zeros(shape)
        print(num_time_steps)
        for time_step in range(num_time_steps):
            if time_step != num_time_steps - 1:
                stokes_stacked[:, :, :, :, time_step] = stokes[:, :, :, time_step * steps:(time_step + 1) * steps]
            else:
                mod = x % steps
                stokes_stacked[:, :, :, :mod, time_step] = stokes[:, :, :, time_step * steps:(time_step + 1) * steps]

        stokes = stokes_stacked

    hdu = fits.PrimaryHDU(stokes)
    hdu.header = fits.open(input_filepath + name)[0].header
    hdu.writeto(output_filepath + 'a.' + correct_mod + normalize_mod + stacked_mod + output_name, overwrite=True)
    print('Saved fits successfully at : ' + output_filepath + output_name)
    print('-------------------------------')


def unzip(zip_name, time_steps, assembled_filepath='../assembled_fits/', remove_zips=False, path_to_zip='../'):
    """
    Unzip: given a filepath and a filename, unzip the file, assemble the data (via calling hinode_assemble),
            and finally, delete the folder and scans.
            _____________
            Inputs: 1. assembled_filepath: filepath to send assembled to
                    2. time_steps: number of slits per scan, for time-series observations.
                       Put None if a single observation.
                    2. remove_zips: whether to remove zips, default is False
                    3. zip_name
                    4. path_to_zip
            _____________
            Outputs: saves an assembled fits file via hinode_assemble to the directory assembled_filepath
    """
    print(path_to_zip + zip_name)
    with zipfile.ZipFile(path_to_zip + zip_name, 'r') as zip_ref:
        temp_slit_folder_name = 'temp'
        # create a temporary folder to put fits slits into:
        try:
            os.mkdir(path_to_zip + temp_slit_folder_name)
        except:
            print('Temp folder already exists.')
        zip_ref.extractall(path_to_zip + temp_slit_folder_name)

    try:
        os.mkdir(assembled_filepath)
    except:
        print('Assembled Fits Folder Already Exits.')

    # find the filepath to the .fits slits
    all_sp3d_dirs, all_data_dirs = get_data_path(path_to_zip + temp_slit_folder_name)

    for data_dir_i in range(len(all_data_dirs)):
        data_dir = all_data_dirs[data_dir_i]
        name = all_data_dirs[data_dir_i][-15:]

        hinode_assemble(output_name=name + '.fits',
                        steps=time_steps,
                        input_filepath=data_dir + '/',
                        output_filepath=assembled_filepath)

    if remove_zips:
        try:
            shutil.rmtree(path_to_zip + zip_name)
            print('Successfully removed slit scan folder: ' + str(path_to_zip) + 'temp')
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))


def get_data_path(path_to_unzipped_directories):
    """
    Get Data Path: given a parent path, traverses the sub-directories to find all contained files.
                   returns all files in the folder ending with SP3D, but could be configured differently.
    _____________
    Inputs:
        1. path_to_unzipped_directories: parent directory path
    _____________
    Outputs:
        1. list of all sp3d directories
        2. list of all data (fits) files
    """
    all_sp3d_dirs = ['']  # all directories
    all_data_dirs = ['']
    # insert the appropriate path, relative or absolute, to where the data are stored
    for root, dirs, files in os.walk(path_to_unzipped_directories):
        # print(root, dirs, files)
        if root.endswith("SP3D"):
            all_sp3d_dirs += [root]
            for subdir in dirs:
                # this is the regular expression to find directories
                #     of the type [YYYYMMDDHHMMSS]
                if bool(re.search('20[012][0-9]+[012]+', subdir)):
                    all_data_dirs += [os.path.join(root, subdir)]
    # trim off the first null record in each list
    all_sp3d_dirs = all_sp3d_dirs[1:]
    all_data_dirs = all_data_dirs[1:]
    # print("SP3D Directories\n", "\n".join(all_sp3d_dirs))
    # print("Data Directories\n", "\n".join(all_data_dirs))

    return all_sp3d_dirs, all_data_dirs


def normalize(input_dataname, output_datapath, remove_original=True):
    """

    NO LONGER FUNCTIONAL: INCLUDED WITHIN HINODE_ASSEMBLE.

    normalize: normalizes data already in the right SIR shape
    _____________
    Parameters:
        - input_data: the filepath/name of a fits cube to normalze.
                      (in the shape (x, y, s, l))
        - output_data: the filepath/name of the output fits cube
        - remove_original: if the original fits file should be removed
    _____________
    Outputs:
        - normalized data: the filepath
    """

    input_data = fits.open(input_dataname)[0].data
    try:
        assert (input_data.shape[2] == 4)
    except Exception as err:
        print('Input data is incorrect format:', err)

    continuum = np.mean(input_data[:, :, 0, :10])
    normalized_data = np.true_divide(input_data, continuum)

    hdu = fits.PrimaryHDU(normalized_data)
    hdu.header = fits.open(input_dataname)[0].header
    hdu.writeto(output_datapath, 'normalized_' + input_dataname, overwrite=True)

    if remove_original:
        os.remove(input_dataname)


def quicklook(input_filepath):
    """
    Makes a simple plot of stokes I of all the assembled fits files, to make sure they look ok/not corrupted.
    given assembled fits files via hinode_assemble (i.e. naming convention is a.*.fits), plots Stokes I.
    _____________
    Inputs:
        1. input_filepath: path to assembled fits images
    _____________
    Outputs:
        1. quicklook.png: image of subplots containing Stokes I of each assembled fits.
    """
    data_list = glob.glob(input_filepath + 'a.*.fits')
    N = len(data_list)

    plt.figure(figsize=[5 * N, 3])

    for i in range(N):
        temp_data = fits.open(input_filepath + data_list[i])[0].data
        plt.subplot(1, N, i + 1)
        plt.imshow(temp_data[:, :, 0, 10], cmap='magma');
        plt.colorbar()
        plt.title(data_list[i])
    plt.savefig(input_filepath + 'quicklook.png')


def unstack(path_to_stacked_data, stacked_data, path_to_unstack, num_to_unstack=None):
    """
    idea 2: instead of making a list, just make a folder and unstack data into it. Then, when you

    """
    try:
        data = fits.open(path_to_stacked_data + stacked_data)[0].data
    except:
        print('Data not found.')
        return None

    assert len(data.shape) == 5
    num_stacks = data.shape[4]

    try:
        folder_name = path_to_unstack + str(stacked_data)[:-5] + '_unstacked'
        os.mkdir(folder_name)
    except:
        print('Unstacked Fits Folder Already Exits.')

    if num_to_unstack is not None:
        num_stacks = num_to_unstack
    else:
        pass

    for i in range(num_stacks):
        data_temp = data[:, :, :, :, i]
        hdu = fits.PrimaryHDU(data_temp)
        hdu.writeto(folder_name + '/stack_' + str(i) + '.fits', overwrite=True)

    print('Successfully unstacked ' + str(num_stacks) + ' in ' + folder_name)
