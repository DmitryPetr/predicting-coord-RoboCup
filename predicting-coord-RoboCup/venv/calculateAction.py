from typing import Dict, List
import matplotlib.pyplot as plt
from config import numPeople, nearestRadius, listSide
from getCoords import *
import pandas as pd
from enums import ACTION_PLAYER

class coordinateObject:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def toStr(self) -> str:
        return f'x: {self.x}, y: {self.y}'

def getMapActionForPlayerByTick() -> Dict[str, ACTION_PLAYER]:
    mapPlayer = {}
    for idxTeam, sideTeam in enumerate(listSide):
        for playerIndex in range(numPeople):
            isGoalie = (playerIndex+1) == numberTeamGoalie[idxTeam]
            namePlayer = f"{sideTeam}G{(playerIndex+1)}" if isGoalie else f"{sideTeam}{(playerIndex+1)}"
            mapPlayer[namePlayer] = ACTION_PLAYER.SEARCHING.value
    return mapPlayer

def isInsideRadius(center: coordinateObject, object: coordinateObject, r: float):
    isInside = (center.x - object.x)**2 / r**2 + (center.y - object.y)**2 / r**2 < 1

    return isInside

def haveOtherSide(listPlayer: List[str]) -> bool:
    print('haveOtherSide: ', len(listPlayer), listPlayer and len(listPlayer) < 2)

    if listPlayer != None and len(listPlayer) < 2:
        return False

    print('haveOtherSide after: ', len(listPlayer))
    startSide = listSide[0] if listSide[0] in listPlayer[0] else listSide[1]
    for player in listPlayer:
        if startSide not in player: 
            return True

    return False

def calculateNearestPlayerToBall(nowTime: pd.Series) -> List[str]:
    listNearest = []
    mapNowTime = nowTime.to_dict()
    ballCoord = coordinateObject(mapNowTime[' ball_x'], mapNowTime[' ball_y'])
    for idxTeam, sideTeam in enumerate(listSide):
        for playerIndex in range(numPeople):
            isGoalie = (playerIndex+1) == numberTeamGoalie[idxTeam]
            namePlayer = f"{sideTeam}G{(playerIndex+1)}" if isGoalie else f"{sideTeam}{(playerIndex+1)}"
            playerCoord = coordinateObject(mapNowTime[f' {namePlayer} x'], mapNowTime[f' {namePlayer} y'])

            if isInsideRadius(ballCoord, playerCoord, nearestRadius):
                    listNearest.append(namePlayer)
                    #print('test isInsideRadius: ', namePlayer)

    return listNearest