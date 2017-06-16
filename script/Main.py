# -*- coding: utf-8 -*-

import sys, os
sys.path.append("./pyxFiles")
sys.path.append("./script")
import numpy
from osgeo import gdal
from Model import Model



if __name__=="__main__":
    mod = Model({})

    root = os.path.abspath("../")

    luTable = {
                0: "Utom regionen",
                1: "Jordbruk",
                2: "Skog",
                3: "Stad-Boende-Kommers",
                4: "Stad-Industri",
                5: "Vägar",
                6: "Park",
                7: "Vatten"
    }

    cTab = [(1,1,1),
            (1,1,0.3),
            (0.5,0.5,0),
            (1,0,0),
            (0.5,0.5,0.5),
            (0.1,0.1,0.1),
            (0,1,0.2),
            (0,0.7,1)]
    img = gdal.Open( os.path.join(root, r"data/LU_150m/lu03_2_150mr") )
    arr = img.ReadAsArray()
    print arr
    # print "test"