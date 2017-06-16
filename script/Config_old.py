# -*- coding: utf-8 -*-
import Utils, CUtils, LandUse, Constants
import copy
import json

def setParams(model):
    """ Here you DEFINE all required input data. """

    model.macroDemand = {
                            # REMEMBER TO COUNT LAND USES AS arr[8:rows-8, 8:cols-8]
                            #1998: {3: 1177, 4: 788}, # data
                            1999: {3: 1180, 4: 800}, # data
                            2000: {3: 1204, 4: 798},
                            2001: {3: 1228, 4: 796},
                            2002: {3: 1252, 4: 794},
                            2003: {3: 1275, 4: 792}, # data
                            2004: {3: 1297, 4: 794},
                            2005: {3: 1319, 4: 797},
                            2006: {3: 1340, 4: 801}, # data
                            2007: {3: 1362, 4: 796},
                            2008: {3: 1384, 4: 791},
                            2009: {3: 1407, 4: 786}, # data
                            2010: {3: 1428, 4: 781},

                            2011: {3: 1452, 4: 776},
                            2012: {3: 1475, 4: 771},
                            2013: {3: 1497, 4: 766},
                            2014: {3: 1519, 4: 761},
                            2015: {3: 1542, 4: 756},
                            2016: {3: 1564, 4: 751},
                            2017: {3: 1587, 4: 746},
                            2018: {3: 1609, 4: 741},
                            2019: {3: 1632, 4: 736},
                            2020: {3: 1654, 4: 731},
                            2021: {3: 1676, 4: 726},
                            2022: {3: 1699, 4: 721},
                            2023: {3: 1721, 4: 716},
                            2024: {3: 1744, 4: 711},
                            2025: {3: 1766, 4: 706},
                            2026: {3: 1789, 4: 701},
                            2027: {3: 1811, 4: 696},
                            2028: {3: 1833, 4: 691},
                            2029: {3: 1856, 4: 686},
                            2030: {3: 1878, 4: 681},
                        }

    model.weights = [0.5, 0.5]

    model.randomFrac = 0.8

    model.neighbourhoodSize = 8

    #model.pathStartLU = "../data/LU_150m/lu98_2_150mr.img"
    model.dictLU = {
                       1998 : "../data/LU_150m/lu98_2_150mr.img",
                       1999 : "../data/LU_150m/lu99_2_150mr",
                       2003 : "../data/LU_150m/lu03_2_150mr",
                       2006 : "../data/LU_150m/lu06_2_150mr",
                       2009 : "../data/LU_150m/lu09_2_150mr"

    }



    model.landUses = {
        0 : {
            'name' : "outside region",
            'type' : "none",
            'color' : (1,1,1),
            'imagePaths' : [],
            'arrayWeights' : []
            },
        1 : {
            'name' : "Jordbruksmark",
            'type' : "vacant",
            'color' : (1,1,0.3),
            'imagePaths' : [],
            'arrayWeights' : []
            },
        2 : {
            'name' : "Skog",
            'type' : "vacant",
            'color' : (0.5,0.5,0),
            'imagePaths' : [],
            'arrayWeights' : []
            },
        3 : {
            'name' : "Stad (Boende & Kommersiell)",
            'type' : "dynamic",
            'color' : (1,0,0),
            'imagePaths' : [],
            'arrayWeights' : []
            },
        4 : {
            'name' : "Stad (Industri)",
            'type' : "dynamic",
            'color' : (0.5,0.5,0.5),
            'imagePaths' : [],
            'arrayWeights' : []
            },
        5 : {
            'name' : "V�gar",
            'type' : "static",
            'color' : (0.1,0.1,0.1),
            'imagePaths' : [],
            'arrayWeights' : []
            },
        6 : {
            'name' : "Park",
            'type' : "static",
            'color' : (0,1,0.2),
            'imagePaths' : [],
            'arrayWeights' : []
            },
        7 : {
            'name' : "Vatten",
            'type' : "static",
            'color' : (0,0.7,1),
            'imagePaths' : [],
            'arrayWeights' : []
            },
        8 : {
            'name' : "Gruva",
            'type' : "static",
            'color' : (0,0.5,0.2),
            'imagePaths' : [],
            'arrayWeights' : []
            }

        }


    model.luNrsOutsideRegion, model.luNrsVac, model.luNrsDyn, model.luNrsStat = getLandUseTypes(model.landUses)

    # ----- Set micro influence
    # Prepare an empty dict containing micro influence (at cell distance) between land uses.
    dictEmpty1 = prepareInfluenceDict(model.landUses.keys(), model.luNrsDyn)
     # Get the user defined nodes.
    model.dictNodes = getInfluenceDefs(dictEmpty1)
    # ----------------------------



