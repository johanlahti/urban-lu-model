# -*- coding: cp1252 -*-
import numpy
import matplotlib
import matplotlib.pyplot as plt
#import matplotlib.cm as cm
from matplotlib.colors import ListedColormap
#import time
#import random
import CMicroInfluence
import CMacroDemand
import Config
import Utils
import copy

class Model:
    """ The model - calculates and returns a land use array for each time step. """
    def __init__(self, config=None):
        pass

    def __str__(self):
        info = "This is an instance of the CA model class"
        return info

    def setParams(self):
        Config.setParams(self)

    def addOtherArrs(self, potArrs):
        weights = self.config["weights"]

        # Define arrs like this so that if the array does not exist
        # it will not affect the calculation
        arrZoning = 0 # value 0 or 1
        arrSuit = 0 # value interval -5 to 5
        arrAccess = 0 # value interval 0 to 10

        print potArrs[3].shape
        print self.arrAccess.shape
        """
        for lu in potArrs.keys():
            try: arrZoning = self.LU[lu].arrZoning
            except: pass

            try: arrSuit = weights["suitability"] * self.LU[lu].arrSuit
            except: pass

            try: arrAccess = weights["accessibility"] * self.arrAccess
            except: pass

            potArrs[lu] = arrZoning * (weights["CA"] * potArrs[lu]) + arrSuit + arrAccess

        return potArrs"""


    def calcPotArrs(self):
        """ For each dynamic land use - calculate an array which gives the potential of growth. """
        self.potArrs = CMicroInfluence.makePotentialArrs(self.arrCurLU, self.rows, self.cols, self.microInfl, self.luNrsDyn, self.luNrsStat, self.maxRand)
        self.potArrs = self.addOtherArrs(self.potArrs)


    def applyMacroDemand(self):
        #print Utils.countLandUseInArr(self.potArrs[3])
        """ Note that this function alters the potArrs values. """
        self.arrCurLU = CMacroDemand.applyMacroDemand(self.macroDemand, self.curYear,\
                                                     self.luNrsDyn, self.luNrsStat,\
                                                     self.potArrs, self.arrCurLU, self.rows, self.cols)

    def calcLandUse(self):
        # Calc this time steps' land use.
        if self.curYear<=self.endYear:
            self.calcPotArrs()
            self.applyMacroDemand()
        else:
            print "Model.calcLandUse says: 'end year has been reached'"

    def calcAndPlotLandUse(self):
        # Calc this time steps' land use if curYear is not higher than end year.
        if self.curYear<=self.endYear:
            self.calcPotArrs()
            self.applyMacroDemand()
            self.plotArr(self.arrCurLU)

            # count LU amounts in the resulting LU array
            #dict = Utils.countLandUseInArr(model.arrCurLU[8:-8,8:-8], filter=[3,4])
            #print "amount 3", dict[3]
            #print "amount 4", dict[4]
            #print "Done"

    def calcNextStep(self):
        if self.curYear<self.endYear:
            # Calc next time steps' land use.
            curYearIndex = self.years.index(self.curYear)
            self.curYear += self.years[curYearIndex+1]
            self.calcLandUse()
            print "Land use calculated for year %i!" % (self.curYear)
        else:
            print "Land use calculation ENDED at year %i!" % (self.curYear)

    def calcNextStepAndPlot(self):
        self.calcNextStep()
        self.plotArr(self.arrCurLU)

    def runModel(self, startYear=None, endYear=None):
        if not startYear: startYear = self.startYear
        else: self.startYear = startYear
        if not endYear: endYear = self.endYear
        else: self.endYear = endYear

        years = Config.getYearsAsList(self.macroDemand, startYear, endYear)

        # Show the first land use map
        self.curYear = startYear
        self.initPlot(self.arrCurLU)
        years = years[1:] # Take away the start year since it's already displayed

        for y in years:
            print "YEAR: ", y
            self.curYear = y
            self.calcAndPlotLandUse()


    def getCurrentLU(self):
        """ Returns the array of current LU. """
        pass

    def initPlot(self, arr, colorTable=None):
        if colorTable==None: colorTable = self.colorTable
        #if not arr.any():
        #    arr = self.arrCurLU

        self.cMap = ListedColormap(colorTable, name="myCMap", N=None)
        self.im = plt.imshow(arr, aspect="equal", cmap=self.cMap,\
                    interpolation="nearest")

        plt.colorbar()
        #self.im.set_cmap('hot')

        self.im.figure.show()

    def plotArr(self, arr, colorTable=None):
        """ Plots the input array or current LU (if not arr) """
        if colorTable==None: colorTable = self.colorTable
        try: arr.any()
        except: arr = self.arrCurLU

        try:
            self.im
        except:
            self.initPlot(arr)
        else:
            # Allow sending in a new colorTable to show new colors.
            self.im.cmap = ListedColormap(colorTable, name="newCMap", N=None)
            self.im.set_data(arr) # Set new data to the plot
            self.im.figure.canvas.draw() # Show it

    def compareArrs(self, arrPredict, arrReal):
        arrDiff = arrReal - arrPredict
        zeros = Utils.countNumberInArr([0], arrDiff)
        percentCorrect = float(zeros) / float(arrDiff.size) * 100
        #print "percentCorrect is %f" % (percentCorrect)
        return percentCorrect


    def resetYear(self, year):
        """ Reset the year and land use map to initial year
        if year not provided - or to the given year (if land
        use array (in calibration dict) exists for this year). """

        self.macroDemand = copy.deepcopy(self.config["macroDemand"]) # Important to reset macro demand since its altered in the code
        self.potArrs = None
        self.startYear = year
        self.curYear = year
        #self.im = None



        self.arrCurLU = self.luDict[year].copy()
        self.arrStartLU = self.luDict[year].copy()

    def resetAll(self):
        """ Restart model from initial state - read all arrays again etc. """
        self.resetYear()
        self.setParams()






