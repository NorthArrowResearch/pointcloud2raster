#!/usr/bin/env python
from pointcloud2raster.pointcloud2raster import GridRaster
from pointcloud2raster.raster import Raster
import os

def main():

    inputdir = os.path.join(os.path.dirname(__file__ ), "datafactory", "output")
    outputdir = os.path.join(os.path.dirname(__file__ ), "datafactory", "output_test")

    try:
        os.makedirs(outputdir)
    except:
        print "folder exists"

    for file in filter(lambda x: os.path.splitext(x)[1] == ".tif" ,os.listdir(inputdir)):
        for method in ["linear", "nearest", "cubic"]:
            try:
                splitext = os.path.splitext(file)
                templatefile = os.path.join(inputdir, file)
                inputcsv = os.path.join(inputdir, splitext[0] + ".csv")
                outputfile = os.path.join(outputdir, splitext[0] + "_" + method + "_output" + splitext[1])

                GridRaster(inputcsv, outputfile, None, 1, 2, 3, method, templatefile)

                # Now do a test
                orig = Raster(filepath=templatefile)
                output = Raster(filepath=outputfile)

                if orig.left != output.left:
                    print "Left does not match"
                if orig.rows != output.rows:
                    print "Rows do not match"
                if orig.cols != output.cols:
                    print "Colums does not match"
                if orig.top != output.top:
                    print "Top does not match"

                subtraction = os.path.join(outputdir, splitext[0] + "_" + method + "_output_SUBTRACT" + splitext[1])
                raster = Raster(filepath=templatefile)
                raster.setArray(orig.array - output.array)
                raster.write(subtraction)
            except:
                print "problem with: {}".format(file)

        print dir


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
