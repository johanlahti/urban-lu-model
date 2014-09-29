# -*- coding: cp1252 -*-

from osgeo import gdal

import CUtils

class LandUse:
    """ An instance of this class will hold all land use types and their:
    -> color
    -> suitability map
    -> accessibility map
    -> zoning map
    -> optional weights for the maps"""
    def __str__(self):
        return "<Instance of the land use class> Name: %s" %(self.name)

    def __init__(self, luName="", val=-1, type="", color=(), imagePaths=[], arrayWeights=[]):
        """ Note that the order of the arrays has to be consequent through the LU:s and the model """
        # Usually arrayPaths should follow this order: arrAccess, arrSuit, arrZoning.
        # All weights should have a sum of 1, even if arrayWeights have a value for zoning.
        #luTypes = {0: "Outside region", 1: "Vacant", 2: "Dynamic", 3: "Static"}

        self.name = luName # the legend name - spaces are allowed
        self.val = val # the integer value (in the array)
        self.type = type # vacant, dynamic or static
        self.color = color # a tuple with length == 3
        self.weights = arrayWeights # Will be used instead of "global" weights (which are same for all LU:s
        if len(imagePaths)>0:
            self.arrs = CUtils.makeArrays(imagePaths)

if __name__=='__main__':
    lu = LandUse("Skog", 3, "dynamic", (0.5,0.5,0), ["../data/sumroads150m", "../data/lu98_2_150mr.img"], [0.5, 0.5])
    for i in lu.arrs:
        print i.shape
