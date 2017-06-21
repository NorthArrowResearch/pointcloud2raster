import gdal, osr
from os import path
import numpy as np
from loghelper import Logger
from scipy import interpolate
# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()

class Raster:

    def __init__(self, *args, **kwargs):
        self.log = Logger("Raster")
        self.filename = kwargs.get('filepath', None)

        # Got a file. Load it
        if self.filename is not None:
            self.errs = ""
            try:
                src_ds = gdal.Open( self.filename )
            except RuntimeError, e:
                self.log.error('Unable to open %s' % self.filename, e)
                raise e
            try:
                # Read Raster Properties
                srcband = src_ds.GetRasterBand(1)
                self.bands = src_ds.RasterCount
                self.driver = src_ds.GetDriver().LongName
                self.gt = src_ds.GetGeoTransform()
                self.nodata = srcband.GetNoDataValue()
                """ Turn a Raster with a single band into a 2D [x,y] = v array """
                self.array = srcband.ReadAsArray()

                # Now mask out any NAN or nodata values (we do both for consistency)
                if self.nodata is not None:
                    self.array = np.ma.array(self.array, mask=(np.isnan(self.array) | (self.array == self.nodata)))

                self.dataType = srcband.DataType
                self.min = np.nanmin(self.array)
                self.max = np.nanmax(self.array)

                if self.min is np.ma.masked:
                    self.min = np.nan
                if self.max is np.ma.masked:
                    self.max = np.nan

                self.proj = src_ds.GetProjection()

                # Remember:
                # [0]/* top left x */
                # [1]/* w-e pixel resolution */
                # [2]/* rotation, 0 if image is "north up" */
                # [3]/* top left y */
                # [4]/* rotation, 0 if image is "north up" */
                # [5]/* n-s pixel resolution */
                self.left = self.gt[0]
                self.cellWidth = self.gt[1]
                self.top = self.gt[3]
                self.cellHeight = self.gt[5]
                self.cols = src_ds.RasterXSize
                self.rows = src_ds.RasterYSize
                # Important to throw away the srcband
                srcband.FlushCache()
                srcband = None

            except RuntimeError as e:
                self.log.error('Could not retrieve meta Data for %s' % self.filepath, e)
                raise e

        # No file to load. this is a new raster
        else:
            self.nodata = kwargs.get('nodata', -9999.0)
            self.min = None
            self.max = None
            self.array = None

            self.rows = int(kwargs.get('rows', 0))
            self.cols = int(kwargs.get('cols', 0))
            self.cellWidth = float(kwargs.get('cellWidth', 0.1))
            self.cellHeight = float(kwargs.get('cellHeight', -self.cellWidth))
            self.proj = kwargs.get('proj', "")
            self.dataType = kwargs.get('dataType', gdal.GDT_Float32)

            tempArray = kwargs.get('array', None)
            if tempArray is not None:
                self.setArray(tempArray)
                self.min = np.nanmin(self.array)
                self.max = np.nanmax(self.array)

            extent = kwargs.get('extent', None)

            # Expecting extent in the form [Xmin, Xmax, Ymin, Ymax]
            if extent is not None:
                self.left = float(extent[0] if self.cellWidth > 0 else extent[1]) # What we mean by left is : top left 'X'
                self.top = float(extent[2] if self.cellHeight > 0 else extent[3])  # What we mean by top is : top left 'Y'

                self.rows = abs(int(round((extent[3] - extent[2]) / self.cellHeight)))
                self.cols = abs(int(round((extent[1] - extent[0]) / self.cellWidth)))
            else:
                self.top = float(kwargs.get('top', -9999.0))
                self.left = float(kwargs.get('left', -9999.0))

    def setArray(self, incomingArray, copy=False):
        """
        You can use the self.array directly but if you want to copy from one array
        into a raster we suggest you do it this way
        :param incomingArray:
        :return:
        """
        masked = isinstance(self.array, np.ma.MaskedArray)
        if copy:
            if masked:
                self.array = np.ma.copy(incomingArray)
            else:
                self.array = np.ma.masked_invalid(incomingArray, copy=True)
        else:
            if masked:
                self.array = incomingArray
            else:
                self.array = np.ma.masked_invalid(incomingArray)

        self.rows = self.array.shape[0]
        self.cols = self.array.shape[1]
        self.min = np.nanmin(self.array)
        self.max = np.nanmax(self.array)

    def write(self, outputRaster):
        """
        Write this raster object to a file. The Raster is closed after this so keep that in mind
        You won't be able to access the raster data after you run this.
        :param outputRaster:
        :return:
        """
        if path.isfile(outputRaster):
            deleteRaster(outputRaster)

        driver = gdal.GetDriverByName('GTiff')
        outRaster = driver.Create(outputRaster, self.cols, self.rows, 1, self.dataType, ['COMPRESS=LZW'])

        # Remember:
        # [0]/* top left x */
        # [1]/* w-e pixel resolution */
        # [2]/* rotation, 0 if image is "north up" */
        # [3]/* top left y */
        # [4]/* rotation, 0 if image is "north up" */
        # [5]/* n-s pixel resolution */
        outRaster.SetGeoTransform([self.left, self.cellWidth, 0, self.top, 0, self.cellHeight])
        outband = outRaster.GetRasterBand(1)

        # Set nans to the original No Data Value
        outband.SetNoDataValue(self.nodata)

        # TODO: Why isn't this working here???
        # self.array.data[np.isnan(self.array)] = self.nodata
        # Any mask that gets passed in here should have masked out elements set to
        # Nodata Value
        if isinstance(self.array, np.ma.MaskedArray):
            np.ma.set_fill_value(self.array, self.nodata)
            outband.WriteArray(self.array.filled())
        else:
            outband.WriteArray(self.array)

        spatialRef = osr.SpatialReference()
        spatialRef.ImportFromWkt(self.proj)

        outRaster.SetProjection(spatialRef.ExportToWkt())
        outband.FlushCache()
        # Important to throw away the srcband
        outband = None
        self.log.debug("Finished Writing Raster: {0}".format(outputRaster))

    def PrintRawArray(self):
        """
        Raw print of raster array values. useful to visualize rasters on the command line
        :return:
        """
        print "\n----------- Raw Array -----------"
        masked = isinstance(self.array, np.ma.MaskedArray)
        for row in range(self.array.shape[0]):
            rowStr = ' '.join(map(str, self.array[row])).replace('-- ', '- ').replace('nan ', '_ ')
            print "{0}:: {1}".format(row, rowStr)
        print "\n"

    def PrintArray(self):
        """
        Print the array flipped if the cellHeight is negative
        useful to visualize rasters on the command line
        :return:
        """
        arr = None
        strFlipped = "False"
        if self.cellHeight >= 0:
            arr = np.flipud(self.array)
            strFlipped = "True"
        else:
            arr = self.array
        print "\n----------- Array Flip: {0} -----------".format(strFlipped)
        masked = isinstance(arr, np.ma.MaskedArray)
        for row in range(arr.shape[0]):
            rowStr = ' '.join(map(str, arr[row])) + ' '
            rowStr = rowStr.replace('-- ', '- ').replace('nan ', '_ ')
            print "{0}:: {1}".format(row, rowStr)
        print "\n"

    def ASCIIPrint(self):
        """
        Print an ASCII representation of the array with an up-down flip if the
        the cell height is negative.

        Int this scenario:
            - '-' means masked
            - '_' means nodata
            - '#' means a number
            - '0' means 0
        :param arr:
        """
        arr = None
        if self.cellHeight >= 0:
            arr = np.flipud(self.array)
        else:
            arr = self.array
        print "\n"
        masked = isinstance(arr, np.ma.MaskedArray)
        for row in range(arr.shape[0]):
            rowStr = ""
            for col in range(arr[row].shape[0]):
                colStr = str(arr[row][col])
                if colStr == 'nan':
                    rowStr+= "_"
                elif masked and arr.mask[row][col]:
                    rowStr += "-"
                elif arr[row][col] == 0:
                    rowStr += "0"
                else:
                    rowStr += "#"
            print "{0}:: {1}".format(row, rowStr)
        print "\n"

def deleteRaster(sFullPath):
    """

    :param path:
    :return:
    """

    log = Logger("Delete Raster")

    if path.isfile(sFullPath):
        try:
            # Delete the raster properly
            driver = gdal.GetDriverByName('GTiff')
            gdal.Driver.Delete(driver, sFullPath)
            log.debug("Raster Successfully Deleted: {0}".format(sFullPath))
        except Exception as e:
            log.error("Failed to remove existing clipped raster at {0}".format(sFullPath))
            raise e
    else:
        log.debug("No raster file to delete at {0}".format(sFullPath))