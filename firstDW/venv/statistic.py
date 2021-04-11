from collections import deque
import numpy as np

def calculateExpectationAndVariance(DF, difference, playerName):
    expectation = [None, None]
    sumDiffX = [0, 0]
    sumDiffY = [0, 0]
    if (len(difference) > 0):
        for diff in difference:
            sumDiffX[0] += diff['x']
            sumDiffX[1] += 1
            sumDiffY[0] += diff['y']
            sumDiffY[1] += 1
        if (sumDiffX[1] != 0):
            expectation[0] = sumDiffX[0] / sumDiffX[1]
        if (sumDiffY[1] != 0):
            expectation[1] = sumDiffY[0] / sumDiffY[1]

        varianceRes = [None, None]
        distanceMax = [difference[0]['x'], difference[0]['y']]
        distanceMix = [difference[0]['x'], difference[0]['y']]
        for indexD in range(1, len(difference)):
            elDist = [difference[indexD]['x'], difference[indexD]['y']]
            if (distanceMax[0] < elDist[0]):
                distanceMax[0] = elDist[0]
            if (distanceMix[0] > elDist[0]):
                distanceMix[0] = elDist[0]
            if (distanceMax[1] < elDist[1]):
                distanceMax[1] = elDist[1]
            if (distanceMix[1] > elDist[1]):
                distanceMix[1] = elDist[1]
        if (sumDiffX[1] != 0):
            varianceRes[0] = np.sqrt(((distanceMax[0] - distanceMix[0]) ** 2) / sumDiffX[1])
        if (sumDiffY[1] != 0):
            varianceRes[1] = np.sqrt(((distanceMax[1] - distanceMix[1]) ** 2) / sumDiffY[1])
        new_row = {'player': playerName, 'expectationX': round(expectation[0], 4),
                   'expectationY': round(expectation[1], 4),
                   'varianceX': round(varianceRes[0], 4), 'varianceY': round(varianceRes[1], 4)}
        DF = DF.append(new_row, ignore_index=True)
    return DF
