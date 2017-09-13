import os
import sys
import argparse
from loghelper import Logger
import numpy as np
from scipy.interpolate import griddata
import gdal
import math
from raster import Raster
gdal.UseExceptions()

def GridRaster(sInputCSV, sOutputRaster, cellsize, xfield, yfield, zfield, method, templateRaster):
    """
    Read here for more about gridding data with scipy
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
    # We poll the data for the minimum extents of all the columsn.
    # This gives us our rectangle
    raw_max_x, raw_max_y, max_z = np.amax(my_data, axis=0)
    raw_min_x, raw_min_y, min_z = np.amin(my_data, axis=0)

    # If the user passed in a template raster then pattern ours off of it.
    if templateRaster is not None:
        raster = Raster(filepath=templateRaster)
        cw = raster.cellWidth
        ch = raster.cellHeight
    # otherwise we'll need to build a raster from scratch without a CRS
    else:
        raster = Raster(cellWidth=cellsize)
        cw = cellsize
        ch = cellsize

    # Calculate the rectangle encompassing all our data by cropping to the nearest cell outside our data's extents
    top = math.ceil( raw_max_y / abs(ch) ) * abs(ch)
    bottom = math.floor( raw_min_y / abs(ch) ) * abs(ch)

    left = math.floor(raw_min_x / cw) * cw
    right = math.ceil(raw_max_x / cw) * cw

    # Here's where we create an array of dimension 2 X Rows X Cols
    # It's basically two grids, one that contains top -> bottom coordinates (y) and the other that contains left to
    # right coordinates (x) using the cell height (ch) and cell width (cw) as an increment
    Log.info("Setting up new Axes...")
    newAxes = np.mgrid[ top:bottom:ch, left:right:cw ]

    # Grid data. The first parameter is a double list containing the X and Y columns of the CSV.
    # The second parameter is just the Z values from the CSV
    # The third parameter are the two new grids, each containing the X and Y values we want to have, adjusted for cell
    # centers.
    Log.info("Gridding irregular data...")
    newArray = griddata((my_data[:,1], my_data[:,0]), my_data[:,2], (newAxes[0]+ ch/2,newAxes[1] + cw/2), method=method, fill_value=np.nan)

    Log.info("Writing Output Raster...")
    extsplit = os.path.splitext(sOutputRaster)
    newpath = os.path.join(os.path.dirname(sOutputRaster), extsplit[0] + extsplit[1])

    # Our top and left may not match the template raster so make sure to set those explicitly
    raster.top = top
    raster.left = left

    # Set the array and write the file to disk
    raster.setArray(newArray)
    raster.write(newpath)

    Log.info("Done. Output file written: {}".format(sOutputRaster))


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
                        help = 'Cell size to use. Use this if not a templateraster',
                        type = int)

    parser.add_argument('--xfield',
                        help = 'column number to use for X (defaults to 1)',
                        default=1,
                        type = int)

    parser.add_argument('--yfield',
                        help = 'column number to use for Y (defaults to 2)',
                        default=2,
                        type = int)

    parser.add_argument('--zfield',
                        help='column number to use for Z (defaults to 3)',
                        default=3,
                        type=int)

    parser.add_argument('--method',
                        help='Method for griddata. One of "cubic", "linear", "nearest" Default: cubic',
                        default="cubic",
                        type=str)
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
        GridRaster(args.csvfile.name, args.outputRaster, args.cellsize, args.xfield, args.yfield, args.zfield, args.method, args.templateraster.name)
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