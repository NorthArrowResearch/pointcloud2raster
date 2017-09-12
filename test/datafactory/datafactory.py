#!/usr/bin/env python

from osgeo import gdal, osr
import numpy as np
from pointcloud2raster.raster import Raster
import os
import math
import csv
import random
import argparse
# this allows GDAL to throw Python Exceptions

proj = 'PROJCS["NAD_1983_2011_StatePlane_Arizona_Central_FIPS_0202",GEOGCS["GCS_NAD_1983_2011",DATUM["NAD_1983_2011",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["false_easting",213360.0],PARAMETER["false_northing",0.0],PARAMETER["central_meridian",-111.9166666666667],PARAMETER["scale_factor",0.9999],PARAMETER["latitude_of_origin",31.0],UNIT["Meter",1.0]]'


def array2rastercsv(array, outName, templateRaster, yoffset=0, xoffset=0, DataType=gdal.GDT_Float32):
    """

    :param array: The array with data
    :param outName: The output name (no extension. Will be suffixed)
    :param templateRaster: Where to get metadata for the raster
    :param DataType:
    :return:
    """
    rastername = outName + ".tif"
    matrixname = outName + ".matrix"

    # reversed_arr = array[::-1] # reverse array so the tif looks like the array
    cols = array.shape[1]
    rows = array.shape[0]
    originX = templateRaster.left + xoffset
    originY = templateRaster.top + yoffset

    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(rastername, cols, rows, 1, DataType)

    outRaster.SetGeoTransform((originX, templateRaster.cellWidth, 0, originY, 0, templateRaster.cellHeight))
    outband = outRaster.GetRasterBand(1)

    outband.WriteArray(array)
    outband.SetNoDataValue(templateRaster.nodata)

    outRaster.SetProjection(proj)
    outband.FlushCache()

    # This array might be upside-down from GDAL's perspective
    newArr = array

    cw = templateRaster.cellWidth
    ch = templateRaster.cellHeight

    # Now write a grid.
    np.savetxt(matrixname, newArr, fmt='%.3f', delimiter=",")

    # Now save the same file as a CSV
    csvname = outName + ".csv"
    with open(csvname, 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=' ', quoting=csv.QUOTE_NONE)
        for idy, row in enumerate(newArr):
            for idx, cell in enumerate(row):
                left = idx * templateRaster.cellWidth + originX + (cw / 2)
                top = idy * templateRaster.cellHeight + originY + (ch / 2)
                spamwriter.writerow([left, top, cell])

    # The cloud CSV has randomized tesselation
    csvname = outName + "_cloud.csv"
    with open(csvname, 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=' ', quoting=csv.QUOTE_NONE)
        for idy, row in enumerate(newArr):
            for idx, cell in enumerate(row):
                for pt in range(0, random.randint(3,15)):
                    val = cell + random.uniform(-0.2,0.2)
                    left = idx * templateRaster.cellWidth + originX + (cw / 2) + random.uniform( -cw / 2, cw / 2 )
                    top = idy * templateRaster.cellHeight + originY + (ch / 2) + random.uniform( -ch / 2, ch / 2 )
                    spamwriter.writerow([left, top, val])


def slopeyArray(width, height, high, low):
    """
    Creates a slopey array that slopes from high to low along the x axis
    :param width:
    :param height:
    :param high:
    :param low:
    :return:
    """
    high = float(high)
    low = float(low)
    array = np.empty((width, height))
    for idy, row in enumerate(array):
        for idx, cell in enumerate(row):
            array[idy][idx] = high - (high - low) *  (float(idx)/(width-1))
    return array



def checkerBoardArray(width, height, high, low):
    """
    Creates a checkerboard pattern
    :param width:
    :param height:
    :param high:
    :param low:
    :return:
    """
    gridsize = 10
    high = float(high)
    low = float(low)
    array = np.empty((width, height))
    for idy, row in enumerate(array):
        for idx, cell in enumerate(row):
            switch = bool((idx / gridsize) % 2) != bool((idy  / gridsize) % 2)
            array[idy][idx] = high if switch else low

    return array

def squareHillArray(width, height, high, low):
    """
    Create a nice square tooth function along the x axis
    :param width:
    :param height:
    :param high:
    :param low:
    :return:
    """
    high = float(high)
    low = float(low)
    array = np.empty((width, height))
    for idy, row in enumerate(array):
        for idx, cell in enumerate(row):
            val = low
            if idx < float(width/3) or idx > float(width/3)*2:
                val = high
            array[idy][idx] = val
    return array

