import matplotlib.pyplot as plt
import seaborn as sns
from config import resultColumn, resultStatisticColumn, resultPredictColumn, numPeople, listSide, nearestRadius, middleRadius
from getCoords import *
from saveModule import infoForTick, storeAgent, posPlayer, otherPlayer
from random import randint
from statistic import createDataForPlt, addDataForStatDist, paramsCreateStats
from processInputData import readFile, createMapViewFlag, createMapViewMove, \
    calcInfoForTick, paramsForCalcPosition, createDataTickWithPredictVal, paramsForDataTickWithPredictVal

from calculateAction import isInsideRadius, CoordinateObject, nearGoalWithCoordinate

resFlagsTeam = {}
resMovTeam = {}
resProcessTeam = {}
resMovePTeam = {}
resMoveBTeam = {}
predictObj = {}
playerList = {}
entropyName = randint(1000, 100000)

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

class returnLenOfObject:
    def __init__(self, lenOfNearTeam, lenOfNearOp, lenMidOfTeam, lenMidOfOp, nearGoal):
        self.lenOfNearTeam = lenOfNearTeam
        self.lenOfNearOp = lenOfNearOp
        self.lenMidOfTeam = lenMidOfTeam
        self.lenMidOfOp = lenMidOfOp
        self.nearGoal = nearGoal

    def toStr(self):
        return f"\nlenOfNearTeam: {self.lenOfNearTeam},\n lenOfNearOp: {self.lenOfNearOp},\n lenMidOfTeam: {self.lenMidOfTeam},\n lenMidOfOp: {self.lenMidOfOp}, \nnearGoal: {self.nearGoal}"

def calculatePlayerNearBall(nowPlayer: str, nowArrayPlayer: otherPlayer) -> returnLenOfObject:
    lenOfNearTeam = 0
    lenOfNearOp = 0
    lenMidOfTeam = 0
    lenMidOfOp = 0

    ballCoords: posPlayer = nowArrayPlayer.mapPlayer['b dist']

    nowSide = listSide[0] if teams[0] in nowPlayer else listSide[1]

    coordBallObject = CoordinateObject(ballCoords.x, ballCoords.y)

    for player in nowArrayPlayer.viewPlayer:
        if player == 'b dist':
            continue

        playerSide = listSide[0] if teams[0] in player else listSide[1]
        playerCoords: posPlayer = nowArrayPlayer.mapPlayer[player]

        inNearRadius = isInsideRadius(coordBallObject, CoordinateObject(playerCoords.x, playerCoords.y), nearestRadius)

        if inNearRadius: 
            if nowSide == playerSide:
                lenOfNearTeam += 1
            else: 
                lenOfNearOp += 1
            continue

        inMiddleRadius = isInsideRadius(coordBallObject, CoordinateObject(playerCoords.x, playerCoords.y), middleRadius)

        if inMiddleRadius: 
            if nowSide == playerSide:
                lenMidOfTeam += 1
            else: 
                lenMidOfOp += 1
            continue

    nearGoal = nearGoalWithCoordinate(coordBallObject)

    return returnLenOfObject(lenOfNearTeam, lenOfNearOp, lenMidOfTeam, lenMidOfOp, nearGoal)


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

            print('time elems- ', elems)

            if (elems['time'] > 3000):
                break

            nowPlObj = playerList[item][(ind + 1)]
            print('test nowPlObj: ', nowPlObj)
            #print('test nowPlObj: ', nowPlObj.storeCoord)
            # timeRow = absolute_Coordinate[absolute_Coordinate['# time'] == elems['time']]
            #print("before getAbsCoords")
            absoluteCoord = getAbsolutedCoordinate(item, (ind+1), elems['time'], angleOrientation, False)
            if (absoluteCoord == None):
                continue
            
            #print("Test after getCoords")
            angleOrientation = absoluteCoord.angleFlag
            angleFlag = absoluteCoord.angleOrientation
            nowPlayer = absoluteCoord.nowPlayer
            playerName = absoluteCoord.nowPlayer
            absoluteX = absoluteCoord.absoluteX
            absoluteY = absoluteCoord.absoluteY

            absoluteCoordArray.append({'x': absoluteX, 'y': absoluteY})
            paramsTick = paramsForCalcPosition(elems, nowPlObj, angleOrientation,
                                               valueLackFlag, varianceArray, angleFlag, absoluteX, absoluteY)
            print("before calc info tick: ", nowPlayer)
            ansInfoForTick = calcInfoForTick(paramsTick, resMovePTeam, item, ind, absoluteCoordArray)
            print("after calc tick info")
            if (ansInfoForTick == None):
                continue

            nowArrayPlayer = ansInfoForTick.arrPlayer
            containBall = 'b dist' in nowArrayPlayer.viewPlayer
            lenViewPlayer = len(nowArrayPlayer.viewPlayer)

            print("test viewPlayer tick info", nowArrayPlayer.viewPlayer)

            print(f"after viewPlayer tick info field: {containBall} {lenViewPlayer}")

            if ( not containBall):
                print("test not a ball")
                continue

            print("after calc tick info after", nowArrayPlayer.mapPlayer)

            if (containBall and lenViewPlayer < 2):
                print("small people number near ball")
                continue

                      

            print("after calc tick info after two check", nowArrayPlayer.mapPlayer)

            returnCalcLen: returnLenOfObject = calculatePlayerNearBall(nowPlayer, nowArrayPlayer)

            print("after calc tick info after returnCalLen", returnCalcLen.toStr())

            angleOrientation = ansInfoForTick.angleOrientation
            valueLackFlag = ansInfoForTick.valueLackFlag
            averageX = ansInfoForTick.averageX
            averageY = ansInfoForTick.averageY
            varianceArray = ansInfoForTick.varianceArray

            newObj = infoForTick(averageX, averageY, absoluteX, absoluteY, ansInfoForTick.radian,
                                 ansInfoForTick.speedX, ansInfoForTick.speedY, ansInfoForTick.arrPlayer)
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
            
            #resultDF = resultDF.append(new_row, ignore_index=True)
            resultDF = pd.concat([resultDF, pd.DataFrame([new_row])], ignore_index=True)
