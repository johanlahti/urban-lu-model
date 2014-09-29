# -*- coding: cp1252 -*-
from osgeo import gdal
import numpy
import random
import Utils

def checkMacroDemand(thisYearsMacroDemand):
    tot = 0
    for luNr in thisYearsMacroDemand.keys():
        tot += thisYearsMacroDemand[luNr]
    return tot

def applyMacroDemand(macroDemand, year, luNrsDyn, luNrsStat, potArrs, arrLU):
    """ Make the new land use map by changing the required cells for current time step,
    for the dynamic land uses. """

    n = 8 # neighborhood size

    thisYearsMacroDemand = macroDemand[year]
    #lastYearsMacroDemand = macroDemand[year-1]

    # Make a new arr for the new land use array, where all dynamic LU are replaced by number 1.
    newArrLU = Utils.findAndReplace(arrLU.copy(), find=luNrsDyn, replaceWith=1, within=[(n,n),(-n,-n)])

    # Cut away the surrounding "frame" of neighborhood cells which are not supposed to be calculated.
    for nr in potArrs.keys():
        potArrs[nr] = potArrs[nr][n:-n, n:-n]
        print "max", potArrs[nr].max()
    # This raster keeps track of which land use has been changed already so that it wont change again.
    arrLUChange = numpy.zeros(arrLU.shape, dtype=numpy.integer) # I would like int0/unit0 here instead

    # Iterate
    while checkMacroDemand(thisYearsMacroDemand)>0:
        mx = 0 # int Note! Maybe this should be initialized as None?
        luNr = None # int
        tempMax = None # int
        # Get max value of all potential arrays and find out which array (LuNr) holds it
        for tLu in potArrs.keys():
            # If the land use demand is satisfied for one land use,
            # then don't try to find the potential for this LU. When
            # all LU are satisfied, the loop with stop automatically (see while-statement)
            if thisYearsMacroDemand[tLu]<=0:
                continue
            tempMax = potArrs[tLu].max()
            if tempMax > mx:
                mx = tempMax # save current max val
                luNr = tLu # save lu (which has the highest potential)
        if luNr==None:
            print "Breaking when macroDemandStatus is: %i" %(checkMacroDemand(thisYearsMacroDemand))
            break

        # Find out the xy-location of the max value
        #print "lu", lu, "tempMax", tempMax, "mx", mx, "luNr", luNr
        potArr = potArrs[luNr] # get potArr for this land use
        sortedArr = potArr.argsort() # sort it according to potential

        rowIndex = 0
        maxValList = []
        for column in sortedArr: # (column is an entire column (1D-array) )
            # Get the column index which has the max value, for row nr = rowIndex
            mxColIndex = column[-1]

            # get the max value, of the argsorted array, for comparison with max
            val = potArr[rowIndex, mxColIndex]

            if val == mx: # if there is more than one max-value... choose randomly
                maxValList.append((rowIndex, mxColIndex))
            rowIndex+=1

        # One (or more) locations of the max potential value found,
        # inserted into the list maxValList. In case many values - pick a random.
        random.shuffle(maxValList)
        row, col = maxValList[0]
        luRow, luCol = row+n, col+n # Add the neighborhood size to the row and col.

        #print "maxVal=", potArr[row, col]

        potArr[row, col] = -999 # make sure it's not again selected for land use change.

        # Don't allow LU change if LU has already been assigned once.
        if arrLUChange[luRow, luCol]==1:
            continue

        nrExistingLU = arrLU[luRow, luCol]
        if nrExistingLU not in luNrsStat:

            # Allow land use change
            newArrLU[luRow, luCol] = luNr
            arrLUChange[luRow, luCol] = 1 # register as "changed"

            # If replacing dynamic land use (which is not its own), increment the replaced LU demand by one.
            if nrExistingLU in luNrsDyn and nrExistingLU!=luNr:
                thisYearsMacroDemand[nrExistingLU] += 1

            # Always decrease decrement the value when satisfying LU demand.
            thisYearsMacroDemand[luNr] -= 1

            # ...and decrease loop counters value by 1.
            # If all demand satisfied for this land use (empty) - take away lu potential arr
            # This means, it won't look for LU change potential in this array anymore.
            #if thisYearsMacroDemand[luNr] <= 0:
                #print "del potArrs[%i]" % luNr
                #del potArrs[luNr]

        else:
            # Continue, without subtracting from the demand counter - since the location of
            # existing land use was not allowed to change
            continue
        #print macroDemandStatus
    # Areas not assigned any dynamic land use gets value nr 1 - i.e. same as vacant lu.
    return newArrLU

def makeMacroDemandDict(macroDemandNodes):
    """ output should look like this:
        dict = {1998 : {3 : 187, 4 : 459}, 1999 : {3 : 193, 4 : 498}}"""
    pass


if __name__=='__main__':
    pass


