import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from config import Flags, resultColumn, resultStatisticColumn, \
    resultPredictColumn, teams, pathDefault, prefixFiles, numberTeamGoalie, movementsTenTick, numPeople
from getCoords import *
from saveModule import infoForTick, storeAgent, posPlayer, otherPlayer
from random import randint
from statistic import calculateExpectationAndVariance, calcMaxAndMidDistForInterval, createDataForPlt, addDataForStatDist, paramsCreateStats
from processInputData import readFile, createMapViewFlag, createMapViewMove, \
    calcInfoForTick, paramsForCalcPosition, createDataTickWithPredictVal, paramsForDataTickWithPredictVal

resFlagsTeam = {}
resMovTeam = {}
resProcessTeam = {}
resMovePTeam = {}
resMoveBTeam = {}
predictObj = {}
playerList = {}
entropyName = randint(1000, 100000)

resultDataForPrint = pd.DataFrame(columns=['distName', 'predictTick', 'maxDiff'])
resultDataForPrintVariance = pd.DataFrame(columns=['distName', 'predictTick', 'maxVariance'])

resultDataForPrintBall = pd.DataFrame(columns=['distName', 'predictTick', 'maxDiff'])
resultDataForPrintVarianceBall = pd.DataFrame(columns=['distName', 'predictTick', 'maxVariance'])


resultDF = pd.DataFrame(columns=resultColumn)
resultStatisticDF = pd.DataFrame(columns=resultStatisticColumn)
# resultPredictDF = pd.DataFrame(columns=resultPredictColumn)
# resultPredictStatisticDF = pd.DataFrame(columns=resultStatisticColumn)
resultPredictStatisticLessTwoDF = pd.DataFrame(columns=resultStatisticColumn)
resultPredictStatisticFromTwoToFiveDF = pd.DataFrame(columns=resultStatisticColumn)
resultPredictStatisticMoreFiveDF = pd.DataFrame(columns=resultStatisticColumn)
resultPredictLessTwoDF = pd.DataFrame(columns=resultPredictColumn)
resultPredictFromTwoToFiveDF = pd.DataFrame(columns=resultPredictColumn)
resultPredictMoreFiveDF = pd.DataFrame(columns=resultPredictColumn)

resultPredictLessTwoBallDF = pd.DataFrame(columns=resultPredictColumn)
resultPredictFromTwoToFiveBallDF = pd.DataFrame(columns=resultPredictColumn)
resultPredictMoreFiveBallDF = pd.DataFrame(columns=resultPredictColumn)

# задаётся по какому игроку нужно получить результат
needTeam = teams[0]
needPlayer = 1
# TODO - доделать пресказание для мяча!

averageCoordArrayGlobal = []
absoluteCoordArrayGlobal = []
averageCoordArrayGlobalGoalie = []
absoluteCoordArrayGlobalGoalie = []

readData = readFile(resFlagsTeam, resMovTeam)
resFlagsTeam = readData['resFlags']
resMovTeam = readData['resMov']

resProcessTeam = createMapViewFlag(resProcessTeam, resFlagsTeam)

dataViewMap = createMapViewMove(resMovePTeam, resMoveBTeam, resMovTeam)
resMovePTeam = dataViewMap['resMoveP']
resMoveBTeam = dataViewMap['resMoveB']

