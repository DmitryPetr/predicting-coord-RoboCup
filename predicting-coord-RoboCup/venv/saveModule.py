from collections import deque
import numpy as np

class posPlayer:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle

class otherPlayer:
    def __init__(self):
        self.viewPlayer = []
        self.mapPlayer = {}

    def addNewViewPlayer(self, playerName, posPlayer):
        self.viewPlayer.append(playerName)
        self.mapPlayer[playerName] = posPlayer


class infoForTick:
    def __init__(self, x, y, absX, absY, angle, speedX, speedY, otherPlayers):
        self.x = x
        self.y = y
        self.absX = absX
        self.absY = absY
        self.angle = angle
        self.speedX = speedX
        self.speedY = speedY
        self.Players = otherPlayers

class storeAgent:
    def __init__(self):
        self.storeCoord = deque([], maxlen=10)
        self.removePlayer = {}

    def addNewTickInfo(self, newInfo):
        if (len(self.storeCoord) < self.storeCoord.maxlen):
            self.storeCoord.append(newInfo)
        else:
            self.storeCoord.popleft()
            self.storeCoord.append(newInfo)
        for elems in newInfo.Players.viewPlayer:
            if elems in self.removePlayer:
                del self.removePlayer[elems]
        lenName = []
        for elems in self.removePlayer:
            lenName.append(elems)
        for elems in lenName:
            if len(self.removePlayer[elems]) > 10:
                del self.removePlayer[elems]

    def getLastItem(self):
        return self.storeCoord[len(self.storeCoord)-1] if len(self.storeCoord) > 0 else None

    def removeList(self):
        remove = []
        if (len(self.storeCoord) > 3):
            current = self.storeCoord[len(self.storeCoord)-2].Players.viewPlayer
            target = self.storeCoord[len(self.storeCoord)-1].Players.viewPlayer
            #print('removeList step 1 current' , current)
            #print('removeList step 1 target', target)
            intersection = set(current) & set(target)
            for i in current:
                if i not in intersection:
                    # remove.append(i)
                    self.removePlayer[i] = []
            for key in self.removePlayer:
                remove.append(key)
        return remove

    def predictForDisappearedPlayer(self, disappearedArray):
        predictCoordinate = []
        for elem in disappearedArray:
            metPos = []
            sizeMorePredict = 1
            for pos in self.storeCoord:
                if elem in pos.Players.viewPlayer:
                    metPos.append(pos.Players.mapPlayer[elem])
            if elem in self.removePlayer:
                metPos = np.concatenate((metPos, self.removePlayer[elem]))
                if len(self.removePlayer[elem]) > 0:
                    sizeMorePredict = len(self.removePlayer[elem]) + 1
            # print('metPos len', len(metPos))
            if len(metPos) > 1:
                length = len(metPos)
                angleFlag = int(metPos[length - 1].angle)
                #print('predict viewPlayer', elem)
                #print('predict angleFlag', angleFlag)
                radian = (angleFlag if angleFlag > 0 else 360 + angleFlag) / (2 * np.pi)
                #print('predict radian', radian)
                speedX = np.abs(metPos[length-1].x) - np.abs(metPos[length-2].x)
                speedY = np.abs(metPos[length-1].y) - np.abs(metPos[length-2].y)
                #print('predict speed', speedX, speedY)
               #print('predict start coord', metPos[length-1].x, metPos[length-1].y)
               # print('predict start delta', speedX * np.cos(radian), speedY * np.sin(radian))
                predictX = metPos[length-1].x + speedX * np.cos(radian)
                predictY = metPos[length-1].y + speedY * np.sin(radian)
                #print('predict coord', predictX, predictY)
                predictCoordinate.append({
                    'name': elem,
                    'x': predictX,
                    'y': predictY,
                    'beforeX': metPos[length-1].x,
                    'beforeY': metPos[length-1].y,
                    'angle': metPos[length - 1].angle,
                    'predictTick': sizeMorePredict
                })
        #print('predictCoordinate', predictCoordinate)
        return predictCoordinate

    def savePredictCoords(self, predictCoordinate):
        for pred in predictCoordinate:
            self.removePlayer[pred['name']].append(posPlayer(pred['x'], pred['y'], pred['angle']))
