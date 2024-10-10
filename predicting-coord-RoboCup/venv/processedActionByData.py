from typing import Dict, List
import matplotlib.pyplot as plt
#import seaborn as sns
from config import resultColumn, resultStatisticColumn, numPeople, listSide
from getCoords import *
#from saveModule import infoForTick, storeAgent
import pandas as pd
from random import randint
from processInputData import readFile
from calculateAction import calculateNearestPlayerToBall, getMapActionForPlayerByTick, \
haveOtherSidePlayer, nearGoal, CoordinateObject, SpeedObject, getCoordGoalBySide, twoLineCross, roughСompare
import math
from enums import ACTION_PLAYER
import time
def setTimeout(delay):
    time.sleep(delay / 1000)
    #callback()


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

def getNextPlayer(startIndex: int) -> int | None:
    #print('test getNextPlayer if startIndex: ', startIndex)
    while ((startIndex) in mapInfoFieldWithBallByTick):
        nowState = mapInfoFieldWithBallByTick[startIndex]
        #print('test getNextPlayer in while main startIndex: ', startIndex)
        #print('test getNextPlayer in while main nowState: ', nowState.toStr())
        #print('test getNextPlayer in while main: ', len(nowState.nearestPlayers))
        if (len(nowState.nearestPlayers) > 0):
            #print('test getNextPlayer in while break: ', startIndex)
            break
        startIndex += 1
        #setTimeout(3000)
    #print('test getNextPlayer if startIndex after while: ', startIndex)
    return startIndex if (startIndex) in mapInfoFieldWithBallByTick else None

def isPrePass(firstPoint: ReturnInfo, secondPoint: ReturnInfo, nowTime: int) -> List[str] | None:
    #print('test isPrePass start')
    if firstPoint.sizeGoal == None \
    and secondPoint.sizeGoal == None:
        isNormalSpeedToPass = (abs(secondPoint.ballInfo.speed.xv) > 0.7 or abs(secondPoint.ballInfo.speed.yv) > 0.7)
        nextLenPlayer = len(secondPoint.nearestPlayers)
        nowLenPlayer = len(firstPoint.nearestPlayers)
        isNormalNearPlayerToPass = nowLenPlayer > 0 and (nextLenPlayer == 0 or not (haveOtherSidePlayer(secondPoint.nearestPlayers)))
        #print('test isPrePass if first: ', isNormalSpeedToPass, nextLenPlayer, isNormalNearPlayerToPass)

        if (isNormalSpeedToPass and isNormalNearPlayerToPass):
            # Доделать, что при борьбе или при ведении меча можно отдать пасс напарнику
            print(f'Time {key}')
            #print('test isPrePass if normal')
            print('test isPrePass: ', len(firstPoint.nearestPlayers))
            startPlayer = firstPoint.nearestPlayers[0] if len(firstPoint.nearestPlayers) == 1 else None
            startSide = listSide[0] if startPlayer != None and listSide[0] in startPlayer else listSide[1]
            #print('test isPrePass if startPlayer: ', startPlayer, startSide)
            nextIndex = getNextPlayer(nowTime+2)
            if nextIndex == None:
                return None
            #print('test isPrePass if nextIndex: ', nextIndex)
            nowState = mapInfoFieldWithBallByTick[nextIndex]
            #print('test isPrePass if nowState: ', nowState.toStr())

            #print('test isPrePass if nowState before if: ', len(nowState.nearestPlayers), haveOtherSidePlayer(nowState.nearestPlayers))
            if (len(nowState.nearestPlayers) > 1 or haveOtherSidePlayer(nowState.nearestPlayers)):
                return None
            
            nextPassPlayer = nowState.nearestPlayers[0]

            if (not (startSide in nextPassPlayer)):
                return None
            #print('test isPrePass if nowState after if')
            return [startPlayer, nextPassPlayer]

    return None

def isPass(time: int) -> CoordinateObject | None:
    startPoint = mapInfoFieldWithBallByTick[time]
    if startPoint.sizeGoal == None:
        #print(f'Time {time}: {value.toStr()}')
        nextTick = key+1
        if ((nextTick) in mapInfoFieldWithBallByTick):
            secondPoint = mapInfoFieldWithBallByTick[nextTick]
            #print('test isPass startPoint: ', startPoint.toStr())
            #print('test isPass secondPoint: ', secondPoint.toStr())

            passPlayers = isPrePass(startPoint, secondPoint, time)

            return passPlayers
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

            #if crossFirst != None and crossSecond != None and roughСompare(crossFirst, crossSecond):
    return None

for key, value in mapInfoFieldWithBallByTick.items():
    #if value.sizeGoal == None and (abs(value.ballInfo.speed.xv) > 1 or abs(value.ballInfo.speed.yv) > 1):
    #print(f'Time {key}: {value.toStr()}')
    passPlayers = isPass(key)
    if (passPlayers != None):
            #print(f'Time {key}')
            print('test isPass passPlayers: ', passPlayers)
    
    # if len(value.nearestPlayers) > 2:
    #     print(f'Time {key}: {value.toStr()}')
    # if value.sizeGoal != None and (abs(value.ballInfo.speed.xv) > 1 or abs(value.ballInfo.speed.yv) > 1):
    #         print(f'\nTime {key}')
    #         #print(f'Time {key}: {value.toStr()}')
    #         kickGoal = isKickToGoal(key)
    #         #print(f'\kickGoal {kickGoal != None}')
    #         if kickGoal != None:
    #             #print(f'Time {key}: {value.toStr()}')
    #             #print(f'\nTime {key}')
    #             print(f'This is  kicking the goal: {kickGoal.toStr()}\n{value.toStr()}')