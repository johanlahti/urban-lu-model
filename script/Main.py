# -*- coding: cp1252 -*-
import numpy
from osgeo import gdal
from Model import *



if __name__=="__main__":
    mod = Model({})

    luTable = { 0:"Utom regionen",
                1:"Jordbruk",
                2:"Skog",
                3:"Stad-Boende-Kommers",
                4:"Stad-Industri",
                5:"Vägar",
                6:"Park",
                7:"Vatten"}

    cTab = [(1,1,1),
            (1,1,0.3),
            (0.5,0.5,0),
            (1,0,0),
            (0.5,0.5,0.5),
            (0.1,0.1,0.1),
            (0,1,0.2),
            (0,0.7,1)]
    img = gdal.Open(r"C:\Projekt\UrbanModel\Data\CurrentData\lu03_2_150mr1.img")
    arr = img.ReadAsArray()
    print "test"