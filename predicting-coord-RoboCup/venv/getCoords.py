import pandas as pd
from config import Flags
import numpy as np
from config import Flags, resultColumn, teams, pathDefault

def Remove_Null_or_NAN_Columns(df):
    dff = pd.DataFrame()
    for cl in df.columns:
        notEmptyFlag = True
        for row in df[cl]:
            if row == 'NAN':
                notEmptyFlag = False
            else:
                notEmptyFlag = True
                break
        if (notEmptyFlag):
            dff[cl] = df[cl]
    return dff

def Find_All_Flags(series, team, ind):
    resArr = []
    for index, value in series.items():
        #print('__________________________')
        if index != '# time' and index.find(' dist') != -1 and index.find('f ') != -1 and value != 'NAN':
            #print('find to flag series', index, value)
            resArr.append({
                'column': index,
                'dist': value,
            })
        if index != '# time' and index.find(' angle') != -1 and index.find('f ') != -1 and value != 'NAN':
            resArr[len(resArr)-1]['angle'] = value
    return resArr


def Find_All_Player(series):
    resArr = []
    for index, value in series.items():
        if index != '# time' and index.find(' dist') != -1 and (index.find('p ') != -1 ) and value != 'NAN':
            resArr.append({
                'column': index,
                'dist': value,
            })
        if index != '# time' and index.find(' angle') != -1 and index.find('p ') != -1 and value != 'NAN':
            resArr[len(resArr)-1]['angle'] = value
    return resArr

def getAnswerForThreeFlags(flagOneCoord, flagTwoCoord, flagThreeCoord, distFOne, distFTwo, distFThree):
    coords = []
    distance = []
    distance.append(float(distFOne))
    distance.append(float(distFTwo))
    distance.append(float(distFThree))
    coords.append(flagOneCoord)
    coords.append(flagTwoCoord)
    coords.append(flagThreeCoord)

    answer = None
    if (coords[0]['x'] == coords[1]['x']):
      answer = coordsForSeemX(coords, distance, 0, 1, 2)
      #print('coords[0][x] == coords[1][]', answer)
    elif (coords[0]['x'] == coords[2]['x']):
      answer = coordsForSeemX(coords, distance, 0, 2, 1)
      #print('coords[0][x] == coords[2][]', answer)
    elif (coords[1]['x'] == coords[2]['x']):
      answer = coordsForSeemX(coords, distance, 1, 2, 0)
      #print('coords[1][x] == coords[2][]', answer)
    elif (coords[0]['y'] == coords[1]['y']):
      answer = this.coordsForSeemY(coords, distance, 0, 1, 2)
      #print('coords[0][y] == coords[1][]', answer)
    elif (coords[0]['y'] == coords[2]['y']):
      answer = coordsForSeemY(coords, distance, 0, 2, 1)
     # print('coords[0][y] == coords[2][]', answer)
    elif (coords[1]['y'] == coords[2]['y']):
      answer = coordsForSeemY(coords, distance, 1, 2, 0)
      #print('coords[1][y] == coords[2][]', answer)
    else:
      alpha1 = (coords[0]['y'] - coords[1]['y']) / (coords[1]['x'] - coords[0]['x'])
      beta1 = (coords[1]['y']**2 - coords[0]['y']**2 + coords[1]['x']**2 - coords[0]['x']**2 + distance[0]**2 - distance[1]**2) / (2 * (coords[1]['x'] - coords[0]['x']))
      alpha2 = (coords[0]['y'] - coords[2]['y']) / (coords[2]['x'] - coords[0]['x'])
      beta2 = (coords[2]['y']**2 - coords[0]['y']**2 + coords[2]['x']**2 - coords[0]['x']**2 + distance[0]**2 - distance[2]**2) /  (2 * (coords[2]['x'] - coords[0]['x']))
      y = (beta1 - beta2) / (alpha2 - alpha1)
      x = alpha1 * y + beta1
      #print('ELSE THREE', y, x)
      if (np.abs(x) <= 54 and np.abs(y) <= 32):
        answer = { 'x': x, 'y': y }
      #print('ELSE THREE', answer)
    return answer