for item in teams:
    print('team - ', item)
    playerList[item] = {}
    for ind in range(numPeople):
        print('player', ind)
        playerList[item][(ind+1)] = storeAgent()
        varianceArray = []storeAgent
        absoluteCoordArray = []
        playerName = None
        difference = []
        angleOrientation = None
        angleFlag = None
        radian = None
        speedX = None
        speedY = None
        valueLackFlag = 0
        for elems in resProcessTeam[item][(ind+1)]:
            #print('elems', elems)
            print('time - ', elems['time'])

            if (elems['time'] > 200):
                break

            nowPlObj = playerList[item][(ind + 1)]
            # timeRow = absolute_Coordinate[absolute_Coordinate['# time'] == elems['time']]
            absoluteCoord = getAbsolutedCoordinate(item, (ind+1), elems['time'], angleOrientation, False)
            if (absoluteCoord == None):
                continue

            angleOrientation = absoluteCoord.angleFlag
            angleFlag = absoluteCoord.angleOrientation
            nowPlayer = absoluteCoord.nowPlayer
            playerName = absoluteCoord.nowPlayer
            absoluteX = absoluteCoord.absoluteX
            absoluteY = absoluteCoord.absoluteY

            absoluteCoordArray.append({'x': absoluteX, 'y': absoluteY})
            paramsTick = paramsForCalcPosition(elems, nowPlObj, angleOrientation,
                                               valueLackFlag, varianceArray, angleFlag, absoluteX, absoluteY)
            ansInfoForTick = calcInfoForTick(paramsTick, resMovePTeam, item, ind, absoluteCoordArray)
            if (ansInfoForTick == None):
                continue
            angleOrientation = ansInfoForTick.angleOrientation
            valueLackFlag = ansInfoForTick.valueLackFlag
            averageX = ansInfoForTick.averageX
            averageY = ansInfoForTick.averageY
            varianceArray = ansInfoForTick.varianceArray
            arrPlayer = ansInfoForTick.arrPlayer
            radian = ansInfoForTick.radian
            speedX = ansInfoForTick.speedX
            speedY = ansInfoForTick.speedY

            newObj = infoForTick(averageX, averageY, absoluteX, absoluteY, radian, speedX, speedY, arrPlayer)
            playerList[item][(ind+1)].addNewTickInfo(newObj)
            if (item == teams[0] and (ind+1) == numberTeamGoalie[0]) or \
                    (item == teams[1] and (ind+1) == numberTeamGoalie[1]):
                averageCoordArrayGlobalGoalie.append({'x': averageX, 'y': averageY})
                absoluteCoordArrayGlobalGoalie.append({'x': absoluteX, 'y': absoluteY})
            else:
                averageCoordArrayGlobal.append({'x': averageX, 'y': averageY})
                absoluteCoordArrayGlobal.append({'x': absoluteX, 'y': absoluteY})
            removeList = playerList[item][(ind + 1)].removeList()
            listPredict = playerList[item][(ind + 1)].predictForDisappearedPlayer(removeList)
            playerList[item][(ind + 1)].savePredictCoords(listPredict)
            for nn in playerList[item][(ind + 1)].removePlayer:
                removePlayer = playerList[item][(ind + 1)].removePlayer[nn]

            valueTickWithPredictVal = paramsForDataTickWithPredictVal(listPredict, elems, predictObj, angleOrientation)
            predictObj = createDataTickWithPredictVal(valueTickWithPredictVal, nowPlayer)

            differenceX = np.abs(np.abs(averageX) - np.abs(absoluteX))
            differenceY = np.abs(np.abs(averageY) - np.abs(absoluteY))
            difference.append({'x': differenceX, 'y': differenceY})

            new_row = {'time': elems['time'], 'player': nowPlayer, 'calc x': round(averageX, 4),
                       'calc y': round(averageY, 4), 'absolute x': absoluteX, 'absolute y': absoluteY,
                       'differenceX': round(differenceX, 4), 'differenceY': round(differenceY, 4)}
            resultDF = resultDF.append(new_row, ignore_index=True)
        # Statistic
        valueCreateStats = paramsCreateStats(predictObj, resultPredictMoreFiveBallDF, resultPredictFromTwoToFiveBallDF, resultPredictLessTwoBallDF,
                 resultPredictMoreFiveDF, resultPredictFromTwoToFiveDF, resultPredictLessTwoDF,
                 resultPredictStatisticLessTwoDF, resultPredictStatisticFromTwoToFiveDF, resultPredictStatisticMoreFiveDF)
        dataForStatDist = addDataForStatDist(valueCreateStats, False)

        resultPredictMoreFiveBallDF = dataForStatDist.resultPredictMoreFiveBallDF
        resultPredictFromTwoToFiveBallDF = dataForStatDist.resultPredictFromTwoToFiveBallDF
        resultPredictLessTwoBallDF = dataForStatDist.resultPredictLessTwoBallDF
        resultPredictMoreFiveDF = dataForStatDist.resultPredictMoreFiveDF
        resultPredictFromTwoToFiveDF = dataForStatDist.resultPredictFromTwoToFiveDF
        resultPredictLessTwoDF = dataForStatDist.resultPredictLessTwoDF

        #resultStatisticDF = calculateExpectationAndVariance(resultStatisticDF, difference, playerName)

