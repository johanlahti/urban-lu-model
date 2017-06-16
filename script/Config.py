# -*- coding: utf-8 -*-
import Utils, CUtils, LandUse, Constants
import copy
import json
import os

def readConfigFile():
    path = "config.json"
    configTxt = open(path, "r").read()
    return configTxt

def parseJSON(jsonTxt):
    dec = json.JSONDecoder()
    dict = dec.decode(jsonTxt)
    return dict

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
    for i in arrsLU.keys():
        luInst = arrsLU[i]
        tuple = luInst.color
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

def getYearsAsList(macroDemand, startYear, endYear):
    """ Return a sorted list containing only the years (or "time steps"). """

    years = macroDemand.keys()
    years.sort()
    for i in range(len(years)):
        years[i] = int(years[i])
    startIndex = years.index(startYear)
    endIndex = years.index(endYear)
    listYears = years[startIndex : endIndex + 1]
    return listYears


def prepareInfluenceDict(listLuNrs, listDynLus):
    """ Makes an empty 3D-dictionary which can hold lu:s influence at dist:
    infl[targetLu][affLu][dist] = someValue,
    defInfl[targetLu][affLu]["startY"] = someValue """

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

def calcInfluenceGraphs(defInfl, luKeysList, luNrsDynList):

    emptyDict = prepareInfluenceDict(luKeysList, luNrsDynList)

    # Iterate through target lu:s
    for tLu in defInfl.keys():
        # Iterate through influencing lu:s
        for iLu in defInfl[tLu].keys():
            if iLu == -1:
                emptyDict[tLu][-1] = defInfl[tLu][-1]
                continue

            inertia = None
            startXY = None
            endXY = None
            middleXY = None

            # if not defined an empty dict will still exist
            if defInfl[tLu][iLu] != {}:
                startXY = (100, defInfl[tLu][iLu]["startY"])
                endXY = (defInfl[tLu][iLu]["endX"], 0)
                try:
                    middleXY = defInfl[tLu][iLu]["middleXY"]
                except KeyError:
                    pass
                try:
                    inertia = defInfl[tLu][iLu]["inertia"]
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

def makeArrsLU(luPaths):
    luDict = {}
    for year in luPaths.keys():
        path = luPaths[year]
        luArr = CUtils.makeArray(str(path))

        # Hack! Replace all 255 with 0 in the image
        # print "\n\n\n---%s %s\n\n\n" % (luArr.shape[0], luArr.shape[1])
        luArr = Utils.findAndReplace(luArr, find=[255], replaceWith=0, within=[ (0, 0), (luArr.shape[0], luArr.shape[1]) ])
        
        luDict[year] = luArr
    return luDict


def convertStringKeysToInt(dict):
    if type(dict)==type({}):
        for key in dict.keys():
            if type(key) in [type(u'2323'), type('2323')]:
                val = dict[key]
                try:
                    newKey = int(key)
                except:
                    newKey = str(key)
                finally:
                    del dict[key]
                    dict[newKey] = val
                convertStringKeysToInt(val)


def setParams(self, configTxt=None):
    if configTxt==None:
        configTxt = readConfigFile()
    config = parseJSON(configTxt)
    convertStringKeysToInt(config)

    self.config = config

    # Get the amount of each land use type (vacant, dynamic and static)
    self.luNrsOutsideRegion, self.luNrsVac, self.luNrsDyn, self.luNrsStat = getLandUseTypes(config["landUses"])

    self.luNrsAll = self.luNrsVac + self.luNrsDyn + self.luNrsStat
    self.luNrsAll.sort()

    # luPaths is a dict with year as key and a path to a land use image as a key.
    # Used for calibration as well.
    luPaths = config["landUsePaths"]
    self.luDict = makeArrsLU(luPaths) # {1998 : arrLU98, 1999 : arrLU99 ...}

    self.arrStartLU = CUtils.makeArray( luPaths[min(luPaths.keys())].encode()) # make starting LU arr to the one with lowest year

    # Hack! Replace 255 with 0
    self.arrStartLU = Utils.findAndReplace(self.arrStartLU, find=[255], replaceWith=0, within=[ (0, 0), (self.arrStartLU.shape[0], self.arrStartLU.shape[1]) ])

    self.arrCurLU = self.arrStartLU.copy()


    self.arrAccess = CUtils.makeArray("../data/accessibility/roadsTest150m.img")
    #self.arrAccess = CUtils.makeArray(config["arrPaths"]["accessibility"].encode())
    # print "self.arrAccess shape...", self.arrAccess.shape

    # Get shape of image - all images must have the same shape
    self.shape = self.arrStartLU.shape
    self.rows = self.arrStartLU.shape[0] # sets the rule for all other arrays
    self.cols = self.arrStartLU.shape[1] # sets the rule for all other arrays
    self.nrCells = self.arrStartLU.size

    # Calibration LU - replace paths with arrays.
    #self.dictCalLU = makeCalArrs(self.dictLU)

    # Time
    self.startYear = min(config["macroDemand"].keys())
    self.endYear = config["endYear"]
    self.curYear = self.startYear
    self.stepSize = (config["endYear"] - config["startYear"] + 1) / len(config["macroDemand"].keys())
    self.years = getYearsAsList(config["macroDemand"], config["startYear"], config["endYear"]) # [1998, 1999, 2000, ...]

    self.maxRand = self.config["maxRand"]

    # print config["landUses"]
    self.LU = makeLandUseInstances(self.arrStartLU, config["landUses"])
    print self.LU

    self.colorTable = makeColorTable(self.LU)

    self.macroDemand = copy.deepcopy(config["macroDemand"]) # config["macroDemand"] will be altered in the model so take a copy

    self.defInfl = config["microInfluence"]

    setMicroInfluence(self, self.defInfl, self.luNrsAll)

def setMicroInfluence(model, defInfl, luKeys):
    # Calculate intermediate values for micro influence
    model.microInfl = calcInfluenceGraphs(defInfl, luKeys, model.luNrsDyn)



if __name__=='__main__':
    root = os.path.abspath("../")
    arrAccess = CUtils.makeArray( os.path.join(root, "data/accessibility/roadsTest150m.img") )
    #self.arrAccess = CUtils.makeArray(config["arrPaths"]["accessibility"].encode())
    # print "self.arrAccess shape...", arrAccess.shape