def getAnswerForTwoFlags(flagOneCoord, flagTwoCoord, distFOne, distFTwo):
    coords = []
    distance = []
    # p - флаги игрока
    distance.append(float(distFOne))
    distance.append(float(distFTwo))
    # print('getAnswerForTwoFlags', flagOneCoord, flagTwoCoord)
    coords.append(flagOneCoord)
    coords.append(flagTwoCoord)
    # Flags[flagTwo]['x']
    # for elems in p:
    #     if (elems.cmd):
    #         coords.append(Flags[elems.cmd.p.join('')])
    #         distance.append(elems.p[0])
    answer = None
    if (coords[0]['x'] == coords[1]['x']):
        answer = coordsForSeemX(coords, distance, 0, 1, None)
    elif (coords[0]['y'] == coords[1]['y']):
        answer = coordsForSeemY(coords, distance, 0, 1, None)
    else:
        alpha = (coords[0]['y'] - coords[1]['y']) / (coords[1]['x'] - coords[0]['x'])
        beta = (coords[1]['y']**2 - coords[0]['y']**2 + coords[1]['x']**2 - coords[0]['x']**2 + distance[0]**2 - distance[1]**2) / (2 * (coords[1]['x'] - coords[0]['x']))
        a = alpha**2 + 1
        b = -2 * (alpha * (coords[0]['x'] - beta) + coords[0]['y'])
        c = (coords[0]['x'] - beta)**2 + coords[0]['y']**2 - distance[0]**2
        ys = []
        ys.append((-b + np.sqrt(b**2 - 4 * a * c)) / (2 * a))
        ys.append((-b - np.sqrt(b**2 - 4 * a * c)) / (2 * a))
        xs = []
        xs.append(coords[0]['x'] + np.sqrt(distance[0]**2 - (ys[0] - coords[0]['y'])**2))
        xs.append(coords[0]['x'] - np.sqrt(distance[0]**2 - (ys[0] - coords[0]['y'])**2))
        xs.append(coords[0]['x'] + np.sqrt(distance[0]**2 - (ys[1] - coords[0]['y'])**2))
        xs.append(coords[0]['x'] - np.sqrt(distance[0]**2 - (ys[1] - coords[0]['y'])**2))
        answer = checkAnswersForTwoFlags(xs, ys)
    return answer

def coordsForSeemX(coords, distance, q0, q1, q2):
    y = (coords[q1]['y']**2 - coords[q0]['y']**2 + distance[q0]**2 - distance[q1]**2) / (2 * (coords[q1]['y'] - coords[q0]['y']))
    xs = []
    xs.append(coords[q0]['x'] + np.sqrt(np.abs(distance[q0]**2 - (y - coords[q0]['y'])**2)))
    xs.append(coords[q0]['x'] - np.sqrt(np.abs(distance[q0]**2 - (y - coords[q0]['y'])**2)))
    answer = None
    if (q2 != None):
        forX1 = np.abs((xs[0] - coords[q2]['x']) ** 2 + (y - coords[q2]['y']) ** 2 - distance[q2] ** 2)
        forX2 = np.abs((xs[1] - coords[q2]['x']) ** 2 + (y - coords[q2]['y']) ** 2 - distance[q2] ** 2)
        if (forX1 - forX2 > 0):
            answer = {'x': xs[1], 'y': y}
        else:
            answer = {'x': xs[0], 'y': y}
    else:
        if (np.abs(xs[0]) <= 54):
            answer = { 'x': xs[0], 'y': y }
        else:
            answer = { 'x': xs[1], 'y': y }
    return answer

