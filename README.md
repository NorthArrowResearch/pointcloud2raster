# PointCloud2Raster

```
usage: pointcloud2raster [-h] [--cellsize CELLSIZE] [--xfield XFIELD]
                         [--yfield YFIELD] [--zfield ZFIELD]
                         [--templateraster TEMPLATERASTER] [--verbose]
                         csvfile outputRaster

positional arguments:
  csvfile               Path to the input CSV pointcloud file.
  outputRaster          Path to the desired output Raster file.

optional arguments:
  -h, --help            show this help message and exit
  --cellsize CELLSIZE   column number to use for Y (defaults to 2 feet)
  --xfield XFIELD       column number to use for Y (defaults to 2)
  --yfield YFIELD       column number to use for Z (defaults to 3)
  --zfield ZFIELD       column number to use for X (defaults to 1)
  --templateraster TEMPLATERASTER
                        Template Raster to use for meta values
  --verbose             Get more information in your logs.
```