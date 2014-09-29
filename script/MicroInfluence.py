import numpy
import Constants

def getNeighbourPotential(tLu, infl, statLU, luArr, row, col):
    """Calculates the CA neighbourhood potential of the input
land use type (identified by cell number). This is the "pure" CA influence.
This is later on added up with road influence, inherit suitability and zoning. """
    # tLu: the land use type (integer) for which the potential
    #       raster is calculated. One potential raster is made for each
    #       land use type.
    # centerCellVal: is the existing land use type (integer) at the center cell.
    #

    centerCellVal = luArr[row][col]
    if centerCellVal in statLU or \
        centerCellVal == 0: # 0 = outside region
        return -99999

    pot = 0
    dists = Constants.distances.keys()
    dists.sort()

    # iterate through all distances
    for dist in dists:

        # Get the cells' coordinates for each distance unit
        for cellXY in Constants.distances[dist]:
            # Fetch the value of one cell from the neighbourhood
            iLu = luArr[row+cellXY[0]][col+cellXY[1]]
            # Test if any influence was defined between these land uses
            # at this distance
            try:
                fromCellInfluence = infl[tLu][iLu][dist]
            except:
                # If not, continue with the next cell (next loop)
                pass
            else:
                pot += fromCellInfluence

    #if centerCellVal == tLu: # add inertia value if land use exists already
        #pot += infl[tLu][-1]
    try:
        # Inertia is a negative value. Gives (negative) infl from existing lu on candidate lu.
        inertia = infl[tLu][centerCellVal][0]
        pot += inertia
    except: pass

    return pot

def makePotentialArrs(luArr, rows, cols, infl, dynKeys, statLU):
    """ Makes the potential arrays for each dynamic land use. """

    nSize = 8
    potArrs = {} # container for the potential arrays

    # Make a potential array for each dynamic land use
    for tLu in dynKeys:
        nArr = numpy.zeros((rows, cols), dtype=numpy.integer)

        # Iterate through the land use array (at time t) and
        # do it once for each targetLU. Then add it to the collection.
        for row in range(nSize, rows-nSize):
            for col in range(nSize, cols-nSize):
                pot = getNeighbourPotential(tLu, infl, statLU, luArr, row, col)

                # Assign neighbourhood potential to the cell
                # if it's not unreplaceable...
                # if pot != -9999:
                nArr[row][col] = pot

        #kRoads = 0.80
        #kN = 0.20
        potArr = nArr

        # Add the potential array to the collection
        potArrs[tLu] = potArr
    return potArrs