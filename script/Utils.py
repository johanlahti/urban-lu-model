# -*- coding: cp1252 -*-
from osgeo import gdal
import numpy
from glob import glob
from PIL import Image

def makeArray(imagePath):
    """ Returns an array from the input image path."""
    array = None
    imageExists = (imagePath and len(imagePath)>0 and len(glob(imagePath))>0)
    if (imageExists):
        try:
            image = gdal.Open(imagePath)
            array = image.ReadAsArray()
        except:
            print "Could not open/convert src land use image"
        else:
            print "File: %s successfully read and converted to array." % (imagePath)
    else:
        print "LandUse.makeArray says that the imagePath: %s is not correct" % (imagePath)

    DTYPE = numpy.uint8
    array.dtype = DTYPE
    return array

def makeArrays(imagePaths):
    arrs = []
    for path in imagePaths:
        array = makeArray(path)
        if (array!=None):
            arrs.append(array)
    return arrs


def countNumberInArr(listNrs, arr):
    # This is a way of counting the number of occurrences in the array
    flatArr = arr.flatten()
    flatArr.sort()
    amount = 0
    for nr in listNrs:
        amount += (flatArr.searchsorted(nr, side='right') - flatArr.searchsorted(nr, side='left'))
    return amount

def countLandUseInArr(arr, filter=[]):
    """ Returns a dict with nr of cells keyed by luNr. A filter
    is an optional array of integers. Only these integers will be calculated.
    E.g. output: {0: 2691, 1: 3423, 2: 107, 3: 1177, 4: 826, 5: 412, 6: 1020, 7: 2764} """
    # Find out the unique numbers in the array
    if not filter:
        luTypes = numpy.unique(arr).tolist() # Get the land use types. E.g. 1,2,3.
    else:
        luTypes = filter

    dictLuNrs = {}
    for i in luTypes:
        # This is a way of counting the number of occurrences in the array
        amount = countNumberInArr([i], arr)
        dictLuNrs[i] = amount
    return dictLuNrs

def makeLinearFunc(xList, startXY, endXY, middleXY=None):
    """
    xList [nr, nr] The x-values which should get a y-value
    startXY [nr, nr] The starting X and Y of the linear function.
    endXY [nr, nr] The ending X and Y.
    middleXY [nr, nr] {Optional} One node in between start and end node.
    """

    """ Make one or two linear functions from given coordinates
    and return the values (as a dict) for the x-values found in
    the xList. """

    x1, y1 = startXY
    try: x2, y2 = middleXY
    except: pass
    x3, y3 = endXY

    # Always sort list first.
    xList.sort()
    # Don't extrapolate values - only calculate intermediate values!
    xList = xList[xList.index(x1):xList.index(x3)+1]

    # The dict holding the final X- and Y-values.
    xyDict = {}

    # Iterate through all distances and stop when distUnit==middleX
    # and/or when distUnit/100==endX.
    for x in xList:
        # Define the straight line
        # Based on: f(x) = y1 + [(y2 - y1) / (x2 - x1)]·(x - x1)
        # And then assign the value to the xyList

        # If no middle was defined, give values based on two equations.
        if middleXY != None:
            if x<=x2:
                val = y1 + ( float((y2 - y1))/(x2 - x1) ) * (x - x1)
            else:
                val = y2 + ( float((y3 - y2))/(x3 - x2) ) * (x - x2)

        # Else, give all values based on one equation.
        else:
            val = y1 + ( float((y3 - y1)) / (x3 - x1) ) * (x - x1)

        xyDict[x] = round(val, 2) # The y-value is rounded to 2 decimals
        if x >= x3: # don't define influence beyond end point.
            break

    # Return a dict with y-values keyed by x-values.
    return xyDict

def findAndReplace(luArr, find=[], replaceWith=1, within=[(8,8),(-8,-8)]):
    rows = luArr.shape[0]
    cols = luArr.shape[1]
    for row in range(within[0][0], within[1][0]):
        for col in range(within[0][1], within[1][1]):
            val = luArr[row, col]
            if val in find:
                luArr[row, col] = replaceWith
    return luArr