def makeLandUseInstances(arrLU, landUses):
    """ Make a land use instance for each unique number (land use) in the startLU array. """

    # Make a dictionary with the raster values as keys
    luDict = Utils.countLandUseInArr(arrLU)
    for i in luDict.keys():
        # Replace the dict value with a new Land Use instance
        lu = landUses[i]
        luInst = LandUse.LandUse(lu['name'], i, lu['type'], lu['color'], lu['imagePaths'], lu['arrayWeights'])
        luDict[i] = luInst # store the instance inside the luDict (keyed by LU nr)
    return luDict

def makeColorTable(arrsLU):
    colorTable = []
    for i in range(len(arrsLU)):
        tuple = arrsLU[i].color
        colorTable.append(tuple)
    return colorTable

def getLandUseTypes(landUses):
    """ Store the LU nrs in arrays, filtered by land use type. """
    luNrsOutsideRegion = []
    luNrsVac = []
    luNrsDyn = []
    luNrsStat = []
    for nr in landUses.keys():
        luType = landUses[nr]["type"]
        if luType=="none":
            luNrsOutsideRegion.append(nr)
        elif luType=="vacant":
            luNrsVac.append(nr)
        elif luType=="dynamic":
            luNrsDyn.append(nr)
        elif luType=="static":
            luNrsStat.append(nr)
    return luNrsOutsideRegion, luNrsVac, luNrsDyn, luNrsStat

# ------------------ MICRO INFLUENCE -------------------------------------

def prepareInfluenceDict(listLuNrs, listDynLus):
    """ Makes an empty 3D-dictionary which can hold lu:s influence at dist:
    infl[targetLu][affLu][dist] = someValue,
    defInfl[targetLu][affLu]["startY"] = someValue """
    # Prepare the influence dictionary
    infl = {}
    listLuNrs.sort()

    # Only changeable lu:s can be changed (not static lu)...
    # Iterate through dynamic land uses
    for cLu in listDynLus: # cLu = "changeable lu"
        # Iterate through all land uses (not 0: outside region).
        # (All land uses can influence the changeable land uses.)
        for iLu in listLuNrs[1:]: # iLu = "influencing lu". Note! Skips 0 because it means "outside region".
            try:
                infl[cLu].update({iLu: {} }) # meaning: append a new dict to infl
            except:
                # if update does not work it means the dict has to be defined, so do that first...
                infl[cLu] = {iLu: {}}
    return infl

def getInfluenceDefs(defInflEmpty):
    # Define the nodes in the linear function describing the influence from iLu (influencing) to tLu (target)
    defInfl = defInflEmpty

    # E.g. defInfl[tLu][iLu][node]

    # Residential
    defInfl[3][3]["inertia"] = 100000
    defInfl[3][3]["startY"] = 90
    #defInfl[3][3]["middleXY"] = (200, 50)
    defInfl[3][3]["endX"] = 700
    defInfl[3][3]["calibrate"] = True

    # Residential <- Parks
    #defInfl[3][6]["startY"] = 60
    #defInfl[3][6]["middleXY"] = (200,50)
    #defInfl[3][6]["endX"] = 700
    #defInfl[3][3]["calibrate"] = True

    # Residential <- Sea/Water
    defInfl[3][7]["startY"] = 60
    #defInfl[3][7]["middleXY"] = (200, 20)
    defInfl[3][7]["endX"] = 700
    defInfl[3][7]["calibrate"] = True

    defInfl[3][4]["startY"] = -100
    #defInfl[3][4]["middleXY"] = (200,3)
    defInfl[3][4]["endX"] = 200

    # Industry
    defInfl[4][4]["inertia"] = 1700
    defInfl[4][4]["startY"] = 100
    defInfl[4][4]["middleXY"] = (200,10)
    defInfl[4][4]["endX"] = 400
    defInfl[4][4]["calibrate"] = True

    #defInfl[3][4]["startY"] = -10
    #defInfl[3][4]["middleXY"] = (200,-4)
    #defInfl[3][4]["endX"] = 400

    #defInfl[4][3]["startY"] = -2
    #defInfl[4][3]["middleXY"] = (200,-1)
    #defInfl[4][3]["endX"] = 400

    return defInfl