def sawtoothArray(width, height, high, low, phase = 0):
    """
    Really simple sawtooth funciton
    :param width:
    :param height:
    :param high:
    :param low:
    :param phase:
    :return:
    """
    high = float(high)
    low = float(low)
    nWidth = width - 1
    nHeight = height - 1
    array = np.empty((width, height))
    period = float(width) / 4
    for idy, row in enumerate(array):
        for idx, cell in enumerate(row):
            array[idy][idx] = low +  (idx/period - math.floor(1/2 + idx/period)) * (high-low)
    return array

def doubleSawtoothArray(width, height, high, low, phase = 0):
    """
    Really simple sawtooth funciton
    :param width:
    :param height:
    :param high:
    :param low:
    :param phase:
    :return:
    """
    high = float(high)
    low = float(low)
    nWidth = width - 1
    nHeight = height - 1
    array = np.empty((width, height))
    period = float(width) / 4
    for idy, row in enumerate(array):
        for idx, cell in enumerate(row):
            vertical = low +  (idx/period - math.floor(1/2 + idx/period)) * (high-low)
            horizontal = low + (idy/period - math.floor(1/2 + idy/period)) * (high-low)
            array[idy][idx] = max([vertical, horizontal])
    return array

def sineArray(width, height, high, low, phase = 0):
    """
    A Nice sine wave function from low to high
    :param width:
    :param height:
    :param high:
    :param low:
    :return:
    """
    high = float(high)
    low = float(low)
    nWidth = width - 1
    nHeight = height - 1
    array = np.empty((width, height))
    for idy, row in enumerate(array):
        for idx, cell in enumerate(row):
            theta = (float(idx) / float(nWidth) * (math.pi * 2)) + phase
            array[idy][idx] = (high-low)/2 + low + (math.sin(theta) * (high-low)/2)
    return array

def tiltySlopeyArray(width, height, high, low, dir="N"):
    """
    Creates a slopey array that slopes from high to low along the x and y axis
    :param width:
    :param height:
    :param high:
    :param low:
    :return:
    """
    high = float(high)
    low = float(low)
    array = np.empty((width, height))
    nWidth = width - 1
    nHeight = height - 1
    diag =  math.sqrt(float(width)**2 + float(height)**2)
    diagAngle = math.atan2(float(width), float(height))

    for idy, row in enumerate(array):
        for idx, cell in enumerate(row):

            val = np.nan
            if dir == "N":
                hypotenuse = math.sqrt(float(idx) ** 2 + float(idy) ** 2)
                theta = diagAngle - math.atan2(idy, idx)
                val = low + ((high - low) * hypotenuse * math.cos(theta) ) / diag
            elif dir == "S":
                hypotenuse = math.sqrt(float(idx) ** 2 + float(idy) ** 2)
                theta = diagAngle - math.atan2(idy, idx)
                val = high - ((high - low) * hypotenuse * math.cos(theta) ) / diag
            elif dir == "E":
                hypotenuse = math.sqrt(float(nWidth - idx) ** 2 + float(idy) ** 2)
                theta = diagAngle - math.atan2(idy, (nWidth - idx))
                val = low + ((high - low) * hypotenuse * math.cos(theta) ) / diag
            elif dir == "W":
                hypotenuse = math.sqrt(float(nWidth - idx) ** 2 + float(idy) ** 2)
                theta = diagAngle - math.atan2(idy, (nWidth - idx))
                val = high - ((high - low) * hypotenuse * math.cos(theta) ) / diag
            array[idy][idx] = val

    return array

def constArray(width,height,value):
    """
    Create a Constant Value Array with width and height
    :param width: number of cells
    :param height: num ber of cells
    :param value: constant value you want for this
    :return:
    """
    arr = np.empty((width, height))
    arr.fill(value)
    return arr

