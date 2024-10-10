from typing import Dict, List
import matplotlib.pyplot as plt
#import seaborn as sns
from config import resultColumn, resultStatisticColumn, numPeople
from getCoords import *
#from saveModule import infoForTick, storeAgent
import pandas as pd
from random import randint
from processInputData import readFile
from calculateAction import calculateNearestPlayerToBall, getMapActionForPlayerByTick, \
haveOtherSide, nearGoal, CoordinateObject, SpeedObject, getCoordGoalBySide, twoLineCross, roughСompare
import math
from enums import ACTION_PLAYER

class BallInfo:
    location: CoordinateObject
    speed: SpeedObject

    def __init__(self, location: CoordinateObject, speed: SpeedObject):
        self.location = location
        self.speed = speed

    def toStr(self) -> str:
        return f'location: {self.location.toStr()}, speed: {self.speed.toStr()}'

class ReturnInfo:
    def __init__(self, nearestPlayers: List[str] = [], sizeGoal: str = None, ballInfo: BallInfo = None):
        self.nearestPlayers = nearestPlayers
        self.sizeGoal = sizeGoal
        self.ballInfo = ballInfo

    def toStr(self) -> str:
        return f'ballInfo: {self.ballInfo.toStr()}\n, sizeGoal: {self.sizeGoal}\n nearestPlayers: {self.nearestPlayers}\n'


absolute_Coordinate = pd.read_csv(pathDefault+prefixFiles+'groundtruth.csv', sep=',')

mapPlayerTemplate = getMapActionForPlayerByTick()

mapInfoFieldWithBallByTick: Dict[int, ReturnInfo] = dict()

mapNearestPlayersByTick = {}

#print(absolute_Coordinate)

times = absolute_Coordinate.shape[0]

#print(times)

for index, row in absolute_Coordinate.iterrows():
    mapPlayerTick = dict(mapPlayerTemplate)
    if index < 6000:
        #print(f'test new tick time {index}______\n')
        mapNowTime = row.to_dict()

        ballInfoObj = BallInfo(CoordinateObject(mapNowTime[' ball_x'], mapNowTime[' ball_y']), 
                               SpeedObject(mapNowTime[' ball_vx'], mapNowTime[' ball_vy']))

        #print(f'test playmode: ', mapNowTime[' playmode'])

        if mapNowTime[' playmode'] != ' play_on':
            #print(f'test playmode is not play_on, skipping...')
            continue

        nearestPlayersL = calculateNearestPlayerToBall(row)
        #print('test __ nearestPlayers: ', nearestPlayersL.copy())
        nearGoalSide = nearGoal(row)

        #print('test dribling: ', len(nearestPlayers) == 1)

        # if len(nearestPlayers) == 1:
        #     mapPlayerTick[nearestPlayers[0]] = ACTION_PLAYER.DRIBLING.value
            
        # #print('test haveOtherSide: ', haveOtherSide(nearestPlayers))
        
        # if haveOtherSide(nearestPlayers):
        #     for player in nearestPlayers:
        #         mapPlayerTick[player] = ACTION_PLAYER.BALL_FIGHT.value
        #mapPlayerTick
        #print(row, index)
        #print(nearestPlayers)
        # for player in nearestPlayers:
        #     print(f"{player}: {mapPlayerTick[player]}")

        mapInfoFieldWithBallByTick[mapNowTime['# time']] = ReturnInfo(list(nearestPlayersL), nearGoalSide, ballInfoObj)
    else:
        break

print('Start view nearestPlayer')

def between(A, B, C):
    return A <= B <= C or C <= B <= A

def betweenRough(A, B, C):
    print(f'test betweenRough: floor({math.floor(B)}), ceil({math.ceil(B)}) ', A <= math.ceil(B) <= C, C <= math.floor(B) <= A)
    return A <= math.ceil(B) <= C or C <= math.floor(B) <= A


def isPreKickToGoal(firstPoint: ReturnInfo, secondPoint: ReturnInfo) -> CoordinateObject | None:
    if firstPoint.sizeGoal != None \
    and secondPoint.sizeGoal != None \
    and (abs(firstPoint.ballInfo.speed.xv) > 1.3 or abs(firstPoint.ballInfo.speed.yv) > 1.3) \
    and (abs(secondPoint.ballInfo.speed.xv) > 1 or abs(secondPoint.ballInfo.speed.yv) > 1):
        listGoalCoords = getCoordGoalBySide(value.sizeGoal)
        crossPoint = twoLineCross(listGoalCoords[0], listGoalCoords[1], firstPoint.ballInfo.location, secondPoint.ballInfo.location)
        #print(f'test isPreKickToGoal crossPoint: {crossPoint.toStr()}')
        crossBetweenGoal = betweenRough(listGoalCoords[0].y, crossPoint.y, listGoalCoords[1].y)
        #print(f'test isPreKickToGoal listGoalCoords: {listGoalCoords[0].y}, {listGoalCoords[1].y}')
        #print(f'test isPreKickToGoal crossBetweenGoal: {crossBetweenGoal}')
        return crossPoint if crossBetweenGoal else None


