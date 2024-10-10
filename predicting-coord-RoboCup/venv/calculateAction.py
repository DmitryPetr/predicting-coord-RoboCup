from typing import Dict, List
import matplotlib.pyplot as plt
from config import numPeople, nearestRadius, listSide, listGoalLeft, listGoalRight, Flags, nearestGoalRadius
from getCoords import *
import pandas as pd
import math
from enums import ACTION_PLAYER

class SpeedObject:
    xv: float
    yv: float

    def __init__(self, xv = 0.0, yv = 0.0):
        self.xv = xv
        self.yv = yv

    def toStr(self) -> str:
        return f'xv: {self.xv}, yv: {self.yv}'

class CoordinateObject:
    x: float
    y: float

    def __init__(self, x = 0.0, y = 0.0):
        self.x = x
        self.y = y

    def toStr(self) -> str:
        return f'x: {self.x}, y: {self.y}'
    
    def compare(self, object) -> str:
        return self.x == object.x and self.y == object.y

def getMapActionForPlayerByTick() -> Dict[str, ACTION_PLAYER]:
    mapPlayer = {}
    for idxTeam, sideTeam in enumerate(listSide):
        for playerIndex in range(numPeople):
            isGoalie = (playerIndex+1) == numberTeamGoalie[idxTeam]
            namePlayer = f"{sideTeam}G{(playerIndex+1)}" if isGoalie else f"{sideTeam}{(playerIndex+1)}"
            mapPlayer[namePlayer] = ACTION_PLAYER.SEARCHING.value
    return mapPlayer

def isInsideRadius(center: CoordinateObject, object: CoordinateObject, r: float) -> bool:
    isInside = (center.x - object.x)**2 / r**2 + (center.y - object.y)**2 / r**2 < 1

    return isInside

def haveOtherSide(listPlayer: List[str]) -> bool:
    #print('haveOtherSide: ', len(listPlayer), listPlayer and len(listPlayer) < 2)

    if listPlayer != None and len(listPlayer) < 2:
        return False

    #print('haveOtherSide after: ', len(listPlayer))
    startSide = listSide[0] if listSide[0] in listPlayer[0] else listSide[1]
    for player in listPlayer:
        if startSide not in player: 
            return True

    return False

def nearGoal(nowTime: pd.Series) -> str:
    mapNowTime = nowTime.to_dict()
    ballCoord = CoordinateObject(mapNowTime[' ball_x'], mapNowTime[' ball_y'])

    for flag in listGoalLeft:
        valueFlag = Flags[flag]
        point = CoordinateObject(valueFlag['x'], valueFlag['y'])
        if isInsideRadius(ballCoord, point, nearestGoalRadius):
            return listSide[0]
        
    for flag in listGoalRight:
        valueFlag = Flags[flag]
        point = CoordinateObject(valueFlag['x'], valueFlag['y'])
        if isInsideRadius(ballCoord, point, nearestGoalRadius):
            return listSide[1]

    return None

def calculateNearestPlayerToBall(nowTime: pd.Series) -> List[str]:
    listNearest = []
    mapNowTime = nowTime.to_dict()
    time = mapNowTime['# time']
    #print('___ test calculateNearestPlayerToBall time: ', time)
    #print(f'test __ calculateNearestPlayerToBall time: {mapNowTime['# time']}')
    ballCoord = CoordinateObject(mapNowTime[' ball_x'], mapNowTime[' ball_y'])
    for idxTeam, sideTeam in enumerate(listSide):
        for playerIndex in range(numPeople):
            isGoalie = (playerIndex+1) == numberTeamGoalie[idxTeam]
            namePlayer = f"{sideTeam}G{(playerIndex+1)}" if isGoalie else f"{sideTeam}{(playerIndex+1)}"
            playerCoord = CoordinateObject(mapNowTime[f' {namePlayer} x'], mapNowTime[f' {namePlayer} y'])

            if isInsideRadius(ballCoord, playerCoord, nearestRadius):
                    listNearest.append(namePlayer)
                    #print('test isInsideRadius: ', namePlayer)

    return listNearest


#float dot[2];  // точка пересечения https://habr.com/ru/articles/523440/

def twoLineCross(
    goalOne: CoordinateObject,
    goalTwo: CoordinateObject, 
    ballLineStart: CoordinateObject, 
    ballLineEnd: CoordinateObject
):
    n: float = 0.0
    if goalTwo.y - goalOne.y != 0:  # a(y)
        q = (goalTwo.x - goalOne.x) / (goalOne.y - goalTwo.y);   
        sn = (ballLineStart.x - ballLineEnd.x) + (ballLineStart.y - ballLineEnd.y) * q; 
        if not sn: # c(x) + c(y)*q
          return None
        fn = (ballLineStart.x - goalOne.x) + (ballLineStart.y - goalOne.y) * q;   # b(x) + b(y)*q
        n = fn / sn
    else:
        if not(ballLineStart.y - ballLineEnd.y): 
            return None #  b(y)
        n = (ballLineStart.y - goalOne.y) / (ballLineStart.y - ballLineEnd.y)   # c(y)/b(y)

    crossCoord = CoordinateObject(ballLineStart.x + (ballLineEnd.x - ballLineStart.x) * n, ballLineStart.y + (ballLineEnd.y - ballLineStart.y) * n)

    #dot[0] = x3 + (x4 - x3) * n;  // x3 + (-b(x))*n
    #dot[1] = y3 + (y4 - y3) * n;  // y3 +(-b(y))*n
    return crossCoord


def getCoordGoalBySide(side: str) -> List[CoordinateObject]:
    listGoalCoord = []

    if side == listSide[0]:
        valueFlag = Flags[listGoalLeft[0]]
        listGoalCoord.append(CoordinateObject(valueFlag['x'], valueFlag['y']))
        valueFlag = Flags[listGoalLeft[1]]
        listGoalCoord.append(CoordinateObject(valueFlag['x'], valueFlag['y']))
    else: 
        valueFlag = Flags[listGoalRight[0]]
        listGoalCoord.append(CoordinateObject(valueFlag['x'], valueFlag['y']))
        valueFlag = Flags[listGoalRight[1]]
        listGoalCoord.append(CoordinateObject(valueFlag['x'], valueFlag['y']))

    return listGoalCoord


def roughСompare(first: CoordinateObject, second: CoordinateObject) -> str:
    return first.x == second.x and math.floor(first.y) == math.floor(second.y)
