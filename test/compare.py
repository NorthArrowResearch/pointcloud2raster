#!/usr/bin/env python
from pointcloud2raster.pointcloud2raster import GridRaster
from pointcloud2raster.raster import Raster
import os



def main():
    """
    This test script runs everything in the data/rasters folder through the tool so we can see what's going on
    :return:
    """
    inputdir = os.path.join(os.path.dirname(__file__ ), "data", "rasters")
    outputdir = os.path.join(os.path.dirname(__file__ ), "data", "output")

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
                inputcsvcloud = os.path.join(inputdir, splitext[0] + "_cloud.csv")
                if not os.path.isfile(inputcsvcloud):
                    inputcsvcloud = inputcsv

                outputfile = os.path.join(outputdir, splitext[0] + "_" + method + "_output" + splitext[1])

                GridRaster(inputcsvcloud, outputfile, None, 1, 2, 3, method, templatefile)

                # Now do a test
                orig = Raster(filepath=templatefile)
                output = Raster(filepath=outputfile)

                # Don't do a subtract if we aren't aligned.
                if orig.left != output.left:
                    print "Left does not match"
                    continue
                if orig.top != output.top:
                    print "Top does not match"
                    continue
                if orig.rows != output.rows:
                    print "Rows do not match"
                    continue
                if orig.cols != output.cols:
                    print "Colunms do not match"
                    continue

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