def isKickToGoal(time: int) -> CoordinateObject | None:
    startPoint = mapInfoFieldWithBallByTick[time]
    nextTick = key+1
    #nextTwoTick = key+2
    #nextThreeTick = key+3
    if ((nextTick) in mapInfoFieldWithBallByTick):
    #if ((nextTick) in mapInfoFieldWithBallByTick) and ((nextTwoTick) in mapInfoFieldWithBallByTick) and ((nextThreeTick) in mapInfoFieldWithBallByTick):
        secondPoint = mapInfoFieldWithBallByTick[nextTick]
        #thirdPoint = mapInfoFieldWithBallByTick[nextTwoTick]
        #fourPoint = mapInfoFieldWithBallByTick[nextThreeTick]
        #print('test isKickToGoal startPoint: ', startPoint.toStr())
        #print('test isKickToGoal secondPoint: ', secondPoint.toStr())
        #print('test isKickToGoal thirdPoint: ', thirdPoint.toStr())
        #print('test isKickToGoal fourPoint: ', fourPoint.toStr())
        crossFirst = isPreKickToGoal(startPoint, secondPoint)
        #crossSecond = isPreKickToGoal(secondPoint, thirdPoint)
        #crossThird = isPreKickToGoal(thirdPoint, fourPoint)
        # if crossFirst != None:
        #     print('test isKickToGoal crossFirst: ', crossFirst.toStr())
        # else:
        #     print('test isKickToGoal crossFirst fail')

        # if crossSecond != None:
        #     print('test isKickToGoal crossSecond: ', crossSecond.toStr())
        # else:
        #     print('test isKickToGoal crossSecond fail')

        # if crossThird != None:
        #     print('test isKickToGoal crossThird: ', crossThird.toStr())
        # else:
        #     print('test isKickToGoal crossThird fail')

        if crossFirst != None:
        #if crossFirst != None and crossSecond != None and roughСompare(crossFirst, crossSecond):
            return crossFirst
    return None

    # if startPoint.sizeGoal != None and (abs(startPoint.ballInfo.speed.xv) > 1 or abs(startPoint.ballInfo.speed.yv) > 1):
    # #if (abs(value.ballInfo.speed.xv) > 2 or abs(value.ballInfo.speed.yv) > 2):
    #     #print(f'Time {key}: {value.toStr()}')
    #     #print(f'Time type {type(key)}')
    #     nextTick = key+1
    #     if (nextTick) in mapInfoFieldWithBallByTick:
    #         print(f'Time {key}: {value.toStr()}')
    #         print(f'Time exist {nextTick}')
    #         nextTickValue = mapInfoFieldWithBallByTick[nextTick]
    #         print(f'Time nextTickValue: {nextTickValue.toStr()}')
    #         listGoalCoords = getCoordGoalBySide(value.sizeGoal)
    #         isCross = twoLineCross(listGoalCoords[0], listGoalCoords[1], value.ballInfo.location, nextTickValue.ballInfo.location)
    #         print(f'Time isCross: {isCross.toStr()}')
    #         if isCross:
    #             print(f'This is  kicking the goal')

for key, value in mapInfoFieldWithBallByTick.items():
    if value.sizeGoal != None and (abs(value.ballInfo.speed.xv) > 1 or abs(value.ballInfo.speed.yv) > 1):
            print(f'\nTime {key}')
            #print(f'Time {key}: {value.toStr()}')
            kickGoal = isKickToGoal(key)
            #print(f'\kickGoal {kickGoal != None}')
            if kickGoal != None:
                #print(f'Time {key}: {value.toStr()}')
                #print(f'\nTime {key}')
                print(f'This is  kicking the goal: {kickGoal.toStr()}\n{value.toStr()}')
    # #if (abs(value.ballInfo.speed.xv) > 2 or abs(value.ballInfo.speed.yv) > 2):
    #     #print(f'Time {key}: {value.toStr()}')
    #     #print(f'Time type {type(key)}')
    #     nextTick = key+1
    #     if (nextTick) in mapInfoFieldWithBallByTick:
    #         print(f'Time {key}: {value.toStr()}')
    #         print(f'Time exist {nextTick}')
    #         nextTickValue = mapInfoFieldWithBallByTick[nextTick]
    #         print(f'Time nextTickValue: {nextTickValue.toStr()}')
    #         listGoalCoords = getCoordGoalBySide(value.sizeGoal)
    #         isCross = twoLineCross(listGoalCoords[0], listGoalCoords[1], value.ballInfo.location, nextTickValue.ballInfo.location)
    #         print(f'Time isCross: {isCross.toStr()}')
    #         if isCross:
    #             print(f'This is  kicking the goal')


