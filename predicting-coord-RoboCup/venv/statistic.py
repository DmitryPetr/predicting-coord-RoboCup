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

def createDataForPlt(DF, DFAddOne, DFAddTwo, name):
    for index, row in DF.iterrows():
        maxDiff = np.sqrt((row['predictDiffX'] - row['predictDiffY']) ** 2)
        maxVariance = np.sqrt((row['predictVarianceX'] - row['predictVarianceY']) ** 2)
        DFAddOne = DFAddOne.append({
            'distName': name,
            'predictTick': row['predictTick'],
            'maxDiff': maxDiff
        }, ignore_index=True)
        DFAddTwo = DFAddTwo.append({
            'distName': name,
            'predictTick': row['predictTick'],
            'maxVariance': maxVariance
        }, ignore_index=True)
    return {'DFAddOne': DFAddOne, 'DFAddTwo': DFAddTwo}

def calcEuclidDist(coord):
    x = coord['x']
    y = coord['y']
    return np.sqrt((np.abs(x) - np.abs(y)) ** 2)

def calcSizeMid(tmpArrayMid):
    midValueSizeX = 0
    midValueSizeY = 0
    midValueSize = 0
    for elem in tmpArrayMid:
        midValueSizeX += elem['diffX']
        midValueSizeY += elem['diffY']
        midValueSize += elem['diff']
    if (len(tmpArrayMid) > 0):
        midValueSizeX = midValueSizeX / len(tmpArrayMid)
        midValueSizeY = midValueSizeY / len(tmpArrayMid)
        midValueSize = midValueSize / len(tmpArrayMid)
    return {'diffX': midValueSizeX, 'diffY': midValueSizeY, 'diff': midValueSize}

def calcMaxAndMidDistForInterval(arrayCoord, size, name):
    lenArray = len(arrayCoord)
    if lenArray <= 1:
        return None
    calcDist = np.abs(calcEuclidDist(arrayCoord[0])-calcEuclidDist(arrayCoord[1]))
    maxValue = calcDist
    maxValueSize = calcDist
    calcDistX = np.abs(np.abs(arrayCoord[0]['x']) - np.abs(arrayCoord[1]['x']))
    maxValueX = calcDistX
    maxValueSizeX = calcDistX
    calcDistY = np.abs(np.abs(arrayCoord[0]['y']) - np.abs(arrayCoord[1]['y']))
    maxValueY = calcDistY
    maxValueSizeY = calcDistY
    startValueX = arrayCoord[0]['x']
    startValueY = arrayCoord[0]['y']
    tmpArrayMidTotal = []
    tmpArrayMid = []
    indexCalc = 0
    for indexCoord in range(lenArray):
        coord = arrayCoord[indexCoord]
        tmpDistValue = np.abs(calcEuclidDist({'x': startValueX, 'y': startValueY}) - calcEuclidDist(coord))
        tmpDistValueX = np.abs(np.abs(startValueX) - np.abs(coord['x']))
        tmpDistValueY = np.abs(np.abs(startValueY) - np.abs(coord['y']))
        if (maxValueSize < tmpDistValue):
            maxValueSize = tmpDistValue
        if (maxValueSizeX < tmpDistValueX):
            maxValueSizeX = tmpDistValueX
        if (maxValueSizeY < tmpDistValueY):
            maxValueSizeY = tmpDistValueY
        tmpArrayMid.append({'diffX': tmpDistValueX, 'diffY': tmpDistValueY, 'diff': tmpDistValue})
        indexCalc += 1
        if(indexCalc >= size or (indexCoord+1) == lenArray):
            tmpArrayMidTotal.append(calcSizeMid(tmpArrayMid))
            tmpArrayMid = []
            #print('change maxValueSizeY', indexCoord, maxValueSize, maxValueSizeX, maxValueSizeY)
            if (maxValue < maxValueSize):
                #print('________ change maxValue', indexCoord)
                maxValue = maxValueSize
            if (maxValueX < maxValueSizeX):
                #print('_______ change maxValueX', indexCoord, maxValueSizeX)
                maxValueX = maxValueSizeX
            if (maxValueY < maxValueSizeY):
                maxValueY = maxValueSizeY
            indexCalc = 0
            startValueX = arrayCoord[indexCoord]['x']
            startValueY = arrayCoord[indexCoord]['y']

    midCalcVal = calcSizeMid(tmpArrayMidTotal)
    midValue = midCalcVal['diff']
    midValueX = midCalcVal['diffX']
    midValueY = midCalcVal['diffY']
    return {'maxValue': round(maxValue, 5), 'maxValueX': round(maxValueX, 5), 'maxValueY': round(maxValueY, 5),
            'midValue': round(midValue, 5), 'midValueX': round(midValueX, 5), 'midValueY': round(midValueY, 5),
            'typeCoord': name}

