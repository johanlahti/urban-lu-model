from operator import itemgetter
import copy
import random

# import model scripts
import Constants, Config, Model, Utils


class Calibration:
    def __init__(self):
        self.yFactor = 1
        self.xFactor = 0.05

#    def getPot(self):
#        pass
#
#    def getCoordsForMinPotError(self, potDiffArr):
#        """ Returns the coordinates of the cell
#        with the lowest potential error. If many with
#        same potential error - choose one randomly. """
#
#        minVal = potDiffArr.min() # lowest potential error (difference)
#        sortArr = potDiffArr.argsort()
#        minColIndex = sortArr[0]
#        row=0
#        minCoordsList = []
#        for col in sortArr:
#            val = potArr[row, col]
#            if val<=minVal:
#                minCoordsList.append([col, row])
#            row+=1
#
#        # So now we have a list with the coordinates for the lowest
#        # potential values 'minCoordsList' and the lowest value 'minVal'.
#        # Return a random value if many...
#        numpy.random.shuffle(minCoordsList)
#        coords = minCoordsList[0]
#
#        return coords, minVal
#
#    def makePotDiffArr(self, errLUCoords, potArrs):
#        """ Makes an array which holds the difference in potential
#        between calculated and actual potential arrays. The difference
#        means the amount of potential needed to add to the calculated
#        land use in order to make the actual (correct) LU take over"""
#
#        for item in errLUCoords:
#            row = item[0]
#            col = item[1]
#            luAct = item[2]
#            luCalc = item[3]
#            potActLU = potArrs[luAct][row, col]
#            potCalcLU = potArrs[luCalc][row, col]
#            potDiff = potCalcLU - potActLU

    # -------------------------------------------------------------------------

    def getLowestPot(self, potArrs, arrStart, arrCalc, rows, cols):
        """ Get the lowest potential ("border line") for each dynamic land use. """

        """ Find out which of the dynamic land uses have changed from original
        land use arr. Then, get the lowest potential for each dynamic land use
        which has changed."""

        lowestPotDict = {}
        pot = None
        #errorArr = arrStart - arrCalc
        dynNrsLU = potArrs.keys() # dynamic land use numbers


        #print Utils.countLandUseInArr(potArrs[3])

        for row in range(8, rows-8):
            for col in range(8, cols-8):
                #luDiff = errorArr[row, col]
                luDiff = arrStart[row, col] - arrCalc[row, col]


                if luDiff not in [0, 255]:
                    # Aha, this cell has changed!

                    # Check the potential of the luCalc.
                    # Remember that we want the lowest potential for
                    # transformation to this land use type.
                    luCalc = arrCalc[row, col]


                    # if luCalc is a dynamic LU, then see if its potential was lower
                    # than previously registered potential of the same LU type.
                    if luCalc in dynNrsLU:
                        pot = potArrs[luCalc][row, col] # get potential for calculated land use
                        try:
                            lowestSoFar = lowestPotDict[luCalc]
                        except:
                            lowestPotDict[luCalc] = pot # in case no lowest potential for this LU number has been registered...
                        else:
                            if (pot < lowestSoFar):
                                # This pot is the lowest potential so far for this land use number
                                lowestPotDict[luCalc] = pot


        return lowestPotDict


    def getErrorList(self, lowestPotDict, arrAct, arrCalc, potArrs, rows, cols):
        """ Returns a list with the coords and lu value
        [row, col, lu_calc]) of all error LUs (calculated) """

        #errorArr = arrAct - arrCalc # all non-zero/non-255 values are error
        errLUs = []

        i = 0
        for row in range(8, rows - 8):
            for col in range(8, cols - 8):
                #luDiff = errorArr[row, col]
                luDiff = arrAct[row, col] - arrCalc[row, col]


                # Only append LUs which are wrong
                if luDiff not in [0, 255]:

                    luCalc = arrCalc[row, col] # error calc lu - must decrease OR...
                    luAct = arrAct[row, col] # actual lu - must increase

                    #print "luCalc", luCalc, "luAct", luAct, "row col", row, col

                    # dirOfChange: The direction we want the land use 'lu' to go... only required if pot is 0 otherwise derived from operator (-/+)
                    dirOfChange = None

                    # Get the potential for either (start with 1st):
                    #     1. calculated land use (which got too high pot), or
                    #     2. actual land use (which got too low pot)
                    try:
                        pot = potArrs[luCalc][row, col]
                        lu = luCalc
                        dirOfChange = -1
                    except:
                        # if lu is a dynamic land use, a lowest pot can be found - else continue loop
                        try:
                            pot = potArrs[luAct][row, col]
                            lu = luAct
                            dirOfChange = 1
                        except:
                            continue

                    lowestPot = lowestPotDict[lu] # get the lowest pot for this dynamic LU
                    potDiff = lowestPotDict[lu] - pot # answers: "How far is it to make this land use disappear?"
                    if potDiff==0:
                        potDiff += dirOfChange # 0 means the lu has to increase in potential go above existing.
                    errLUs.append([ row, col, lu, potDiff, potDiff.__abs__() ]) # [ row, col, error_land_use, pot_distance_to_correct, abs(pot_distance_to_correct) ]
                    i += 1
        print "Number of errors: ", i

        # Sort list according to pot difference. Lowest potDiff first...
        errLUs.sort(key=itemgetter(-1))
        return errLUs



    def makeCandidateSets(self, leastErrorCell, defInfl):
        """ Adjust the neighbourhood influence for the leastErrorCell
        so that its potential passes the border number. """




        tLu = leastErrorCell[2]
        potDiff = leastErrorCell[-2]

        if potDiff<0:
            oper = "INcrease"
        else:
            oper = "DEcrease"
        print "LU", tLu, "HAS TO:", oper


        # ---- Decrease luCalc's potential ------

        # Find dynamic LU's influencing LUs and the one/those which should be calibrated.
        listInflLU = defInfl[tLu].keys()
        listCalLU = [] # a list of the land uses who's influence function (defInfl) should be calibrated

        # Get the land uses which should be calibrated in order to change error land use 'lu'
        for iLu in listInflLU:
            try:
                shouldBeCalibrated = defInfl[tLu][iLu]["calibrate"]
                # If this influencing LU should be calibrated, append its LU nr.
                if (shouldBeCalibrated==True):
                    listCalLU.append(iLu)
            except:
                pass

        # Now let's create some candidate calibration sets
        defSets = [] # contains defInfl dicts
        distList = Constants.distances.keys()
        distList.sort()

        yFactor = self.yFactor # value change
        xFactor = self.xFactor # dist index change

        # Loop through all land uses influencing luAct or luCalc
        # (only those which should be calibrated) and change their
        # influence XX percent or one distance step.
        # Note! Preferably, there is only one calibratable land use
        # for each land use.

        for iLu in listCalLU:
            for nodeType in ["startY", "middleXY", "endX"]: # ["inertia",
                defInflCand = copy.deepcopy(defInfl) # Make a new defInfl for each candidate set
                oldVal = defInfl[tLu][iLu][nodeType]

                oldIndex = None # for x (dist)
                yChange = None # for y

                oldX = None
                oldY = None

                newX = None # new dist
                newY = None # new y

                if nodeType=="middleXY":
                    oldX = oldVal[0] # middleX
                    oldY = oldVal[1] # middleY

                elif nodeType=="endX":
                    oldX = oldVal

                elif nodeType=="startY":
                    oldY = oldVal

                # -----------------------------

                if oldY:
                    # Increase/Decrease the oldY by a percentage of yFactor
                    yChange = yFactor * oldY
                    # if pot should be decreased - make attraction to a negative number
                    if potDiff>0:
                        yChange = -yChange
                    newY = oldY + yChange
                    print "oldY->newY: ", oldY, "->", newY

                if oldX:
                    oldIndex = distList.index(oldX) # get the index for distance x
                    if potDiff>0:
                        xFactor = -xFactor
                    newIndex = oldIndex + xFactor # new dist index

                    print "old->newIndex: ", oldIndex, "->", newIndex
                    maxIndex = len(distList)-1

                    # If index is out of range - use the old index.
                    if newIndex > maxIndex or newIndex < 0:
                        newIndex = oldIndex
                    newX = distList[newIndex] # new dist

                # -------------------------------
                if nodeType=="startY":
                    defInflCand[tLu][iLu][nodeType] = newY
                    defSets.append(defInflCand)
                elif nodeType=="endX":
                    if newX > 141 and newX <= 800:
                        defInflCand[tLu][iLu][nodeType] = newX
                        defSets.append(defInflCand)
                elif nodeType=="middleXY":
                    if newX >= 141 and newX < 800:
                        defInflCand[tLu][iLu][nodeType] = (newX, oldY)
                        defSets.append(defInflCand)
                    defInflCand2 = copy.deepcopy(defInfl) # Make a new defInfl
                    defInflCand2[tLu][iLu][nodeType] = (oldX, newY)
                    defSets.append(defInflCand2)


        print "defSets from makeCandidateSets: ", defSets

        return defSets


    def makeSets(self, defSets):
        """ Fill in the intermediate values from the defSets """

        sets = [] # will contain sets ready to be tested in model runs

        dictEmpty = Config.prepareInfluenceDict(self.model.LU.keys(), self.model.luNrsDyn)
        for defSet in defSets:
            dictEmptyTemp = copy.deepcopy(dictEmpty)
            set = Config.defineInfluence(defSet, dictEmptyTemp)
            sets.append(set)

        return sets


    def testSets(self, leastErrorCell, defSets, startYear, endYear):
        """
            @param defSets {List}
                All sets
            @param startYear {Integer}
            @param endYear {Integer}
                The year towards which we will run the model.
                We will also compare the model output with
                actual land use for this year.
            @param recordPercent {Number}
                If one of the defSet's gives a better result than this
                it's defSet will be returned. Otherwise False will be
                returned. """

        firstCalcYear = startYear + 1
        defInfl = None
        infl = None


        bestPercent = 0.0
        for defSet in defSets:
            # calibrate towards the land use array of calibration year, and start from model starting year.


            # just for printing
            """for tLu in defSet.keys():
                for iLu in defSet[tLu].keys():
                    print str(tLu) + "<-" + str(iLu)
                    for nType in ["startY", "middleXY", "endX"]:
                        try:
                            val = defSet[tLu][iLu][nType]
                            if (val):
                                print nType, val
                                val = None
                        except:
                            pass"""


            # Run the model from startYear to endYear...
            self.runModel(defSet, startYear, endYear)


            # Find out if our cell became OK
            row = leastErrorCell[0]
            col = leastErrorCell[1]
            isCorrect = (self.model.arrCurLU[row, col] == self.model.luDict[endYear][row, col])

            # Store the defSet of the best performing one... and also the model
            #percentCorrect = Utils.compareArrs(self.model.arrCurLU, self.model.luDict[endYear])
            #if percentCorrect >= bestPercent:
            #    bestDefSet = defSet
            #    bestModel = copy.deepcopy(self.model)
            #models.append(copy.deepcopy(self.model))


            # If it became correct - then don't try more sets...
            if isCorrect==True:
                print "The cell is now correct! defSet: ", defSet
                break

        if isCorrect!=True:
            random.shuffle(defSets)
            defSet = defSets[0]

        return isCorrect, defSet


    def initModel(self, startYear, endYear):
        self.model = Model.Model()
        self.model.setParams()

        # Take away the old mine (coded as industrial) and replace by mining land use
        self.model.arrStartLU = Utils.findAndReplace(self.model.arrStartLU, find=[4], replaceWith=8, within=[(45,15),(61,31)])

        for year in range(startYear + 1, endYear+1):
            self.model.curYear = year
            self.model.calcLandUse()

        # When the calibration year has been reached - check percent correct
        #percentCorrect = Utils.compareArrs(self.model.arrCurLU, self.model.luDict[endYear])
        #return percentCorrect


    def runModel(self, startYear, endYear, defInfl):
        """ Calculate influence graphs from nodes and run
        the model from startYear to endYear. Do nothing else... """

        self.model.resetYear(startYear)

        # Take away the old mine (coded as industrial) and replace by mining land use
        self.model.arrStartLU = Utils.findAndReplace(self.model.arrStartLU, find=[4], replaceWith=8, within=[(45,15),(61,31)])

        Config.setMicroInfluence(self.model, defInfl, self.model.luNrsAll)

        for year in range(startYear+1, endYear+1):
            self.model.curYear = year
            self.model.calcLandUse();


    def getLeastErrorCell(self, errLUs):
        # Find the land use type to process. Loop through errLUs
        # until it finds one LU which is not in the list self.banList.
        # If all LUs are banned - don't do this since it would end the
        # calibration.
        leastErrorCell=None

        if self.model.luNrsDyn.sort()==self.banList.sort():
            leastErrorCell = errLUs[0]
            self.banList = [] # empty list
            print "all cells banned - taking the first item"
        else:
            leastErrorCell = None
        q=0
        while leastErrorCell==None:
            if errLUs[q][2] not in self.banList:
                leastErrorCell = errLUs[q]
            q+=1

        return leastErrorCell

    def calibrate(self, startYear, endYear):
        """ startYear and endYear must have a land use array in the luDict. """

        # Make an instance of the Model class and set its parameters.
        # It will run once so that we get some output to analyze!
        self.initModel(startYear, endYear)

        self.model.luDict[endYear] = Utils.findAndReplace(self.model.luDict[endYear], find=[4], replaceWith=8, within=[(45,15),(61,31)])

        # Used when finding out which cells we don't need to analyze -
        # i.e. those cells which
        arrStart = self.model.luDict[startYear]

        # Get the first performance and store its settings.
        oldPercentCorrect = Utils.compareArrs(self.model.arrCurLU, self.model.luDict[endYear])
        oldDefInfl = self.model.defInfl
        oldMicroInfl = self.model.microInfl
        oldPotArrs = copy.deepcopy(self.model.potArrs)


        print "\nStarting defSet: ", oldDefInfl

        # Fetch the output...
        oldArrCalc = self.model.arrCurLU

        # ...and the real data to compare our output against.
        arrAct = self.model.luDict[endYear] # land use array ex. {1998 : luArr98, ...}

        # The banList contains land use numbers for the land use(s) which has
        # been tested but with no success. By changing the graphs affecting
        # this land use, so that the land use becomes replaced by the correct
        # land use, did not give a better global result.
        self.banList = []

        runs = 5
        run = 0
        for y in range(runs):
            run +=1
            print "\n\n ******** Starting run %i ******" %(run)



            # Now - lets compare these two arrays to find one cell which
            # was erroneously predicted - but nearest to become correct!

            lowestPotDict = self.getLowestPot(oldPotArrs, arrStart, oldArrCalc, self.model.rows, self.model.cols)
            print "\n\nlowestPotDict", lowestPotDict, "\n\n"

            errLUs = self.getErrorList(lowestPotDict, arrAct, oldArrCalc, oldPotArrs, self.model.rows, self.model.cols)
            print "errLUs", errLUs
            leastErrorCell = self.getLeastErrorCell(errLUs)

            # Tweak all three nodes in the two graphs a little bit until
            # our cell becomes correct.
            ok = False
            defInfl = copy.deepcopy(oldDefInfl) # Start using the oldDefInfl
            while ok==False:

                # Make 5 sets of new graphs with tweaked parameters.
                defSets = self.makeCandidateSets(leastErrorCell, defInfl) # new set

                # Run the model with these candidate sets (graphs) to see
                # if any of them can make our cell become OK.
                ok, defInfl = self.testSets(leastErrorCell, defSets, startYear, endYear)

                print "\nCELL is still not ok: defInfl", defInfl

                # The while-loop continues using a new set of defInfl so that
                # we can tweak their nodes another little bit more.

            #oldDefInfl = copy.deepcopy(defInfl) # Store the defInfl which managed to change the cell, for the next run - even if it does not improve global result

            # When the cell finally got correct we want to know - did
            # the overall (global) result improve? If not - keep the
            # old graphs.
            newPercentCorrect = Utils.compareArrs(self.model.arrCurLU, self.model.luDict[endYear]) # OBS! fix the mine in actual land use!!


            print "newPercentCorrect <-> oldPercentCorrect: ", newPercentCorrect, "<->", oldPercentCorrect

            if newPercentCorrect > oldPercentCorrect:
                print "\nHALLELUJA - we got an improvement"

                # Improvement! -> DO NOT replace new model settings by old.
                oldPercentCorrect = newPercentCorrect # of course, save the new record for next run!
                oldDefInfl = copy.deepcopy(self.model.defInfl)
                oldMicroInfl = copy.deepcopy(self.model.microInfl)
                oldPotArrs = copy.deepcopy(self.model.potArrs)

                oldArrCalc = copy.deepcopy(self.model.arrCurLU) # Store the calculated output for the best

                self.banList = [] # Empty the banList

            else:
                print "\nOOOPS - no improvement... lets try another run"
                # No improvement -> replace new model settings
                self.model.defInfl = copy.deepcopy(oldDefInfl)
                self.model.microInfl = copy.deepcopy(oldMicroInfl)
                self.banList.append(leastErrorCell[2]) # this LU number will not be selected again



if __name__=="__main__":
    calib = Calibration()
    calib.calibrate(1998, 2003)
    #plt.show()


