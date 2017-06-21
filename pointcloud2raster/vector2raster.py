import os
import sys
import argparse
from loghelper import Logger
import subprocess
from os import path
import numpy as np
from scipy.interpolate import griddata
import gdal
import math
from raster import Raster
gdal.UseExceptions()

def GridRaster(sInputCSV, sOutputRaster, cellsize, xfield, yfield, zfield, templateRaster):
    """
    Read here for more
    http://www.gdal.org/grid_tutorial.html
    http://geoexamples.blogspot.ca/2012/05/creating-grid-from-scattered-data-using.html

    https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.griddata.html

    :param gdalWarpPath:
    :param sInputCSV:
    :param sOutputRaster:
    :return:
    """

    # Read Raster Properties
    Log = Logger("GridRaster")
    Log.info("Loading Data...")

    # Don't forget to zero-offset the indeces for the columns
    my_data = np.genfromtxt(sInputCSV, delimiter=' ', usecols=(xfield-1,yfield-1,zfield-1))

    Log.info("Getting data extents...")
    raw_max_x, raw_max_y, max_z = np.amax(my_data, axis=0)
    raw_min_x, raw_min_y, min_z = np.amin(my_data, axis=0)

    buffer = 10

    top = math.ceil(raw_max_y / cellsize) * cellsize + buffer
    bottom = math.floor(raw_min_y / cellsize) * cellsize - buffer

    left = math.floor(raw_min_x / cellsize) * cellsize - buffer
    right = math.floor(raw_max_x / cellsize) * cellsize + buffer

    Log.info("Setting up new Axes...")
    newAxes = np.mgrid[bottom:top:cellsize, left:right:cellsize]

    Log.info("Aligning with cell centers...")
    points = my_data[:,[0,1]] + cellsize/2
    data = my_data[:,2]

    Log.info("Gridding irregular data...")
    newArray = griddata((points[:,1], points[:,0]), data, (newAxes[0],newAxes[1]), method='cubic', fill_value=np.nan)

    Log.info("Writing Output Raster...")
    if templateRaster is not None:
        raster = Raster(filepath=templateRaster)
        raster.setArray(newArray)
        raster.write(sOutputRaster)
    else:
        raster = Raster(cellWidth=cellsize, array=newArray)
        raster.write(sOutputRaster)
    Log.info("Done.")



def main():
    #parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('csvfile',
                        help = 'Path to the input CSV pointcloud file.',
                        type = argparse.FileType('r'))
    parser.add_argument('outputRaster',
                        help = 'Path to the desired output Raster file.',
                        type = str)
    parser.add_argument('--cellsize',
                        help = 'column number to use for Y (defaults to 2 feet)',
                        default=2,
                        type = int)
    parser.add_argument('--xfield',
                        help = 'column number to use for Y (defaults to 2)',
                        default=1,
                        type = int)
    parser.add_argument('--yfield',
                        help = 'column number to use for Z (defaults to 3)',
                        default=2,
                        type = int)
    parser.add_argument('--zfield',
                        help='column number to use for X (defaults to 1)',
                        default=3,
                        type=int)
    parser.add_argument('--templateraster',
                        help='Template Raster to use for meta values',
                        type=argparse.FileType('r'))
    parser.add_argument('--verbose',
                        help = 'Get more information in your logs.',
                        action='store_true',
                        default=False )
    args = parser.parse_args()

    log = Logger("Program")

    try:
        # Now kick things off
        GridRaster(args.csvfile.name, args.outputRaster, args.cellsize, args.xfield, args.yfield, args.zfield, args.templateraster.name)
    except AssertionError as e:
        log.error("Assertion Error", e)
        sys.exit(0)
    except Exception as e:
        log.error('Unexpected error: {0}'.format(sys.exc_info()[0]), e)
        raise
        sys.exit(0)


"""
This function handles the argument parsing and calls our main function
"""
if __name__ == '__main__':
    main()