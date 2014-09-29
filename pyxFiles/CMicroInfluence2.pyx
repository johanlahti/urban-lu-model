import Constants
import numpy
cimport numpy

ctypedef numpy.uint8_t DTYPE_t

def getNeighbourPotential(int tLu, infl, nrsStatLU, numpy.ndarray luArr, int row, int col):
    """Calculates the CA neighbourhood potential of the input
land use type (identified by cell number). This is the "pure" CA influence.
This is later on added up with road influence, inherit suitability and zoning. """

    # tLu: the land use type (integer) for which the potential
    #       raster is calculated. One potential raster is made for each
    #       land use type.
    # centerCellVal: is the existing land use type (integer) at the center cell.
    #
    # Existing dynamic land uses cannot be replaced in this version...

    cdef DTYPE_t iLu
    #cdef DTYPE_t centerCellVal

    cdef int centerCellVal = luArr[row, col]
    if centerCellVal in nrsStatLU or centerCellVal == 0: # 0 = outside region
        return -127

    # Define C-types ----------------------
    cdef int pot = 0, inertia=0
    dists = Constants.distances.keys()
    dists.sort()
    cdef int dist
    # -------------------------------------

    # iterate through all distances
    for dist in dists:

        # Get the cells' coordinates for each distance unit
        for cellXY in Constants.distances[dist]:
            # Fetch the value of one cell from the neighbourhood
            iLu = luArr[row+cellXY[0], col+cellXY[1]]
            # Test if any influence was defined between these land uses
            # at this distance
            try:
                fromCellInfluence = infl[tLu][iLu][dist]
            except:
                # If not, continue with the next cell (next loop)
                pass
            else:
                pot += fromCellInfluence
    try:
        # infl from existing lu on candidate lu. The inertia here is usually negative.
        # => the resistance to be replaced by other land uses
        inertia = infl[tLu][centerCellVal][0]
        pot += inertia
    except: pass

    if tLu!=centerCellVal: # don't add inertia 2 times
	    try:
	    	# inertia on itself
	    	# => the resistance to be replaced by vacant land use (because another location might be better)
	    	inertia = infl[tLu][tLu][0]
	        pot += inertia
	    except: pass

    return pot

def makePotentialArrs(numpy.ndarray luArr, int rows, int cols, infl, dynKeys, nrsStatLU):
    """ Makes the potential arrays for each dynamic land use. """

    cdef int nSize = 8
    cdef numpy.ndarray nArr

    potArrs = {} # container for the potential arrays
    cdef int tLu

    # Make a potential array for each dynamic land use
    for tLu in dynKeys:
        nArr = numpy.zeros((rows, cols), dtype=numpy.integer)

        # Iterate through the land use array (at time t) and
        # do it once for each targetLU. Then add it to the collection.
        for row in range(nSize, rows-nSize):
            for col in range(nSize, cols-nSize):
                pot = getNeighbourPotential(tLu, infl, nrsStatLU, luArr, row, col)
                nArr[row, col] = pot

        # Add the potential array to the collection
        potArrs[tLu] = nArr
    return potArrs