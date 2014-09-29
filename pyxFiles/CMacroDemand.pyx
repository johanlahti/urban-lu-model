from osgeo import gdal
import numpy
cimport numpy
import random
import copy

ctypedef numpy.uint8_t U_DTYPE8_t

def findAndReplace(numpy.ndarray[U_DTYPE8_t, ndim=2] arrLU not None, int rows, int cols, int nSize, find=[], int replaceWith=1):
    cdef int row, col
    cdef float val

    for row in range(nSize, rows-nSize):
        for col in range(nSize, cols-nSize):
            val = arrLU[row][col]
            if val in find:
                arrLU[row][col] = replaceWith
    return arrLU

def checkMacroDemand(thisYearsMacroDemand):
    tot = 0
    for luNr in thisYearsMacroDemand.keys():
        tot += thisYearsMacroDemand[luNr]
    return tot

def applyMacroDemand(dict macroDemand, int year, luNrsDyn, luNrsStat, dict potArrs, numpy.ndarray[U_DTYPE8_t, ndim=2] arrLU not None, int rows, int cols):
    """ Make the new land use map by changing the required cells for current time step,
    for the dynamic land uses. """

    cdef int n = 8 # neighborhood size
    cdef int nr, luNr, tLu, rowIndex, mxColIndex, row, col, luRow, luCol
    
    cdef float tempMax, mx, val
    
    cdef U_DTYPE8_t nrExistingLU
    cdef dict potArrsNoFrame = {} # create a new local dict with potArrs where the frame of 8 pixels is taken away

    cdef dict thisYearsMacroDemand = macroDemand[year]
    #lastYearsMacroDemand = macroDemand[year-1]

    # Make a new arr for the new land use array, where all dynamic LU are replaced by number 1.
    cdef numpy.ndarray newArrLU = findAndReplace(arrLU.copy(), rows, cols, n, find=luNrsDyn, replaceWith=1)
    #newArrLU.dtype = U_DTYPE8_t
    cdef numpy.ndarray potArr, sortedArr

    # Cut away the surrounding "frame" of neighborhood cells which are not supposed to be calculated.
    for nr in potArrs.keys():
        potArrsNoFrame[nr] = copy.deepcopy(potArrs[nr][n:-n, n:-n]) # Make a deep copy to avoid changes in the original potArrs
    # This raster keeps track of which land use has been changed already so that it wont change again.
    arrLUChange = numpy.zeros((rows, cols), dtype=numpy.integer) # I would like int0/unit0 here instead

    # Iterate
    while checkMacroDemand(thisYearsMacroDemand)>0:
        mx = 0.0 # float Note! Maybe this should be initialized as None?
        luNr = -9999 # int
        tempMax = -999999.0 # float
        # Get max value of all potential arrays and find out which array (LuNr) holds it
        for tLu in potArrsNoFrame.keys():
            # If the land use demand is satisfied for one land use,
            # then don't try to find the potential for this LU. When
            # all LU are satisfied, the loop with stop automatically (see while-statement)
            if thisYearsMacroDemand[tLu]<=0:
                continue
            tempMax = potArrsNoFrame[tLu].max() # Max for this LU - but maybe not compared with other LU:s

            # Add a stochastic effect. Don't allow LU change if random number not within range.
            if tempMax > mx:
                mx = tempMax # save current max val
                luNr = tLu # save lu (which has the highest potential)
        if luNr == -9999:
            #print "Continuing when macroDemandStatus is: %i" %(checkMacroDemand(thisYearsMacroDemand))
            continue

        # ---- Find out the xy-location of the max value -------------------------------------

        potArr = potArrsNoFrame[luNr] # get potArr for this land use
        sortedArr = potArr.argsort() # sort it according to potential

        rowIndex = 0
        maxValList = []
        for column in sortedArr: # (column is an entire column (1D-array) )
            # Get the column index which has the max value, for row nr = rowIndex
            mxColIndex = column[-1]

            # get the max value, of the argsorted array, for comparison with max
            val = potArr[rowIndex, mxColIndex] # location with max value found!

            if val == mx: # if there is more than one max-value... choose randomly
                maxValList.append((rowIndex, mxColIndex))
            rowIndex+=1

        # In case many values - pick a random.
        for i in range(len(maxValList)):
            random.shuffle(maxValList)
            row, col = maxValList[0]
            luRow, luCol = row+n, col+n # Add the neighborhood size to the row and col.
            potArr[row, col] = -999999.0 # make sure the potential is not again selected for land use change.

            # Don't allow LU change if LU has already been assigned once.
            if arrLUChange[luRow, luCol]==1:
                continue

            nrExistingLU = arrLU[luRow, luCol] # Get the existing land use which will now be replaced (if not static)
            if nrExistingLU not in luNrsStat:

                # If replacing dynamic land use (which is not its own), increment the replaced LU demand by one.
                if nrExistingLU in luNrsDyn and nrExistingLU!=luNr:
                    thisYearsMacroDemand[nrExistingLU] += 1


                # Always decrease decrement the value when satisfying LU demand.
                thisYearsMacroDemand[luNr] -= 1

                # Allow land use change
                newArrLU[luRow, luCol] = luNr
                arrLUChange[luRow, luCol] = 1 # register as "changed"
            else:
                # Continue, without subtracting from the demand counter - since the existing land use was of type "static".
                continue
    # Note! Areas not assigned any dynamic land use gets value nr 1 - i.e. same as vacant lu.
    return newArrLU

def makeMacroDemandDict(macroDemandNodes):
    """ output should look like this:
        dict = {1998 : {3 : 187, 4 : 459}, 1999 : {3 : 193, 4 : 498}}"""
    pass


if __name__=='__main__':
    pass