# resultDF.to_csv(str(entropyName) + 'resultCalc.csv')
# resultStatisticDF.to_csv(str(entropyName) + 'resultStatistic.csv')

# resultDF.to_csv(needTeam + '_' + str(needPlayer) + '_resultCalc.csv')
# resultStatisticDF.to_csv(needTeam + '_' + str(needPlayer) + '_resultStatistic.csv')

#resultPredictDF.to_csv(str(entropyName) + 'resultPredict.csv')
#resultPredictStatisticDF.to_csv(str(entropyName) + 'resultPredictStatistic.csv')

# resultPredictLessTwoDF.to_csv(str(entropyName) + 'resultPredictLessTwo.csv')
# resultPredictFromTwoToFiveDF.to_csv(str(entropyName) + 'resultPredictFromTwoToFive.csv')
# resultPredictMoreFiveDF.to_csv(str(entropyName) + 'resultPredictMoreFive.csv')
#
# resultPredictStatisticLessTwoDF.to_csv(str(entropyName) + 'resultPredictStatisticLessTwo.csv')
# resultPredictStatisticFromTwoToFiveDF.to_csv(str(entropyName) + 'resultPredictStatisticFromTwoToFive.csv')
# resultPredictStatisticMoreFiveDF.to_csv(str(entropyName) + 'resultPredictStatisticMoreFive.csv')

# resultPredictLessTwoDF.to_csv(needTeam + '_' + str(needPlayer) + 'resultPredictLessTwo.csv')
# resultPredictFromTwoToFiveDF.to_csv(needTeam + '_' + str(needPlayer) + 'resultPredictFromTwoToFive.csv')
# resultPredictMoreFiveDF.to_csv(needTeam + '_' + str(needPlayer) + 'resultPredictMoreFive.csv')

# resultPredictLessTwoBallDF.to_csv(needTeam + '_' + str(needPlayer) + 'resultPredictLessTwoBallDF.csv')
# resultPredictFromTwoToFiveBallDF.to_csv(needTeam + '_' + str(needPlayer) + 'resultPredictFromTwoToFiveBallDF.csv')
# resultPredictMoreFiveBallDF.to_csv(needTeam + '_' + str(needPlayer) + 'resultPredictMoreFiveBallDF.csv')

# resultPredictStatisticLessTwoDF.to_csv(needTeam + '_' + str(needPlayer) + 'resultPredictStatisticLessTwo.csv')
# resultPredictStatisticFromTwoToFiveDF.to_csv(needTeam + '_' + str(needPlayer) + 'resultPredictStatisticFromTwoToFive.csv')
# resultPredictStatisticMoreFiveDF.to_csv(needTeam + '_' + str(needPlayer) + 'resultPredictStatisticMoreFive.csv')
#print(len(resultPredictLessTwoDF.index), len(resultPredictFromTwoToFiveDF.index), len(resultPredictMoreFiveDF.index))

printDataAns = createDataForPlt(resultPredictLessTwoDF, resultDataForPrint, resultDataForPrintVariance, 'PredictLessTwo')
resultDataForPrint = printDataAns['DFAddOne']
resultDataForPrintVariance = printDataAns['DFAddTwo']

printDataAns = createDataForPlt(resultPredictFromTwoToFiveDF, resultDataForPrint, resultDataForPrintVariance, 'FromTwoToFive')
resultDataForPrint = printDataAns['DFAddOne']
resultDataForPrintVariance = printDataAns['DFAddTwo']