def defineInfluence(dictNodes, emptyDict):

    #defInflEmpty = prepareInfluenceDict(luTable, listDynLus)
    #defInfl = getInfluenceDefs(defInflEmpty) # the dict with nodes

    #infl = prepareInfluenceDict(luTable, listDynLus) # the final dict

    # Iterate through target lu:s
    for tLu in dictNodes.keys():
        # Iterate through influencing lu:s
        for iLu in dictNodes[tLu].keys():
            if iLu==-1:
                emptyDict[tLu][-1] = dictNodes[tLu][-1]
                continue

            inertia = None
            startXY = None
            endXY = None
            middleXY = None

            # if not defined an empty dict will still exist
            if dictNodes[tLu][iLu] != {}:
                startXY = (100, dictNodes[tLu][iLu]["startY"])
                endXY = (dictNodes[tLu][iLu]["endX"], 0)
                try:
                    middleXY = dictNodes[tLu][iLu]["middleXY"]
                except KeyError:
                    pass
                try:
                    inertia = dictNodes[tLu][iLu]["inertia"]
                except:
                    inertia = None

            if startXY and endXY:
                # Make a list from the distances keys and...
                distXs = Constants.distances.keys()

                # Send the list and the values to the "linear function creator"
                distInfl = Utils.makeLinearFunc(distXs, startXY, endXY, middleXY)
                for dist in distInfl.keys():
                    emptyDict[tLu][iLu][dist] = distInfl[dist]
            # Add inertia
            if inertia:
                emptyDict[tLu][iLu]["inertia"] = inertia

    return emptyDict

# ------------ END ------- MICRO INFLUENCE -------------------------------------

def makeCalArrs(dictCalLU):
    """ Make arrays out of the paths """
    for y in dictCalLU.keys():
        path = dictCalLU[y]
        dictCalLU[y] = Utils.makeArray(path)
    return dictCalLU

def getYearsAsList(macroDemand, startYear, endYear):
    """ Return a sorted list containing only the years (or "time steps"). """

    years = macroDemand.keys()
    years.sort()
    startIndex = years.index(startYear)
    endIndex = years.index(endYear)
    listYears = years[startIndex : endIndex + 1]
    return listYears



def configure(model):
    # Starting land use
    model.arrStartLU = CUtils.makeArray(model.dictLU[ min(model.dictLU.keys()) ]) # make starting LU arr to the one with lowest year
    model.arrCurLU = model.arrStartLU
    model.shape = model.arrStartLU.shape
    model.rows = model.arrStartLU.shape[0] # sets the rule for all other arrays
    model.cols = model.arrStartLU.shape[1] # sets the rule for all other arrays
    model.nrCells = model.arrStartLU.size

    # Calibration LU - replace paths with arrays.
    model.dictCalLU = makeCalArrs(model.dictLU)

    # Time
    model.startYear = min(model.macroDemand.keys())
    model.endYear = max(model.macroDemand.keys())
    model.curYear = min(model.macroDemand.keys())
    model.stepSize = (model.endYear - model.startYear + 1) / len(model.macroDemand.keys())
    model.years = getYearsAsList(model.macroDemand, model.startYear, model.endYear)


    # Make the land use instances - all the land uses, with associated rasters
    # and other data, keyed by the land use number.
    model.LU = makeLandUseInstances(model.arrStartLU, model.landUses)

    # The colorTable used by maplotLib
    model.colorTable = makeColorTable(model.LU)

    # --------- Micro influence --------------------------------------------------------------------

    dictEmpty2 = prepareInfluenceDict(model.landUses.keys(), model.luNrsDyn)
    # Fill the values in-between the user defined nodes. (First create another empty dict to hold these values)
    #dictEmpty2 = prepareInfluenceDict(model.landUses.keys(), model.luNrsDyn) # dictEmpty2 becomes the final dict
    model.microInfl = defineInfluence(model.dictNodes, dictEmpty2)

    # ------ END - Micro influence --------------------------------------------------------------------


if __name__=='__main__':
    pass
