import Constants
import numpy
import random
cimport numpy

ctypedef numpy.uint8_t U_DTYPE8_t
ctypedef numpy.float64_t U_DTYPE64_t


def getNeighbourPotential(int tLu, dict infl, dists, nrsStatLU, numpy.ndarray[U_DTYPE8_t, ndim=2] luArr not None, int row, int col):
    """Calculates the CA neighbourhood potential of the input
land use type (identified by cell number). This is the "pure" CA influence.
This is later on added up with road influence, inherit suitability and zoning. """

    # tLu: the land use type (integer) for which the potential
    #       raster is calculated. One potential raster is made for each
    #       land use type.
    # centerCellVal: is the existing land use type (integer) at the center cell.
    #
    # Existing dynamic land uses cannot be replaced in this version...

    # Define C-types ----------------------
    cdef U_DTYPE8_t iLu, centerCellVal # must receive value from luArr
    cdef float pot=0.0, inertia=0.0
    #cdef int pot=0, inertia=0 # must assign a value to potArr (nArr)
    cdef int dist # NOT fetching value from array
    # -------------------------------------

    centerCellVal = luArr[row, col]
    if centerCellVal in nrsStatLU or centerCellVal == 0.0: # 0.0 = outside region
        return -999.0


    # iterate through all distances
    for dist in dists:
        # Get the cells' coordinates for each distance unit
        for xy in Constants.distances[dist]:
            # Fetch the value of one cell from the neighbourhood
            iLu = luArr[row+xy[0], col+xy[1]]
            # Test if any influence was defined between these land uses
            # at this distance
            try:
                fromCellInfluence = infl[iLu][dist]
            except:
                pass
            else:
                pot = pot + fromCellInfluence

    # Try to see if any inertia was defined which will strengthen existing LU.
    try:
        inertia = infl[centerCellVal]["inertia"]
        pot = pot + inertia
    except KeyError:
        pass


    return pot

def makePotentialArrs(numpy.ndarray[U_DTYPE8_t, ndim=2] luArr not None, int rows, int cols, dict infl, dynKeys, nrsStatLU, float maxRand):
    """ Makes the potential arrays for each dynamic land use. """

    cdef numpy.ndarray nArr
    cdef int tLu, row, col, nSize=8
    cdef float pot, inertia

    cdef dict potArrs={}

    dists = Constants.distances.keys()
    dists.sort()

    # Make a potential array for each dynamic land use
    for tLu in dynKeys:
        nArr = numpy.zeros((rows, cols), dtype=numpy.float64)
        # Iterate through the land use array (at time t) and
        # do it once for each targetLU. Then add it to the collection.
        for row in range(nSize, rows-nSize):
            for col in range(nSize, cols-nSize):
                pot = getNeighbourPotential(tLu, infl[tLu], dists, nrsStatLU, luArr, row, col)
                nArr[row, col] = pot
                #print nArr[row, col] == pot

        #if (maxRand!=None):
        #    nArr = addRand(rows, cols, nSize, nArr, maxRand)

        # Add the potential array to the collection
        potArrs[tLu] = nArr


        #print "Average", numpy.average(arrTest), "Max:", max(arrTest), "Min:", min(arrTest)

    # Add a random effect
    if (maxRand!=None):
        potArrKeys = potArrs.keys()
        randArrs = makeRandomArrs(rows, cols, potArrKeys, maxRand)
        potArrs = addRandom(potArrs, randArrs)
        print "random added", maxRand
    return potArrs

"""def addRand(int rows, int cols, int nSize, numpy.ndarray[U_DTYPE64_t, ndim=2] potArr not None, float maxRand):

    cdef float randNr=0.0, mn, mx, newPot
    cdef U_DTYPE64_t pot

    mx = 1 + maxRand/2.0
    mn = 1 - maxRand/2.0

    for row in range(nSize, rows-nSize):
        for col in range(nSize, cols-nSize):
            randNr = random.uniform(mn, mx)
            pot = potArr[row, col]
            newPot = pot * randNr
            potArr[row, col] = newPot
    return potArr"""


def makeRandomArrs(int rows, int cols, potArrKeys, float maxRand):
    """ Make random arrays with an amount specified by input parameter maxRand (float in range 0-1) """

    cdef numpy.ndarray randArr
    cdef int i

    maxRand = maxRand/2.0
    # Make a random array for each dynamic land use and store it in dict randArrs
    # Add random (stochastic) effect to each potential array.
    cdef dict randArrs = {}
    #cdef numpy.ndarray randArr, potArr
    for i in potArrKeys:
        randArr = numpy.random.uniform(1-maxRand, 1+maxRand, (rows, cols) )
        randArrs[i] = randArr # Store it for later use
    return randArrs

def addRandom(dict potArrs, dict randArrs):
    """ Add the random effect given by randArrs to the potArrs. """

    cdef int i

    #cdef numpy.ndarray newPotArr

    #cdef dict potArrsRand = {} # The new potArrs container, replacing potArrs
    for i in potArrs.keys():
        potArrs[i] = potArrs[i] * randArrs[i] # Add random effect to potArrs. The 8-cells frame of values 0 will remain 0.
    return potArrs




