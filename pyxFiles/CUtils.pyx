from osgeo import gdal
import numpy
cimport numpy
from glob import glob

def makeArray(str imagePath):
    """ Returns an array from the input image path."""
    cdef numpy.ndarray array # define array as ctype
    
    imageExists = (imagePath and len(imagePath)>0 and len(glob(imagePath))>0)
    if (imageExists):
        try:
            image = gdal.Open(imagePath)
            array = image.ReadAsArray()
        except:
            print "Could not open/convert src land use image"
        else:
            print "File: %s successfully read and converted to array." % (imagePath)
    else:
        print "LandUse.makeArray says that the imagePath: %s is not correct" % (imagePath)
    
    # Set dtype for raster
    DTYPE = numpy.uint8
    array.dtype = DTYPE
    return array