printDataAns = createDataForPlt(resultPredictMoreFiveDF, resultDataForPrint, resultDataForPrintVariance, 'MoreFive')
resultDataForPrint = printDataAns['DFAddOne']
resultDataForPrintVariance = printDataAns['DFAddTwo']

# Ball
printDataAns = createDataForPlt(resultPredictLessTwoBallDF, resultDataForPrintBall, resultDataForPrintVarianceBall, 'PredictLessTwo')
resultDataForPrintBall = printDataAns['DFAddOne']
resultDataForPrintVarianceBall = printDataAns['DFAddTwo']

printDataAns = createDataForPlt(resultPredictFromTwoToFiveBallDF, resultDataForPrintBall, resultDataForPrintVarianceBall, 'FromTwoToFive')
resultDataForPrintBall = printDataAns['DFAddOne']
resultDataForPrintVarianceBall = printDataAns['DFAddTwo']

printDataAns = createDataForPlt(resultPredictMoreFiveBallDF, resultDataForPrintBall, resultDataForPrintVarianceBall, 'MoreFive')
resultDataForPrintBall = printDataAns['DFAddOne']
resultDataForPrintVarianceBall = printDataAns['DFAddTwo']

order = resultDataForPrint['predictTick']
dfWide = resultDataForPrint.pivot_table(index='predictTick', columns='distName', values='maxDiff')
dfWide = dfWide.reindex(order, axis=0)

order = resultDataForPrintVariance['predictTick']
dfWideVariance = resultDataForPrintVariance.pivot_table(index='predictTick', columns='distName', values='maxVariance')
dfWideVariance = dfWideVariance.reindex(order, axis=0)

order = resultDataForPrintBall['predictTick']
dfWideBall = resultDataForPrintBall.pivot_table(index='predictTick', columns='distName', values='maxDiff')
dfWideBall = dfWideBall.reindex(order, axis=0)

order = resultDataForPrintVarianceBall['predictTick']
dfWideVarianceBall = resultDataForPrintVarianceBall.pivot_table(index='predictTick', columns='distName', values='maxVariance')
dfWideVarianceBall = dfWideVarianceBall.reindex(order, axis=0)

# print('dfWide')
# print(dfWide)
#
# print('dfWideVariance')
# print(dfWideVariance)


print('dfWide draw')
sns.lineplot(data=dfWide)
plt.show()

print('dfWideVariance draw')
sns.lineplot(data=dfWideVariance)
plt.show()

# print('dfWideBall')
# print(dfWideBall)
#
# print('dfWideVarianceBall')
# print(dfWideVarianceBall)


print('dfWide draw Ball')
sns.lineplot(data=dfWideBall)
plt.show()

print('dfWideVariance draw Ball')
sns.lineplot(data=dfWideVarianceBall)
plt.show()

# movementsTenTickDF = pd.DataFrame(columns=movementsTenTick)
#
# needTickSize = 10
# movementsTenTickDF = movementsTenTickDF.append(calcMaxAndMidDistForInterval(averageCoordArrayGlobal, needTickSize, 'averageCoordArrayGlobal'), ignore_index=True)
# movementsTenTickDF = movementsTenTickDF.append(calcMaxAndMidDistForInterval(absoluteCoordArrayGlobal, needTickSize, 'absoluteCoordArrayGlobal'), ignore_index=True)
# movementsTenTickDF = movementsTenTickDF.append(calcMaxAndMidDistForInterval(averageCoordArrayGlobalGoalie, needTickSize, 'averageCoordArrayGlobalGoalie'), ignore_index=True)
# movementsTenTickDF = movementsTenTickDF.append(calcMaxAndMidDistForInterval(absoluteCoordArrayGlobalGoalie, needTickSize, 'absoluteCoordArrayGlobalGoalie'), ignore_index=True)
#
# movementsTenTickDF.to_csv(str(entropyName) + 'movementsTenTickDF.csv')