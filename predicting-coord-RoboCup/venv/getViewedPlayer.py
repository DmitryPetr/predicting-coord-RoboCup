import matplotlib.pyplot as plt
import seaborn as sns
from config import resultColumn, resultStatisticColumn, resultPredictColumn, numPeople
from getCoords import *
from saveModule import infoForTick, storeAgent
from random import randint
from statistic import createDataForPlt, addDataForStatDist, paramsCreateStats
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


#print(resProcessTeam)
#print(dataViewMap)


for item in teams:
    print('team - ', item)
    playerList[item] = {}
    for ind in range(numPeople):
        print('player', ind)
        playerList[item][(ind+1)] = storeAgent()
        varianceArray = []
        absoluteCoordArray = []
        playerName = None
        difference = []
        angleOrientation = None
        angleFlag = None
        valueLackFlag = 0
        for elems in resProcessTeam[item][(ind+1)]:
            print('time - ', elems['time'], item, ind)

            if (elems['time'] > 100):
                break

            nowPlObj = playerList[item][(ind + 1)]
            timeRow = absolute_Coordinate[absolute_Coordinate['# time'] == elems['time']]
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
            print('paramsTick.arrPlayer: ', paramsTick.arrPlayer)
            # getPa = calcPosOtherPl(paramsTick, resMovePTeam, item, ind)
            # if (ansInfoForTick == None):
            #     continue
            # angleOrientation = ansInfoForTick.angleOrientation
            # valueLackFlag = ansInfoForTick.valueLackFlag
            # averageX = ansInfoForTick.averageX
            # averageY = ansInfoForTick.averageY
            # varianceArray = ansInfoForTick.varianceArray

            # newObj = infoForTick(averageX, averageY, absoluteX, absoluteY, ansInfoForTick.radian,
            #                      ansInfoForTick.speedX, ansInfoForTick.speedY, ansInfoForTick.arrPlayer)
            # playerList[item][(ind+1)].addNewTickInfo(newObj)
            # if (item == teams[0] and (ind+1) == numberTeamGoalie[0]) or \
            #         (item == teams[1] and (ind+1) == numberTeamGoalie[1]):
            #     averageCoordArrayGlobalGoalie.append({'x': averageX, 'y': averageY})
            #     absoluteCoordArrayGlobalGoalie.append({'x': absoluteX, 'y': absoluteY})
            # else:
            #     averageCoordArrayGlobal.append({'x': averageX, 'y': averageY})
            #     absoluteCoordArrayGlobal.append({'x': absoluteX, 'y': absoluteY})
            # removeList = playerList[item][(ind + 1)].removeList()
            # listPredict = playerList[item][(ind + 1)].predictForDisappearedPlayer(removeList)
            # playerList[item][(ind + 1)].savePredictCoords(listPredict)
            # for nn in playerList[item][(ind + 1)].removePlayer:
            #     removePlayer = playerList[item][(ind + 1)].removePlayer[nn]

            # valueTickWithPredictVal = paramsForDataTickWithPredictVal(listPredict, elems, predictObj, angleOrientation)
            # predictObj = createDataTickWithPredictVal(valueTickWithPredictVal, nowPlayer)

            # differenceX = np.abs(np.abs(averageX) - np.abs(absoluteX))
            # differenceY = np.abs(np.abs(averageY) - np.abs(absoluteY))
            # difference.append({'x': differenceX, 'y': differenceY})

            # new_row = {'time': elems['time'], 'player': nowPlayer, 'calc x': round(averageX, 4),
            #            'calc y': round(averageY, 4), 'absolute x': absoluteX, 'absolute y': absoluteY,
            #            'differenceX': round(differenceX, 4), 'differenceY': round(differenceY, 4)}
            # resultDF = resultDF.append(new_row, ignore_index=True)