if __name__=='__main__':
    import Utils

    model = Model()
    model.setParams()

    # {3: {3: {'endX': 583, 'startY': 28.282294052911926, 'inertia': 1000014.624277354, 'middleXY': [200, 8.0275588539048464], 'calibrate': True}, 6: {'endX': 700, 'startY': 20.0, 'calibrate': False, 'middleXY': [200, 5.0]}, 7: {'endX': 361, 'startY': 32.571320299257764, 'calibrate': True, 'middleXY': [300, 5.0]}}, 4: {4: {'endX': 224, 'startY': 52.293818291930783, 'inertia': 538.06978757564798, 'middleXY': [200, 50.0], 'calibrate': True}}}
    # {3: {3: {'endX': 600, 'startY': -45.142266843469244, 'inertia': 999965.56603029824, 'middleXY': [224, 16.890561025686125], 'calibrate': True}, 6: {'endX': 700, 'startY': 20.0, 'middleXY': [200, 5.0], 'calibrate': False}, 7: {'endX': 781, 'startY': -41.649476914528655, 'middleXY': [539, 11.591782651792633], 'calibrate': True}}, 4: {4: {'endX': 361, 'startY': 63.453254351133594, 'inertia': 423.12543020842639, 'middleXY': [200, 14.988660031481544], 'calibrate': True}}}
    #{3: {3: {'endX': 608, 'startY': 16.685983517099761, 'inertia': 999999.31259816128, 'middleXY': [200, 11.40490076918122], 'calibrate': True}, 6: {'endX': 700, 'startY': 20.0, 'calibrate': False, 'middleXY': [200, 5.0]}, 7: {'endX': 566, 'startY': 15.906512005936282, 'calibrate': True, 'middleXY': [361, 6.2646476181050854]}}, 4: {4: {'endX': 224, 'startY': 106.03950765304029, 'inertia': 518.20122108662486, 'middleXY': [200, 50.0], 'calibrate': True}}}
    Config.setMicroInfluence(model, {3: {3: {'endX': 600, 'startY': -45.142266843469244, 'inertia': 999965.56603029824, 'middleXY': [224, 16.890561025686125], 'calibrate': True}, 6: {'endX': 700, 'startY': 20.0, 'middleXY': [200, 5.0], 'calibrate': False}, 7: {'endX': 781, 'startY': -41.649476914528655, 'middleXY': [539, 11.591782651792633], 'calibrate': True}}, 4: {4: {'endX': 361, 'startY': 63.453254351133594, 'inertia': 423.12543020842639, 'middleXY': [200, 14.988660031481544], 'calibrate': True}}}, model.luNrsAll)



    # Edit land use - take away the old mine which is not in use anymore.
    model.arrStartLU = Utils.findAndReplace(model.arrStartLU, find=[4], replaceWith=8, within=[(45,15),(61,31)])

    #model.runModel(1998, 2010)
    #model.plotArr(model.arrStartLU)

    #model.initPlot(model.arrStartLU)


    for y in range(model.startYear+1, model.endYear+1):
        print "YEAR: ", y
        model.curYear = y
        model.calcAndPlotLandUse()
        print "LU", model.arrCurLU[62,10]
        if model.curYear in model.microInfl.keys():
            percentCorrect = model.compareArrs(model.arrCurLU, model.dictCalLU[model.curYear])

    print "done"
    plt.show()




    #plt.show() # has to be in the end