def coordsForSeemY(coords, distance, q0, q1, q2):
    x = (coords[q1]['x']**2 - coords[q0]['x']**2 + distance[q0]**2 - distance[q1]**2) / (2 * (coords[q1]['x'] - coords[q0]['x']))
    ys = []
    ys.append(coords[q0]['y'] + np.sqrt(np.abs(distance[q0]**2 - (x - coords[q0]['x'])**2)))
    ys.append(coords[q0]['y'] - np.sqrt(np.abs(distance[q0]**2 - (x - coords[q0]['x'])**2)))
    answer = None
    if (q2 != None):
        forY1 = np.abs((x - coords[q2]['x']) ** 2 + (ys[0] - coords[q2]['y']) ** 2 - distance[q2] ** 2)
        forY2 = np.abs((x - coords[q2]['x']) ** 2 + (ys[1] - coords[q2]['y']) ** 2 - distance[q2] ** 2)
        if (forY1 - forY2 > 0):
            answer = {'x': x, 'y': ys[1]}
        else:
            answer = {'x': x, 'y': ys[0]}
    else:
        if (np.abs(ys[0]) <= 32):
            answer = { 'x': x, 'y': ys[0] }
        else:
            answer = { 'x': x, 'y': ys[1] }
    return answer


def checkAnswersForTwoFlags(xs, ys):
    answer = None
    for index in range(len(xs)):
        ind = 0 if (index < 2) else 1
        if (np.abs(xs[index]) <= 54 and np.abs(ys[ind]) <= 32):
            answer = { 'x': xs[index], 'y' : ys[ind] }

    return answer

class absoluteCoords:
    def __init__(self, x, y, angle, angleOrientation, nowPlayer):
        self.absoluteX = x
        self.absoluteY = y
        self.angleFlag = angle
        self.angleOrientation = angleOrientation
        self.nowPlayer = nowPlayer


absolute_Coordinate = pd.read_csv(pathDefault+'20170904132709-Gliders2016_0-vs-HELIOS2016_0-groundtruth.csv', ',')

def getAbsolutedCoordinate(team, numPlayer, time, angleOrientation):
    timeRow = absolute_Coordinate[absolute_Coordinate['# time'] == time]
    nowPlayer = ''
    absoluteX = None
    absoluteY = None
    angleFlag = None
    # print('time', time)
    if team == teams[0]:
        if numPlayer == 1:
            # print('time', elems['time'])
            # print('flags', elems['flags'])
            # print(timeRow[' LG1 x'])
            if (len(timeRow[' LG1 x'].values) == 0):
                return None
            absoluteX = timeRow[' LG1 x'].values[0]
            absoluteY = timeRow[' LG1 y'].values[0]
            if (angleOrientation == None):
                angleOrientation = timeRow[' LG1 body'].values[0]
            angleFlag = timeRow[' LG1 body'].values[0]
            nowPlayer = team + ' LG1'
        else:
            if (len(timeRow[' L' + str(numPlayer) + ' x'].values) == 0):
                return None
            absoluteX = timeRow[' L' + str(numPlayer) + ' x'].values[0]
            absoluteY = timeRow[' L' + str(numPlayer) + ' y'].values[0]
            if (angleOrientation == None):
                angleOrientation = timeRow[' L' + str(numPlayer) + ' body'].values[0]
            angleFlag = timeRow[' L' + str(numPlayer) + ' body'].values[0]
            nowPlayer = team + ' L' + str(numPlayer)
    if team == teams[1]:
        if numPlayer == 1:
            if (len(timeRow[' RG1 x'].values) == 0):
                return None
            absoluteX = timeRow[' RG1 x'].values[0]
            absoluteY = timeRow[' RG1 y'].values[0]
            if (angleOrientation == None):
                angleOrientation = timeRow[' RG1 body'].values[0]
            angleFlag = timeRow[' RG1 body'].values[0]
            nowPlayer = team + ' RG1'
        else:
            if (len(timeRow[' R' + str(numPlayer) + ' x'].values) == 0):
                return None
            absoluteX = timeRow[' R' + str(numPlayer) + ' x'].values[0]
            absoluteY = timeRow[' R' + str(numPlayer) + ' y'].values[0]
            if (angleOrientation == None):
                angleOrientation = timeRow[' R' + str(numPlayer) + ' body'].values[0]
            angleFlag = timeRow[' R' + str(numPlayer) + ' body'].values[0]
            nowPlayer = team + ' R' + str(numPlayer)
    #print(angleFlag, team, numPlayer)
    return absoluteCoords(absoluteX, absoluteY, angleFlag, angleOrientation, nowPlayer)
