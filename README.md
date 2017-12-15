# PointCloud2Raster

## Installation

You can use the tool either by cloning this repo or by installing using pip. Then benefit to the pip install method is that you will be able to access and execute `pointcloud2raster` from any location on your machine. 

### Git clone

```bash
git clone git@github.com:NorthArrowResearch/pointcloud2raster.git
```

### Pip install

```bash
pip install git@github.com:NorthArrowResearch/pointcloud2raster.git
```

***NB: installing this way requires that you have git installed and configured in your `PATH` environment variable***

## Using the tool

The tool takes a csv file point cloud as an input and produces a raster as an output.

In order for the raster to have the correct dimensions, projection and cell size you can either pass in another raster as a template or manually specify these fields with the parameters.

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

### Example use


```angular2html
pointcloud2raster mypointcloud.csv mypointcloudraster.tif --templateraster mytemplateraster.tif
```