#print(mapNearestPlayersByTick)
# for item, index in range(times):
#     print(times)

#print(readData)

# for item in teams:
#     print('team - ', item)
#     playerList[item] = {}
#     for ind in range(numPeople):
#         print('player', ind)
#         playerList[item][(ind+1)] = storeAgent()
#         varianceArray = []
#         absoluteCoordArray = []
#         playerName = None
#         difference = []
#         angleOrientation = None
#         angleFlag = None
#         valueLackFlag = 0
#         for elems in resProcessTeam[item][(ind+1)]:
#             print('time - ', elems['time'], item, ind)

#             # if (elems['time'] > 3000):
#             #     break

#             nowPlObj = playerList[item][(ind + 1)]
#             # timeRow = absolute_Coordinate[absolute_Coordinate['# time'] == elems['time']]
#             absoluteCoord = getAbsolutedCoordinate(item, (ind+1), elems['time'], angleOrientation, False)
#             if (absoluteCoord == None):
#                 continue

#             angleOrientation = absoluteCoord.angleFlag
#             angleFlag = absoluteCoord.angleOrientation
#             nowPlayer = absoluteCoord.nowPlayer
#             playerName = absoluteCoord.nowPlayer
#             absoluteX = absoluteCoord.absoluteX
#             absoluteY = absoluteCoord.absoluteY

#             absoluteCoordArray.append({'x': absoluteX, 'y': absoluteY})
#             paramsTick = paramsForCalcPosition(elems, nowPlObj, angleOrientation,
#                                                valueLackFlag, varianceArray, angleFlag, absoluteX, absoluteY)
#             ansInfoForTick = calcInfoForTick(paramsTick, resMovePTeam, item, ind, absoluteCoordArray)
#             if (ansInfoForTick == None):
#                 continue
#             angleOrientation = ansInfoForTick.angleOrientation
#             valueLackFlag = ansInfoForTick.valueLackFlag
#             averageX = ansInfoForTick.averageX
#             averageY = ansInfoForTick.averageY
#             varianceArray = ansInfoForTick.varianceArray

#             newObj = infoForTick(averageX, averageY, absoluteX, absoluteY, ansInfoForTick.radian,
#                                  ansInfoForTick.speedX, ansInfoForTick.speedY, ansInfoForTick.arrPlayer)
#             playerList[item][(ind+1)].addNewTickInfo(newObj)
#             if (item == teams[0] and (ind+1) == numberTeamGoalie[0]) or \
#                     (item == teams[1] and (ind+1) == numberTeamGoalie[1]):
#                 averageCoordArrayGlobalGoalie.append({'x': averageX, 'y': averageY})
#                 absoluteCoordArrayGlobalGoalie.append({'x': absoluteX, 'y': absoluteY})
#             else:
#                 averageCoordArrayGlobal.append({'x': averageX, 'y': averageY})
#                 absoluteCoordArrayGlobal.append({'x': absoluteX, 'y': absoluteY})
#             removeList = playerList[item][(ind + 1)].removeList()
#             listPredict = playerList[item][(ind + 1)].predictForDisappearedPlayer(removeList)
#             playerList[item][(ind + 1)].savePredictCoords(listPredict)
#             for nn in playerList[item][(ind + 1)].removePlayer:
#                 removePlayer = playerList[item][(ind + 1)].removePlayer[nn]

#             valueTickWithPredictVal = paramsForDataTickWithPredictVal(listPredict, elems, predictObj, angleOrientation)
#             predictObj = createDataTickWithPredictVal(valueTickWithPredictVal, nowPlayer)

#             differenceX = np.abs(np.abs(averageX) - np.abs(absoluteX))
#             differenceY = np.abs(np.abs(averageY) - np.abs(absoluteY))
#             difference.append({'x': differenceX, 'y': differenceY})

#             new_row = {'time': elems['time'], 'player': nowPlayer, 'calc x': round(averageX, 4),
#                        'calc y': round(averageY, 4), 'absolute x': absoluteX, 'absolute y': absoluteY,
#                        'differenceX': round(differenceX, 4), 'differenceY': round(differenceY, 4)}
#             resultDF = resultDF.append(new_row, ignore_index=True)