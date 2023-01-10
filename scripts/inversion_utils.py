import os
import time
import glob
import astropy.io.fits as fits


def create_list(stacked_data):
    """
    Creates a list of all time steps in a stacked dataset
    _____________
    Inputs:
        1. input, stacked fits file. Time-series should be 5th
           (4th indexed) column
    _____________
    Outputs:
        1. saves a text file with all the stacked datasets, to be iterated over via SIR
    """
    try:
        data = fits.open(stacked_data)[0].data
    except:
        print('Data not found.')
        return None

    assert len(data.shape) == 5

    num_stacked = data.shape[4]



