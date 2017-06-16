from operator import itemgetter
import copy
import random
import os, sys
sys.path.append( "../pyxFiles" )

# import model scripts
import Constants, Config, Model, Utils
from PIL import Image

import matplotlib
import matplotlib.pyplot as plt
#import matplotlib.cm as cm
from matplotlib.colors import ListedColormap


class Calibration:
    def __init__(self):
        self.yStepMin = 1
        self.yStepMax = 20

        self.xStepMin = 1
        self.xStepMax = 8

        self.yStepMinOld = self.yStepMin
        self.yStepMaxOld = self.yStepMax

        self.xStepMinOld = self.xStepMin
        self.xStepMaxOld = self.xStepMax


        self.yStepIncrease = 5
        self.xStepIncrease = 2

        self.acceptedNoneImprovements = 20
        self.localMinimumMaxRuns = 6

        self.successSound = r"C:\WINDOWS\Media\chimes.wav"
        self.failureSound = r"C:\WINDOWS\Media\chord.wav"


    def checkPerformance(self, arrCalc, arrAct):

        fArr1, fScore1 = Utils.getFuzzyValue(arrCalc, arrAct, nSize=2)
        fArr2, fScore2 = Utils.getFuzzyValue(arrAct, arrCalc, nSize=2, banList=[0,1,2,5,6,7,8])

        fScore = (fScore1 + fScore2) / 2.0

        #errors = Utils.compareArrs(arrCalc, arrAct)
        return fScore

    def pickTargetLU(self):
        random.shuffle(self.model.luNrsDyn)
        tLu = self.model.luNrsDyn[0]
        return tLu

    def pickInfluencingLU(self, tLu):
        """ Pick a random tLu from the possible influencing LU:s """

        iLusDict = self.model.config["microInfluence"][tLu]
        iLus = iLusDict.keys()
        random.shuffle(iLus)
        for lu in iLus:
            shouldBeCalibrated = iLusDict[lu]["calibrate"]
            if shouldBeCalibrated==True:
                return lu

    def makeSets(self, defInfl):

        distList = Constants.distances.keys()
        distList.sort()

        # Get a random selected tLu and iLu
        tLu = self.pickTargetLU()
        iLu = self.pickInfluencingLU(tLu)


        sets = []

        for nodeType in ["inertia", "startY", "middleXY", "endX"]:

            # Get a random step size (within range)
            stepSizeX = random.randrange(self.xStepMin, self.xStepMax+1)
            stepSizeY = random.uniform(self.yStepMin, self.yStepMax)

            try:
                oldNode = defInfl[tLu][iLu][nodeType] # Get existing node
            except:
                oldNode = None

            # Change the nodeType in this set in two directions (+/-)
            for i in [1, -1]:

                if nodeType=="startY":
                    set = copy.deepcopy(defInfl)
                    set[tLu][iLu][nodeType] = oldNode + (stepSizeY * i)
                    sets.append(set)

                elif nodeType=="inertia" and oldNode!=None:
                    set = copy.deepcopy(defInfl)
                    set[tLu][iLu][nodeType] = oldNode + (stepSizeY * i)
                    sets.append(set)


                elif nodeType=="middleXY":
                    # Make two sets
                    setX = copy.deepcopy(defInfl)
                    setY = copy.deepcopy(defInfl)

                    # x for middle cannot be higher than the last node "endX"
                    endX = defInfl[tLu][iLu]["endX"]
                    indexEndX = distList.index(endX)

                    # Change the X-value
                    oldX = oldNode[0]
                    oldIndex = distList.index(oldX)
                    newIndex = oldIndex + (stepSizeX * i)
                    if newIndex<=1 or newIndex>28 or newIndex >= indexEndX:
                        continue
                        #newIndex = oldIndex

                    newX = distList[newIndex]
                    setX[tLu][iLu][nodeType][0] = newX

                    # Change the Y-value
                    oldY = oldNode[1]
                    setY[tLu][iLu][nodeType][1] = oldY + (stepSizeY * i)

                    # Append sets
                    sets.append(setX)
                    sets.append(setY)

                elif nodeType=="endX":
                    set = copy.deepcopy(defInfl)

                    # x for endX cannot be lower than the middle node
                    middleX = defInfl[tLu][iLu]["middleXY"][0]
                    indexMiddleX = distList.index(middleX)

                    oldX = oldNode
                    oldIndex = distList.index(oldX)
                    newIndex = oldIndex + (stepSizeX * i)
                    if newIndex<=1 or newIndex>28 or newIndex <= indexMiddleX:
                        continue
                        #newIndex = oldIndex

                    newX = distList[newIndex]
                    set[tLu][iLu][nodeType] = newX

                    sets.append(set)

        return sets


    def testSets(self, sets, startYear, endYear):
        bestScore = 0
        bestCalcArr = None
        bestSet = None

        # Run the model with all sets. Return the set from the best one,
        # together with its calc array and performance.

        setNr = 0
        for set in sets:
            setNr += 1

            self.runModel(startYear, endYear, set)
            arrCalc = self.model.arrCurLU.copy()
            score = self.checkPerformance(arrCalc, self.arrAct)
            if score > bestScore:
                bestScore = score
                bestCalcArr = arrCalc
                bestSet = copy.deepcopy(set)

            print "Score this set: ", score, set

            savePath = "../output/arrCalc_%i_%i.png" % (self.runNr, setNr)
            palette = Utils.makeLandUsePalette(self.model.config["landUses"])
            Utils.saveArrAsImage(arrCalc, savePath, palette)

        return bestSet, bestScore, arrCalc

    def initModel(self, startYear, endYear):
        self.model = Model.Model()
        self.model.setParams()

        # Take away the old mine (coded as industrial) and replace by mining land use
        self.model.arrStartLU = Utils.findAndReplace(self.model.arrStartLU, find=[4], replaceWith=8, within=[(45,15),(61,31)])
        self.model.arrCurLU = self.model.arrStartLU.copy()

        for year in range(startYear+1, endYear+1):
            self.model.curYear = year
            self.model.calcLandUse()

    def runModel(self, startYear, endYear, defInfl):
        """ Calculate influence graphs from nodes and run
        the model from startYear to endYear. Do nothing else... """

        #self.model = Model.Model()
        #self.model.setParams()

        self.model.resetYear(startYear)

        #Config.calcInfluenceGraphs(defInfl, self.model.LU.keys(), self.model.luNrsDyn)
        Config.setMicroInfluence(self.model, defInfl, self.model.luNrsAll)

        for year in range(startYear+1, endYear+1):
            self.model.curYear = year
            self.model.calcLandUse();



    def writeToConsole(self, text):
        textFile = open("../output/resultFile.txt", "a")
        textFile.write(text)
        textFile.close()


    def calibrate(self, startYear, endYear, runs):
        textFile = open("../output/resultFile.txt", "w")

        self.localMinimumRunNr = 0

        self.noneImprovements = 0
        self.bestSets = [] # Stores the best set of each run IF it's better than last run

        # Run the model once to get a first result
        self.initModel(startYear, endYear)

        # Compare performance using this array, but first take away the mine...
        self.model.luDict[endYear] = Utils.findAndReplace(self.model.luDict[endYear], find=[4], replaceWith=8, within=[(45,15),(61,31)])
        self.model.luDict[startYear] = Utils.findAndReplace(self.model.luDict[startYear], find=[4], replaceWith=8, within=[(45,15),(61,31)])
        self.arrAct = self.model.luDict[endYear]

        # Save the actual land use so that we can compare.
        savePath = "../output/arrActual.png"
        palette = Utils.makeLandUsePalette(self.model.config["landUses"])
        Utils.saveArrAsImage(self.arrAct, savePath, palette)

        bestScore = self.checkPerformance(self.model.arrCurLU, self.arrAct)

        defInfl = self.model.config["microInfluence"]

        consoleString = "Starting calibration using these settings:"+\
                            "\nacceptedNoneImprovements\t"+str(self.acceptedNoneImprovements)+\
                            "\nyStepMin\t"+str(self.yStepMin)+\
                            "\nyStepMax\t"+str(self.yStepMax)+\
                            "\nxStepMin\t"+str(self.xStepMin)+\
                            "\nxStepMax\t"+str(self.xStepMax)+\
                            "\nyStepIncrease\t"+ str(self.yStepIncrease)+\
                            "\nxStepIncrease\t"+ str(self.xStepIncrease)+\
                            "\nStarting error\t"+str(bestScore)

        self.writeToConsole(consoleString)


        self.runNr = 0
        for run in range(runs):
            self.runNr += 1

            print "******* Starting run %i *******" %(run+1)
            # Make new sets based on the current set
            sets = self.makeSets(defInfl)

            print "sets length %i" %(len(sets))

            # Test the sets (run the model).
            bestSet, score, arrCurLU = self.testSets(sets, startYear, endYear)

            print "bestSet: ", bestSet


            # Compare the best performing set with the performance of previous run
            if score > bestScore:
                print "Improvement!\nOld:\t%f\nNew:\t%f" %(bestScore, score)
                #winsound.PlaySound(self.successSound, winsound.SND_FILENAME)


                # Reset some parameters
                self.noneImprovements = 0
                self.localMinimumRunNr = 0

                # Go back normal step size - since we seem to have escaped this local minimum
                ##self.yStepMin = self.yStepMinOld
                ##self.yStepMax = self.yStepMaxOld
                ##self.xStepMin = self.xStepMinOld
                ##self.xStepMax = self.xStepMaxOld

                # Keep it for next run!
                bestScore = score
                defInfl = bestSet
                self.model.defInfl = bestSet
                self.bestSets.append(bestSet)

            else:
                print "No improvement\nOld:\t%f\nNew:\t%f" %(bestScore, score)
                #winsound.PlaySound(self.failureSound, winsound.SND_FILENAME)

                # Keep the defInfl from last run
                self.noneImprovements += 1
                print "Number of noneImprovements:",  self.noneImprovements


                if self.noneImprovements >= self.acceptedNoneImprovements:

                    # Use the current best set although it did not beat the record.
                    # For an allowed number of runs the model will allow worse
                    # sets than the record. This is to escape the local minimum.
                    # If no new record after the allowed number of runs, the
                    # model will repeat this, but starting with the best set a few
                    # items ahead of the last best set.

                    # Increase the range of search

                    if self.localMinimumRunNr < self.localMinimumMaxRuns:
                        # Continue the current "local minimum" run
                        self.localMinimumRunNr += 1
                        defInfl = bestSet
                        self.model.defInfl = bestSet # Use the best set from the test (although worse than record)
                    else:
                        # Start another "local minimum" run using a new start set
                        self.localMinimumRunNr = 0
                        defInfl = copy.deepcopy(self.bestSets[-1]) # Use the record set and try again
                        self.model.defInfl = defInfl

                    print "local min run nr", self.localMinimumRunNr

            print "\nBest set ever:", bestSet
            self.writeToConsole(str(score)+"\n")
            # If worse - restore the old set.
            # Also check how many none-improvements has occurred. If too many,
            # restore the set a bit before the none-improvement happened (ca 20 steps).

            print "self.yStepMin\tself.yStepMax\tself.xStepMin\tself.xStepMax"
            print self.yStepMin, "\t", self.yStepMax, "\t", self.xStepMin, "\t", self.xStepMax


if __name__=="__main__":
    calib = Calibration()
    calib.calibrate(1998, 2009, runs=2)
    #plt.show()


