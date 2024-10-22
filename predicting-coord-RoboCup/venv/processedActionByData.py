from typing import Dict, List
import matplotlib.pyplot as plt
#import seaborn as sns
from config import actionInfoTick, listSide
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
resultOfActionFieldDF = pd.DataFrame(columns=actionInfoTick)

print(resultOfActionFieldDF)

mapNearestPlayersByTick = {}

#print(absolute_Coordinate)

times = absolute_Coordinate.shape[0]

#print(times)

for index, row in absolute_Coordinate.iterrows():
    mapPlayerTick = dict(mapPlayerTemplate)
    if index < 6000:
        mapNowTime = row.to_dict()

        ballInfoObj = BallInfo(CoordinateObject(mapNowTime[' ball_x'], mapNowTime[' ball_y']), 
                               SpeedObject(mapNowTime[' ball_vx'], mapNowTime[' ball_vy']))

        if mapNowTime[' playmode'] != ' play_on':
            #print(f'test playmode is not play_on, skipping...')
            continue

        nearestPlayersL = calculateNearestPlayerToBall(row)
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
        return crossPoint if crossBetweenGoal else None


def isKickToGoal(time: int) -> CoordinateObject | None:
    startPoint = mapInfoFieldWithBallByTick[time]
    nextTick = key+1
    #nextTwoTick = key+2
    #nextThreeTick = key+3
    if ((nextTick) in mapInfoFieldWithBallByTick):
        secondPoint = mapInfoFieldWithBallByTick[nextTick]
        crossFirst = isPreKickToGoal(startPoint, secondPoint)

        if crossFirst != None:
            return crossFirst
    return None

def getNextPlayer(startIndex: int) -> int | None:
    while ((startIndex) in mapInfoFieldWithBallByTick):
        nowState = mapInfoFieldWithBallByTick[startIndex]
        if (len(nowState.nearestPlayers) > 0):
            break
        startIndex += 1
        #setTimeout(3000)
    return startIndex if (startIndex) in mapInfoFieldWithBallByTick else None

def isPrePass(firstPoint: ReturnInfo, secondPoint: ReturnInfo, nowTime: int) -> List[str] | None:
    #print('test isPrePass start')
    lastTick = None
    if (nowTime -1) in mapInfoFieldWithBallByTick:
        lastTick = mapInfoFieldWithBallByTick[nowTime -1]
    if firstPoint.sizeGoal == None \
    and secondPoint.sizeGoal == None:
        isNormalSpeedToPass = (abs(secondPoint.ballInfo.speed.xv) > 0.7 or abs(secondPoint.ballInfo.speed.yv) > 0.7)
        nextLenPlayer = len(secondPoint.nearestPlayers)
        nowLenPlayer = len(firstPoint.nearestPlayers)
        isNormalNearPlayerToPass = nowLenPlayer > 0 and (nextLenPlayer == 0 or not (haveOtherSidePlayer(secondPoint.nearestPlayers)))
        isNotSamePlayer = not (nowLenPlayer == 1 and nextLenPlayer == 1 and firstPoint.nearestPlayers[0] == secondPoint.nearestPlayers[0])
        #print('test isPrePass if first: ', isNormalSpeedToPass, nextLenPlayer, isNormalNearPlayerToPass)

        if (isNormalSpeedToPass and isNormalNearPlayerToPass and isNotSamePlayer):
            # Доделать, что при борьбе или при ведении меча можно отдать пасс напарнику
            print(f'Time {key}')
            #print('test isPrePass if normal')
            print('test isPrePass: ', len(firstPoint.nearestPlayers))
            startPlayer = (firstPoint.nearestPlayers[0] if len(firstPoint.nearestPlayers) == 1 else None) or \
                ((lastTick.nearestPlayers[0] if len(lastTick.nearestPlayers) == 1 else None))
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
            return [startPlayer, nextPassPlayer, startSide]

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
    return None

def appendToResultList(resultdDF, time: int, timeValue: ReturnInfo, action: ACTION_PLAYER, sideWithBall: str, passPair: List[str] | None):
    #print('Start appendToResultList:')
    #print(resultdDF)
    valForAppend = {
        'time': time,
        'action': action.value, 
        'sideWithBall': sideWithBall, 
        'lenOfNearest': len(timeValue.nearestPlayers), 
        'nearestPlayer': timeValue.nearestPlayers,
        'passPair': passPair
    }
    #print('Start  v2 appendToResultList:')
    #print(valForAppend)
    #print(resultdDF)
    #print(type(resultdDF))
    resultdDF = pd.concat([resultdDF, pd.DataFrame([valForAppend])], ignore_index=True)
    return resultdDF

for key, value in mapInfoFieldWithBallByTick.items():
    #if value.sizeGoal == None and (abs(value.ballInfo.speed.xv) > 1 or abs(value.ballInfo.speed.yv) > 1):
    #print(f'Time {key}: {value.toStr()}')
    print(f'\nTime {key}')

    #print(resultOfActionFieldDF)
    kickGoal = isKickToGoal(key)
            #print(f'\kickGoal {kickGoal != None}')
    if kickGoal != None:
        #print(f'Time {key}: {value.toStr()}')
        #print(f'\nTime {key}')
        resultOfActionFieldDF = appendToResultList(resultOfActionFieldDF, key, value, ACTION_PLAYER.KICK_GOAL, listSide[0] if value.sizeGoal in listSide[1] else listSide[1], None)
        #print(f'This is  kicking the goal: {kickGoal.toStr()}\n{value.toStr()}')
        continue

    passPlayers = isPass(key)
    if (passPlayers != None):
            #print(f'Time {key}')
            #print('test isPass passPlayers: ', passPlayers)
            #print('test isPass passPlayers value: ', value.toStr())
            resultOfActionFieldDF = appendToResultList(resultOfActionFieldDF, key, value, ACTION_PLAYER.PASSING, passPlayers[2], passPlayers)
            continue
    
    if kickGoal == None and passPlayers == None and len(value.nearestPlayers) == 1:
        resultOfActionFieldDF = appendToResultList(resultOfActionFieldDF, key, value, ACTION_PLAYER.DRIBLING,listSide[0] if listSide[0] in value.nearestPlayers[0] else listSide[1], None)
        #print(f'test dribling: {value.toStr()}')
        continue
        #print(f'This is  kicking the goal: {kickGoal.toStr()}\n{value.toStr()}')
        #mapPlayerTick[nearestPlayers[0]] = ACTION_PLAYER.DRIBLING.value

    if haveOtherSidePlayer(value.nearestPlayers):
        resultOfActionFieldDF = appendToResultList(resultOfActionFieldDF, key, value, ACTION_PLAYER.BALL_FIGHT, None, None)
        #print(f'test haveOtherSidePlayer: {value.toStr()}')
        continue

    #print(f'test finding ball: {value.toStr()}')
    resultOfActionFieldDF = appendToResultList(resultOfActionFieldDF, key, value, ACTION_PLAYER.SEARCHING, None, None)
        # for player in nearestPlayers:
        #     mapPlayerTick[player] = ACTION_PLAYER.BALL_FIGHT.value


print("test resultOfActionFieldDF: ", resultOfActionFieldDF)

resultOfActionFieldDF.to_csv(f'{teams[0]}-{teams[1]}-action-groundtruth.csv')