def compareArrs(arrPredict, arrReal):
    errors = 0
    for row in range(8, arrPredict.shape[0] - 8):
        for col in range(8, arrPredict.shape[1] - 8):
            if arrPredict[row, col]!=arrReal[row, col]:
                errors+=1
    #percentCorrect = (arrPredict.size - errors) / float(arrPredict.size) * 100.0
    #arrDiff = arrReal - arrPredict
    #zeros = countNumberInArr([0, 255], arrDiff)
    #percentCorrect = float(zeros) / float(arrDiff.size) * 100
    #print "percentCorrect is %f" % (percentCorrect)
    return errors


def getFuzzyValue(arrPredict, arrReal, frameSize=(0,0), nSize=1, banList=[0]):
    """ Return a fuzzy value. Compares each cell of the two arrs.
    It finds the shortest distance within the nSize neighborhood
    where the value in the arrReal is present in arrPredict (if present).
    The longer the distance, the lower score for this cell. Maximum
    is 1 and if not present its 0. The used weight function is linear
    and the neighborhood is square.

    @param arrPredict {numpy array}: Calculated data
    @param arrReal {numpy array}: Real data
    @param frameSize (rows, cols): A frame of values which are not compared. fuzzyArr value will be -1 here.
    @param nSize {Integer}: The size of the neighbourhood which we compare within.
    @param banList {List}: Values in the arrs which will not be evaluated. fuzzyArr value will be -1 here. """


    # Store the result both as a number and as an image
    fuzzyArr = numpy.zeros( (arrPredict.shape[0]-frameSize[0], arrPredict.shape[1]-frameSize[1]), dtype='float')
    fuzzyScore = 0.0

    for row in range(frameSize[0], arrPredict.shape[0]-frameSize[0]):
        for col in range(frameSize[1], arrPredict.shape[1]-frameSize[1]):
            actVal = arrReal[row, col] # We are looking for this value in the neighborhood

            # Don't compare values which should not be compared
            if actVal in banList:
                fuzzyArr[row, col] = 2
                continue

            fuzzyVal = 0.0
            distWeight = 0.0
            shortestDist = 999

            # Search the neighborhood
            for r in range(-nSize, nSize+1):
                for c in range(-nSize, nSize+1):
                    dist = (r**2 + c**2)**(1/2.0)
                    try:
                        foundVal = arrPredict[row+r, col+c]
                    except:
                        continue
                    if foundVal in banList:
                        continue

                    if foundVal==actVal and dist < shortestDist:
                        # Store the shortest distance at which we found the value
                        distWeight = 1 - ( float(dist)/(nSize+1) )
                        shortestDist = dist

            fuzzyVal = distWeight

            fuzzyArr[row, col] = fuzzyVal
            fuzzyScore += fuzzyVal
    return fuzzyArr, fuzzyScore


"""
@param landUses {dict}
    The land uses property in the configuration file.
@return {list}
    A palette which fits with the PIL Image palette.
"""
def makeLandUsePalette(landUses):
    palette = []
    for luNr in landUses.keys():
        color = landUses[luNr]["color"]
        for i in color:
            palette.append(int(i*255))
    return palette


"""
 Function requires Image library (PIL)

 @param arr {numpy Array}
 @param savePath {String}
     Must have an allowed extension (e.g. .png, .jpg)
     since format is derived from this. Format could also be
     given as a second parameter in img.save .
 @param palette {List}
     The index gives color to the same array value. """
def saveArrAsImage(arr, savePath, palette=[]):
    img = Image.fromarray(arr)
    img.putpalette(palette)
    #size = img.size
    #img.resize(size, Image.NEAREST)
    img.save(savePath)


if __name__=='__main__':
    arr1 = makeArray("../data/LU_150m/lu98_2_150mr.img")
    arr2 = makeArray("../data/LU_150m/lu99_2_150mr")
    fArr, fScore = getFuzzyValue(arr2, arr1, nSize=1)



    #cMap = ListedColormap(colorTable, name="myCMap", N=None)
    import matplotlib
    import matplotlib.pyplot as plt


    im = plt.imshow(fArr, aspect="equal", interpolation="nearest")
    plt.colorbar()

    #self.im.set_cmap('hot')

    im.figure.show()

    plt.show()
    print fArr.max()

    print "fScore", fScore