def main():
    templateRaster = Raster('SampleData/sample.tif')

    # Create rasters with the following parameters
    max = 980
    min = 950
    pxwidth = 100
    pxheight = 100

    squaregrid = 3
    spacing = 100

    folder = 'output/'

    try:
        os.makedirs(folder)
    except:
        print "folder exists"

    topoffset = (pxheight + spacing) * templateRaster.cellHeight
    leftoffset = (pxwidth + spacing) * templateRaster.cellWidth

    array2rastercsv(checkerBoardArray(pxwidth, pxheight, min, max), '{0}Checkerboard{1}-{2}'.format(folder, min, max), templateRaster, topoffset, leftoffset)

    array2rastercsv(constArray(pxwidth, pxheight, 900), folder + 'const900', templateRaster, topoffset, leftoffset)
    array2rastercsv(constArray(pxwidth, pxheight, 950), folder + 'const950', templateRaster, topoffset, leftoffset)
    array2rastercsv(constArray(pxwidth, pxheight, 970), folder + 'const970', templateRaster, topoffset, leftoffset)
    array2rastercsv(constArray(pxwidth, pxheight, 980), folder + 'const980', templateRaster, topoffset, leftoffset)
    array2rastercsv(constArray(pxwidth, pxheight, 990), folder + 'const990', templateRaster, topoffset, leftoffset)

    array2rastercsv(slopeyArray(pxwidth, pxheight, max, min), '{0}Slopey{1}-{2}'.format(folder, min, max), templateRaster, topoffset, leftoffset)
    array2rastercsv(slopeyArray(pxwidth, pxheight, min, max), '{0}Slopey{1}-{2}'.format(folder, max, min), templateRaster, topoffset, leftoffset)

    array2rastercsv(tiltySlopeyArray(pxwidth, pxheight, max, min, "N"), '{0}AngledSlopey{1}-{2}{3}'.format(folder, min, max, "N"), templateRaster, topoffset, leftoffset)
    array2rastercsv(tiltySlopeyArray(pxwidth, pxheight, max, min, "E"), '{0}AngledSlopey{1}-{2}{3}'.format(folder, min, max, "E"), templateRaster, topoffset, leftoffset)
    array2rastercsv(tiltySlopeyArray(pxwidth, pxheight, max, min, "S"), '{0}AngledSlopey{1}-{2}{3}'.format(folder, min, max, "S"), templateRaster, topoffset, leftoffset)
    array2rastercsv(tiltySlopeyArray(pxwidth, pxheight, max, min, "W"), '{0}AngledSlopey{1}-{2}{3}'.format(folder, min, max, "W"), templateRaster, topoffset, leftoffset)

    array2rastercsv(squareHillArray(pxwidth, pxheight, max, min), '{0}SquareHill{1}-{2}'.format(folder, min, max), templateRaster, topoffset, leftoffset)
    array2rastercsv(squareHillArray(pxwidth, pxheight, min, max), '{0}SquareValley{1}-{2}'.format(folder, min, max), templateRaster, topoffset, leftoffset)

    array2rastercsv(sineArray(pxwidth, pxheight, max, min), '{0}SinWave{1}-{2}'.format(folder, min, max), templateRaster, topoffset, leftoffset)
    array2rastercsv(sineArray(pxwidth, pxheight, min, max), '{0}SinWaveInv{1}-{2}'.format(folder, min, max), templateRaster, topoffset, leftoffset)

    array2rastercsv(sineArray(pxwidth, pxheight, max, min, math.pi/2), '{0}CosWave{1}-{2}'.format(folder, min, max), templateRaster, topoffset, leftoffset)
    array2rastercsv(sineArray(pxwidth, pxheight, min, max, math.pi/2), '{0}CosWaveInv{1}-{2}'.format(folder, min, max), templateRaster, topoffset, leftoffset)

    array2rastercsv(sawtoothArray(pxwidth, pxheight, min, max), '{0}SawTooth{1}-{2}'.format(folder, min, max), templateRaster, topoffset, leftoffset)
    array2rastercsv(sawtoothArray(pxwidth, pxheight, max, min), '{0}SawToothInv{1}-{2}'.format(folder, min, max), templateRaster, topoffset, leftoffset)

    array2rastercsv(doubleSawtoothArray(pxwidth, pxheight, min, max), '{0}DoubleSawTooth{1}-{2}'.format(folder, min, max), templateRaster, topoffset, leftoffset)
    array2rastercsv(doubleSawtoothArray(pxwidth, pxheight, max, min), '{0}DoubleSawToothInv{1}-{2}'.format(folder, min, max), templateRaster, topoffset, leftoffset)

if __name__ == '__main__':
    # parse command line options
    # parser = argparse.ArgumentParser()
    # parser.add_argument('input_xml',
    #                     help = 'Path to the input XML file.',
    #                     type = str)
    # parser.add_argument('--verbose',
    #                     help = 'Get more information in your logs.',
    #                     action='store_true',
    #                     default=False )
    # args = parser.parse_args()


    main()