class paramsCreateStats:
    def __init__(self, predictObj, resultPredictMoreFiveBallDF, resultPredictFromTwoToFiveBallDF, resultPredictLessTwoBallDF,
                 resultPredictMoreFiveDF, resultPredictFromTwoToFiveDF, resultPredictLessTwoDF,
                 resultPredictStatisticLessTwoDF, resultPredictStatisticFromTwoToFiveDF, resultPredictStatisticMoreFiveDF):
        self.predictObj = predictObj
        self.resultPredictMoreFiveBallDF = resultPredictMoreFiveBallDF
        self.resultPredictFromTwoToFiveBallDF = resultPredictFromTwoToFiveBallDF
        self.resultPredictLessTwoBallDF = resultPredictLessTwoBallDF
        self.resultPredictMoreFiveDF = resultPredictMoreFiveDF

        self.resultPredictFromTwoToFiveDF = resultPredictFromTwoToFiveDF
        self.resultPredictLessTwoDF = resultPredictLessTwoDF

        self.resultPredictStatisticLessTwoDF = resultPredictStatisticLessTwoDF
        self.resultPredictStatisticFromTwoToFiveDF = resultPredictStatisticFromTwoToFiveDF
        self.resultPredictStatisticMoreFiveDF = resultPredictStatisticMoreFiveDF

def addDataForStatDist(param, withFull):
    startValuePredict = None
    #print('tuple start', param)
    #print('addDataForStatDist', param.predictObj)
    for name in param.predictObj:
        differencePredictLessTwo = []
        differencePredictFromTwoToFive = []
        differencePredictMoreFive = []
        print('predictObj[name]', len(param.predictObj[name]))
        for indexPrObj in range(len(param.predictObj[name])):
            #print('stats')
            newElems = param.predictObj[name][indexPrObj]
            if ((indexPrObj + 1 >= len(param.predictObj[name]) and newElems['predictTick'] == 1) or
                    indexPrObj + 1 < len(param.predictObj[name]) and (
                            newElems['predictTick'] == 1 and param.predictObj[name][indexPrObj + 1]['predictTick'] == 1)):
                continue
            newElems['player'] = name
            if (newElems['predictTick'] == 1):
                startValuePredict = newElems
            calcDiffWithStartX = np.abs(np.abs(startValuePredict['predictX']) - np.abs(newElems['predictX']))
            calcDiffWithStartY = np.abs(np.abs(startValuePredict['predictY']) - np.abs(newElems['predictY']))
            newElems['startPredictX'] = startValuePredict['predictX']
            newElems['startPredictY'] = startValuePredict['predictY']
            if name == 'b':
                if (calcDiffWithStartX > 5 or calcDiffWithStartY > 5):
                    param.resultPredictMoreFiveBallDF = param.resultPredictMoreFiveBallDF.append(newElems, ignore_index=True)
                elif (
                        calcDiffWithStartX > 2 and calcDiffWithStartX <= 5 or calcDiffWithStartY > 2 and calcDiffWithStartY <= 5):
                    param.resultPredictFromTwoToFiveBallDF = param.resultPredictFromTwoToFiveBallDF.append(newElems,
                                                                                               ignore_index=True)
                else:
                    param.resultPredictLessTwoBallDF = param.resultPredictLessTwoBallDF.append(newElems, ignore_index=True)
            else:
                if (calcDiffWithStartX > 5 or calcDiffWithStartY > 5):
                    param.resultPredictMoreFiveDF = param.resultPredictMoreFiveDF.append(newElems, ignore_index=True)
                    differencePredictMoreFive.append({'x': round(newElems['predictDiffX'], 4),
                                                      'y': round(newElems['predictDiffY'], 4)})
                elif (
                        calcDiffWithStartX > 2 and calcDiffWithStartX <= 5 or calcDiffWithStartY > 2 and calcDiffWithStartY <= 5):
                    param.resultPredictFromTwoToFiveDF = param.resultPredictFromTwoToFiveDF.append(newElems, ignore_index=True)
                    differencePredictFromTwoToFive.append({'x': round(newElems['predictDiffX'], 4),
                                                           'y': round(newElems['predictDiffY'], 4)})
                else:
                    param.resultPredictLessTwoDF = param.resultPredictLessTwoDF.append(newElems, ignore_index=True)
                    differencePredictLessTwo.append({'x': round(newElems['predictDiffX'], 4),
                                                     'y': round(newElems['predictDiffY'], 4)})
            differencePredictLessTwo = []
            differencePredictFromTwoToFive = []
            differencePredictMoreFive = []
        if (withFull):
          param.resultPredictStatisticLessTwoDF = calculateExpectationAndVariance(param.resultPredictStatisticLessTwoDF, differencePredictLessTwo, name)
          param.resultPredictStatisticFromTwoToFiveDF = calculateExpectationAndVariance(param.resultPredictStatisticFromTwoToFiveDF, differencePredictFromTwoToFive, name)
          param.resultPredictStatisticMoreFiveDF = calculateExpectationAndVariance(param.resultPredictStatisticMoreFiveDF, differencePredictMoreFive, name)
    return param