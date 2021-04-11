import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from config import Flags, resultColumn, resultStatisticColumn, resultPredictColumn, teams, pathDefault
from getCoords import *
from saveModule import infoForTick, storeAgent, posPlayer, otherPlayer
from random import randint
from statistic import calculateExpectationAndVariance

# print(absolute_Coordinate)

# timeRowIndex = [74, 154, 415, 867, 1122]
timeRowIndex = [154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170]
resFlagsTeam = {}
resMovTeam = {}
resProcessTeam = {}
resMovePTeam = {}
numPeople = 1

for item in teams:
    resFlagsTeam[item] = []
    resMovTeam[item] = []
    for index in range(numPeople):
      print(index, pathDefault+'20170904132709-Gliders2016_0-vs-HELIOS2016_0-'+item+'_'+str((index+1))+'-landmarks.csv')
      iter = pd.read_csv(pathDefault+'20170904132709-Gliders2016_0-vs-HELIOS2016_0-'+item+'_'+str((index+1))+'-landmarks.csv', ',')
      print(index, pathDefault + '20170904132709-Gliders2016_0-vs-HELIOS2016_0-' + item + '_' + str((index + 1)) + '-moving.csv')
      iterMov = pd.read_csv(pathDefault + '20170904132709-Gliders2016_0-vs-HELIOS2016_0-' + item + '_' + str((index + 1)) + '-moving.csv', ',')
      # shortDf = iter.iloc[timeRowIndex, :]
      # shortDfMov = iterMov.iloc[timeRowIndex, :]
      # resFlagsTeam[item].append(Remove_Null_or_NAN_Columns(shortDf))
      # resMovTeam[item].append(Remove_Null_or_NAN_Columns(shortDfMov))

      resFlagsTeam[item].append(Remove_Null_or_NAN_Columns(iter))
      resMovTeam[item].append(Remove_Null_or_NAN_Columns(iterMov))

# задаётся по какому игроку нужно получить результат
needTeam = teams[0]
needPlayer = 0
# TODO - доделать пресказание для мяча!

for item in teams:
    if (item != needTeam):
        continue
    #print('team - ', item)
    resProcessTeam[item] = {}
    for ind in range(numPeople):
        if (ind != needPlayer):
            continue
        #print(ind)
        resProcessTeam[item][(ind + 1)] = []
        for index, row in resFlagsTeam[item][ind].iterrows():
            flags = Find_All_Flags(row, item, ind)
            resProcessTeam[item][(ind+1)].append({
                'time': row['# time'],
                'flags': flags
            })

for item in teams:
    if (item != needTeam):
        continue
    #print('team - ', item)
    resMovePTeam[item] = {}
    for ind in range(numPeople):
        if (ind != needPlayer):
            continue
        #print(ind)
        resMovePTeam[item][(ind + 1)] = {}
        for index, row in resMovTeam[item][ind].iterrows():
            player = Find_All_Player(row)
            resMovePTeam[item][(ind+1)][row['# time']] = player
resultDF = pd.DataFrame(columns=resultColumn)
resultStatisticDF = pd.DataFrame(columns=resultStatisticColumn)
#resultPredictDF = pd.DataFrame(columns=resultPredictColumn)
# resultPredictStatisticDF = pd.DataFrame(columns=resultStatisticColumn)
resultPredictStatisticLessTwoDF = pd.DataFrame(columns=resultStatisticColumn)
resultPredictStatisticFromTwoToFiveDF = pd.DataFrame(columns=resultStatisticColumn)
resultPredictStatisticMoreFiveDF = pd.DataFrame(columns=resultStatisticColumn)
resultPredictLessTwoDF = pd.DataFrame(columns=resultPredictColumn)
resultPredictFromTwoToFiveDF = pd.DataFrame(columns=resultPredictColumn)
resultPredictMoreFiveDF = pd.DataFrame(columns=resultPredictColumn)
# resultDF = pd.DataFrame(columns=resultColumn)
# print('resMovePTeam', resMovePTeam)

print('Before main calc')
predictObj = {}
playerList = {}

for item in teams:
    if (item != needTeam):
        continue
    print('team - ', item)
    playerList[item] = {}
    for ind in range(numPeople):
        print('player', ind)
        if (ind != needPlayer):
            continue
        playerList[item][(ind+1)] = storeAgent()
        varianceArray = []
        averageCoordArray = []
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
            # print('time - ', elems['time'])
            if (elems['time'] > 1000):
                break
            # timeRow = absolute_Coordinate[absolute_Coordinate['# time'] == elems['time']]
            absoluteCoord = getAbsolutedCoordinate(item, (ind+1), elems['time'], angleOrientation)
            if (absoluteCoord == None):
                continue

            angleOrientation = absoluteCoord.angleFlag
            angleFlag = absoluteCoord.angleOrientation
            nowPlayer = absoluteCoord.nowPlayer
            playerName = absoluteCoord.nowPlayer
            absoluteX = absoluteCoord.absoluteX
            absoluteY = absoluteCoord.absoluteY

            absoluteCoordArray.append({'x': absoluteX, 'y': absoluteY})
            averageX = 0
            averageY = 0
            if (len(elems['flags']) < 2):
                if (len(averageCoordArray) < 2):
                    continue
                lenArCoord = len(averageCoordArray)
                speedX = np.abs(averageCoordArray[lenArCoord - 1]['x']) - np.abs(averageCoordArray[lenArCoord - 2]['x'])
                speedY = np.abs(averageCoordArray[lenArCoord - 1]['y']) - np.abs(averageCoordArray[lenArCoord - 2]['y'])
                #radian = (angleOrientation if angleOrientation > 0 else 360 + angleOrientation)/(2*np.pi)
                radian = (angleOrientation if angleOrientation > 0 else 360 + angleOrientation) * np.pi / 180
                # print('radian', radian, angleOrientation, angleOrientation if angleOrientation > 0 else 360 + angleOrientation)
                averageX = averageCoordArray[lenArCoord-1]['x'] + speedX * np.cos(radian) # cos
                averageY = averageCoordArray[lenArCoord - 1]['y'] + speedY * np.sin(radian)  # sin
                # print('valueLackFlag', valueLackFlag, averageX, averageY)
                # print('coord', averageCoordArray[lenArCoord-1]['x'], averageCoordArray[lenArCoord - 1]['y'])
                # print('speed', averageSpeedX * np.cos(radian), averageSpeedY * np.sin(radian), averageSpeedX, averageSpeedY, np.cos(radian), np.sin(radian))
                if (valueLackFlag > 3 or (np.abs(averageX) > 54 or np.abs(averageY) > 32)):
                    print('rotate for find flag!')
                    continue
                valueLackFlag += 1
                averageCoordArray.append({'x': averageX, 'y': averageY})
                #print('Flag', len(elems['flags']))
            else:
                angleOrientation = None
                valueLackFlag = 0
                coordsIndAllFl = []
                for indexFirstFlag in range(len(elems['flags'])):
                    for indexSecondFlag in range(indexFirstFlag+1, len(elems['flags'])):
                        firstFlag = elems['flags'][indexFirstFlag]['column']
                        firstFlag = firstFlag[:len(firstFlag) - 4].replace(' ', '')
                        secondFlag = elems['flags'][indexSecondFlag]['column']
                        secondFlag = secondFlag[:len(secondFlag) - 4].replace(' ', '')
                        calcCoords = getAnswerForTwoFlags(Flags[firstFlag], Flags[secondFlag], elems['flags'][indexFirstFlag]['dist'], elems['flags'][indexSecondFlag]['dist'])
                        #print(' angle', elems['flags'][indexFirstFlag]['angle'], elems['flags'][indexSecondFlag]['angle'])
                        if (calcCoords):
                            calcX = calcCoords['x']
                            calcY = calcCoords['y']
                            coordsIndAllFl.append({'x': calcX, 'y': calcY})
                if (len(coordsIndAllFl) > 0):
                    sumX = [0, 0, 0, 0]
                    sumY = [0, 0, 0, 0]
                    for indexEl in range(0, len(coordsIndAllFl)):
                        el_X = coordsIndAllFl[indexEl]['x']
                        el_Y = coordsIndAllFl[indexEl]['y']
                        indexX = 0 if el_X < 0 else 1
                        indexY = 0 if el_X < 0 else 1
                        sumX[indexX] += el_X
                        sumY[indexY] += el_Y
                        sumX[indexX+2] += 1
                        sumY[indexY+2] += 1
                    if (np.abs(sumX[0]) < sumX[1] and sumX[3] != 0):
                        averageX = sumX[1]/sumX[3]
                    if (np.abs(sumX[0]) > sumX[1] and sumX[2] != 0):
                        averageX = sumX[0] / sumX[2]
                    if (np.abs(sumY[0]) < sumY[1] and sumY[3] != 0):
                        averageY = sumY[1] / sumY[3]
                    if (np.abs(sumY[0]) > sumY[1] and sumY[2] != 0):
                        averageY = sumY[0] / sumY[2]

                distanceMax = float(elems['flags'][0]['dist'])
                distanceMix = float(elems['flags'][0]['dist'])
                for indexD in range(1, len(elems['flags'])):
                    elDist = float(elems['flags'][indexD]['dist'])
                    if (distanceMax < elDist):
                        distanceMax = elDist
                    if (distanceMix > elDist):
                        distanceMix = elDist
                variance = ((distanceMax - distanceMix)**2)/12

                if (len(varianceArray) > 0):
                    varianceLast = varianceArray[len(varianceArray)-1]
                    kalman = 0.5
                    if ((varianceLast+variance) != 0):
                        kalman = (varianceLast)/(varianceLast+variance)
                    varianceArray.append(variance)
                    coordLastAbsolute = absoluteCoordArray[len(absoluteCoordArray)-2]
                    coordLast = averageCoordArray[len(averageCoordArray)-1]
                    #radian = (angleFlag if angleFlag > 0 else 360 + angleFlag) / (2 * np.pi)
                    radian = (angleFlag if angleFlag > 0 else 360 + angleFlag) * np.pi / 180
                    speedX = np.abs(absoluteX) - np.abs(coordLastAbsolute['x']) # calculate speed from (dash <num speed> - by Vx)
                    speedY = np.abs(absoluteY) - np.abs(coordLastAbsolute['y']) # calculate speed from (dash <num speed> - by Vy)
                    # print('array', absoluteCoordArray, len(absoluteCoordArray))
                    # print('kalman', kalman)
                    # print("speed", speedX, speedY)
                    # print("coords", averageX, averageY, coordLast['x'], coordLast['y'], coordLast['x'] * speedX, coordLast['y'] * speedY)
                    averageX = averageX * kalman + (1 - kalman) * (coordLast['x'] + speedX * np.cos(radian))
                    averageY = averageY * kalman + (1 - kalman) * (coordLast['y'] + speedY * np.sin(radian))
                    averageCoordArray.append({'x': averageX, 'y': averageY})
                else:
                    varianceArray.append(variance)
                    averageCoordArray.append({'x': averageX, 'y': averageY})

                # calc other obj
                arrPlayer = otherPlayer()
                for player in resMovePTeam[item][(ind + 1)][elems['time']]:
                    coordsNewPlayer = []
                    #print('!!!!!!!!!!!!!!!!!!')
                    #print('player', player)
                    #print('calc', averageX, averageY)
                    #print('______ calc x y ', absoluteX, absoluteY)
                    #print('!!!!!!!!!!!!!!!!!!')
                    for indexFirstFlag in range(len(elems['flags'])):
                        for indexSecondFlag in range(indexFirstFlag + 1, len(elems['flags'])):
                            firstFlag = elems['flags'][indexFirstFlag]['column']
                            firstFlag = firstFlag[:len(firstFlag) - 4].replace(' ', '')
                            secondFlag = elems['flags'][indexSecondFlag]['column']
                            secondFlag = secondFlag[:len(secondFlag) - 4].replace(' ', '')
                            #print('type', type(elems['flags'][indexFirstFlag]['dist']), type(player['dist']))
                            calcAngle = 0
                            angleFl = int(elems['flags'][indexFirstFlag]['angle'])
                            anglePl = int(player['angle'])
                            calcAngle = angleFl - anglePl
                            # if ((angleFl > 0 and anglePl < 0) or (angleFl < 0 and anglePl > 0)):
                            #     calcAngle = np.abs(angleFl) + np.abs(anglePl)
                            # else:
                            #     calcAngle = np.abs(angleFl) - np.abs(anglePl)
                            # print('ang;e flags', angleFl, anglePl, calcAngle, )
                            # print('ang;e flags st1', calcAngle / (2 * np.pi))
                            # print('ang;e flags st1', (angleOrientation if angleOrientation > 0 else 360 + angleOrientation) / (2 * np.pi))
                            # radian = (angleOrientation if angleOrientation > 0 else 360 + angleOrientation) / (2 * np.pi)
                            distanceBetweenFlagAndPlayerFirst = np.sqrt(np.abs(
                                float(elems['flags'][indexFirstFlag]['dist']) ** 2 + float(player['dist']) ** 2 -
                                2 * float(player['dist']) * float(elems['flags'][indexFirstFlag]['dist']) * np.cos(
                                    (np.abs(calcAngle) * np.pi / 180))
                            ))
                            # print('coords before dist 1', elems['flags'][indexFirstFlag]['dist'], float(player['dist'], Flags[firstFlag], Flags[secondFlag],
                            #       player['dist'], distanceBetweenFlagAndPlayerFirst, distanceBetweenFlagAndPlayerSecond)
                            calcAngle = 0
                            angleFl = int(elems['flags'][indexSecondFlag]['angle'])
                            anglePl = int(player['angle'])
                            calcAngle = angleFl - anglePl
                            # if ((angleFl > 0 and anglePl < 0) or (angleFl < 0 and anglePl > 0)):
                            #     calcAngle = np.abs(angleFl) + np.abs(anglePl)
                            # else:
                            #     calcAngle = np.abs(angleFl) - np.abs(anglePl)
                            distanceBetweenFlagAndPlayerSecond = np.sqrt(np.abs(
                                float(elems['flags'][indexSecondFlag]['dist']) ** 2 + float(player['dist']) ** 2 -
                                2 * float(player['dist']) * float(elems['flags'][indexSecondFlag]['dist']) * np.cos(
                                    (np.abs(calcAngle) * np.pi / 180))
                            ))
                            #print(distanceBetweenFlagAndPlayer)
                            # if (distanceBetweenFlagAndPlayer < 10 and distanceBetweenFlagAndPlayer <>> 50):
                            #     continue
                            # print(distanceBetweenFlagAndPlayer)
                            #print('player angle', int(elems['flags'][indexFirstFlag]['angle']), int(player['angle']))
                            #print('distanceBetweenFlagAndPlayer',elems['flags'][indexFirstFlag]['column'], distanceBetweenFlagAndPlayer)
                            # if (distanceBetweenFlagAndPlayer > 30.0):
                            #     continue
                            # print('______ iter 1', {'x': averageX, 'y': averageY})
                            # print('______ iter 2', Flags[secondFlag])
                            #print('coords before', averageX, averageY, Flags[firstFlag], Flags[secondFlag], player['dist'], distanceBetweenFlagAndPlayerFirst, distanceBetweenFlagAndPlayerSecond)
                            calcCoords = getAnswerForThreeFlags({'x': averageX, 'y': averageY}, Flags[firstFlag], Flags[secondFlag], player['dist'], distanceBetweenFlagAndPlayerFirst, distanceBetweenFlagAndPlayerSecond)
                            # print('calcCoords calc', calcCoords)
                            if (calcCoords):
                                calcX = calcCoords['x']
                                calcY = calcCoords['y']
                                coordsNewPlayer.append({'x': calcX, 'y': calcY})

                    newPlayerX = 0.0
                    newPlayerY = 0.0
                    # print('coordsNewPlayer', coordsNewPlayer)
                    if (len(coordsNewPlayer) > 0):
                        sumX = [0, 0, 0, 0]
                        sumY = [0, 0, 0, 0]
                        for indexEl in range(0, len(coordsNewPlayer)):
                            el_X = coordsNewPlayer[indexEl]['x']
                            el_Y = coordsNewPlayer[indexEl]['y']
                            indexX = 0 if el_X < 0 else 1
                            indexY = 0 if el_Y < 0 else 1
                            sumX[indexX] += el_X
                            sumY[indexY] += el_Y
                            sumX[indexX + 2] += 1
                            sumY[indexY + 2] += 1
                        if (np.abs(sumX[0]) < sumX[1] and sumX[3] != 0):
                            newPlayerX = sumX[1] / sumX[3]
                        if (np.abs(sumX[0]) > sumX[1] and sumX[2] != 0):
                            newPlayerX = sumX[0] / sumX[2]
                        if (np.abs(sumY[0]) < sumY[1] and sumY[3] != 0):
                            newPlayerY = -(sumY[1]) / sumY[3]
                        if (np.abs(sumY[0]) > sumY[1] and sumY[2] != 0):
                            newPlayerY = np.abs(sumY[0]) / sumY[2]
                    #print('sum SS ', sumX[0], sumX[1], sumY[0], sumY[1])
                    name = player['column'].replace(' dist', '')
                    team = name[(name.find('"')+1):name.rfind('"')]
                    teamNum = name[(name.rfind('"')+2):len(name)]
                    absCoord = getAbsolutedCoordinate(team, int(teamNum), elems['time'], angleOrientation)
                    # print('calc', newPlayerX, newPlayerY)
                    # print('______ calc x y ', absCoord.absoluteX, absCoord.absoluteY)
                    #print('______ __________________')
                    positionP = posPlayer(newPlayerX, newPlayerY, player['angle'])
                    arrPlayer.addNewViewPlayer(player['column'], positionP)
                    #print('player', elems['time'], player['column'], newPlayerX, newPlayerY, player['angle'], otherPlayer)
            newObj = infoForTick(averageX, averageY, absoluteX, absoluteY, radian, speedX, speedY, arrPlayer)
            playerList[item][(ind+1)].addNewTickInfo(newObj)
            removeList = playerList[item][(ind + 1)].removeList()
            listPredict = playerList[item][(ind + 1)].predictForDisappearedPlayer(removeList)
            playerList[item][(ind + 1)].savePredictCoords(listPredict)
            for nn in playerList[item][(ind + 1)].removePlayer:
                removePlayer = playerList[item][(ind + 1)].removePlayer[nn]
                # print('_____ start people')
                # print(nn, removePlayer)
                # for coorld in removePlayer:
                #     print(coorld.x, coorld.y, coorld.angle)
                # print('_____ end')
            #print('list P', playerList[item][(ind + 1)].removePlayer)
            #if (len(removeList)):
                # print('playerList', removeList)
                # print('predictForDisappearedPlayer', listPredict)
            for predictVal in listPredict:
                # getAbsolutedCoordinate(item, (ind+1), elems['time'], angleOrientation)
                name = predictVal['name'].replace(' dist', '')
                team = name[(name.find('"')+1):name.rfind('"')]
                teamNum = name[(name.rfind('"')+2):len(name)]
                # print(' !!!!!!!!!!')
                # print('______ predictVal name <' + name + '>')
                # print('______ predictVal team <' + team + '>')
                #print('______ predictVal teamNum <' + teamNum+ '>')
                #print('______ predictVal ', predictVal['name'])
                #print('______ predictVal time', elems['time'], elems['time'] + 1)
                absCoord = getAbsolutedCoordinate(team, int(teamNum), elems['time'] + 1, angleOrientation)
                absCoordNow = getAbsolutedCoordinate(team, int(teamNum), elems['time'], angleOrientation)
                #print('______ predictVal absCoord', absCoord)
                if (absCoord != None and absCoordNow!= None):
                    # print('______ predictVal x y ', absCoord.absoluteX, absCoord.absoluteY)
                    # print('______ predictVal x y ', predictVal['x'], predictVal['y'])
                    addObj = {
                        'viewFrom': nowPlayer,
                        'timeNow': elems['time'],
                        'nowX': round(predictVal['beforeX'], 4),
                        'nowY': round(predictVal['beforeY'], 4),
                        'nowAbsoluneX': absCoordNow.absoluteX,
                        'nowAbsoluneY': absCoordNow.absoluteY,
                        'predictX': round(predictVal['x'], 4),
                        'predictY': round(predictVal['y'], 4),
                        'predictAbsoluneX': absCoord.absoluteX,
                        'predictAbsoluneY': absCoord.absoluteY,
                        'nowDiffX': round(np.abs(np.abs(predictVal['beforeX']) - np.abs(absCoordNow.absoluteX)), 4),
                        'nowDiffY': round(np.abs(np.abs(predictVal['beforeY']) - np.abs(absCoordNow.absoluteY)), 4),
                        'predictDiffX': round(np.abs(np.abs(predictVal['x']) - np.abs(absCoord.absoluteX)), 4),
                        'predictDiffY': round(np.abs(np.abs(predictVal['y']) - np.abs(absCoord.absoluteY)), 4),
                        'predictVarianceX': np.sqrt((round(np.abs(np.abs(predictVal['x']) - np.abs(absCoord.absoluteX)), 4) ** 2) / predictVal['predictTick']),
                        'predictVarianceY': np.sqrt((round(np.abs(np.abs(predictVal['y']) - np.abs(absCoord.absoluteY)), 4) **2) / predictVal['predictTick']),
                        'predictTick': predictVal['predictTick'],
                    }
                    if name in predictObj:
                        predictObj[name].append(addObj)
                    else:
                        predictObj[name] = [addObj]
                    #print(' ___________ ')

            # for el in playerList[item][(ind+1)].storeCoord:
            #     print('______ el', el.Players.viewPlayer)

            differenceX = np.abs(np.abs(averageX) - np.abs(absoluteX))
            differenceY = np.abs(np.abs(averageY) - np.abs(absoluteY))
            difference.append({'x': differenceX, 'y': differenceY})

            new_row = {'time': elems['time'], 'player': nowPlayer, 'calc x': round(averageX, 4),
                       'calc y': round(averageY, 4), 'absolute x': absoluteX, 'absolute y': absoluteY,
                       'differenceX': round(differenceX, 4), 'differenceY': round(differenceY, 4)}
            resultDF = resultDF.append(new_row, ignore_index=True)
        #
        startValuePredict = None
        for name in predictObj:
            # differencePredict = []
            differencePredictLessTwo = []
            differencePredictFromTwoToFive = []
            differencePredictMoreFive = []
            for indexPrObj in range(len(predictObj[name])):
            # for elems in predictObj[name]:
                newElems = predictObj[name][indexPrObj]
                print('elems ', newElems, indexPrObj, len(predictObj[name]))
                if ((indexPrObj+1 >= len(predictObj[name]) and newElems['predictTick'] == 1) or
                indexPrObj+1 < len(predictObj[name]) and (newElems['predictTick'] == 1 and predictObj[name][indexPrObj+1]['predictTick'] == 1)):
                    print('in continue')
                    continue
                newElems['player'] = name
                if (newElems['predictTick'] == 1):
                    startValuePredict = newElems
                calcDiffWithStartX = np.abs(np.abs(startValuePredict['predictX']) - np.abs(newElems['predictX']))
                calcDiffWithStartY = np.abs(np.abs(startValuePredict['predictY']) - np.abs(newElems['predictY']))
                newElems['startPredictX'] = startValuePredict['predictX']
                newElems['startPredictY'] = startValuePredict['predictY']
                if (calcDiffWithStartX > 5 or calcDiffWithStartY > 5):
                    resultPredictMoreFiveDF = resultPredictMoreFiveDF.append(newElems, ignore_index=True)
                    differencePredictMoreFive.append({'x': round(newElems['predictDiffX'], 4),
                                          'y': round(newElems['predictDiffY'], 4)})
                elif(calcDiffWithStartX > 2 and calcDiffWithStartX <= 5 or calcDiffWithStartY > 2 and calcDiffWithStartY <= 5):
                    resultPredictFromTwoToFiveDF = resultPredictFromTwoToFiveDF.append(newElems, ignore_index=True)
                    differencePredictFromTwoToFive.append({'x': round(newElems['predictDiffX'], 4),
                                                'y': round(newElems['predictDiffY'], 4)})
                else:
                    resultPredictLessTwoDF = resultPredictLessTwoDF.append(newElems, ignore_index=True)
                    differencePredictLessTwo.append({'x': round(newElems['predictDiffX'], 4),
                                                    'y': round(newElems['predictDiffY'], 4)})
                #print('elems ', newElems)
                # differencePredict.append({'x': round(newElems['predictDiffX'], 4),
                #                           'y': round(newElems['predictDiffY'], 4)})
                #differencePredictLessTwo = []
                #differencePredictFromTwoToFive = []
                #differencePredictMoreFive = []
                # resultPredictDF = resultPredictDF.append(newElems, ignore_index=True)

            # resultPredictStatisticDF = calculateExpectationAndVariance(resultPredictStatisticDF, differencePredict, name)
            print(len(differencePredictLessTwo), len(differencePredictFromTwoToFive), len(differencePredictMoreFive))
            resultPredictStatisticLessTwoDF = calculateExpectationAndVariance(resultPredictStatisticLessTwoDF, differencePredictLessTwo, name)
            resultPredictStatisticFromTwoToFiveDF = calculateExpectationAndVariance(resultPredictStatisticFromTwoToFiveDF, differencePredictFromTwoToFive, name)
            resultPredictStatisticMoreFiveDF = calculateExpectationAndVariance(resultPredictStatisticMoreFiveDF, differencePredictMoreFive, name)

        resultStatisticDF = calculateExpectationAndVariance(resultStatisticDF, difference, playerName)

print(resultDF)
print('_______')
print(resultStatisticDF)

print('\n___   predict   ____\n')

#print(resultPredictDF)
print('_______')
# print(resultPredictStatisticDF)

entropyName = randint(1000, 100000)
resultDF.to_csv(str(entropyName) + 'resultCalc.csv')
resultStatisticDF.to_csv(str(entropyName) + 'resultStatistic.csv')

# resultDF.to_csv(needTeam + '_' + str(needPlayer) + '_resultCalc.csv')
# resultStatisticDF.to_csv(needTeam + '_' + str(needPlayer) + '_resultStatistic.csv')

#resultPredictDF.to_csv(str(entropyName) + 'resultPredict.csv')
# resultPredictStatisticDF.to_csv(str(entropyName) + 'resultPredictStatistic.csv')


#

resultPredictLessTwoDF.to_csv(str(entropyName) + 'resultPredictLessTwo.csv')
resultPredictFromTwoToFiveDF.to_csv(str(entropyName) + 'resultPredictFromTwoToFive.csv')
resultPredictMoreFiveDF.to_csv(str(entropyName) + 'resultPredictMoreFive.csv')

resultPredictStatisticLessTwoDF.to_csv(str(entropyName) + 'resultPredictStatisticLessTwo.csv')
resultPredictStatisticFromTwoToFiveDF.to_csv(str(entropyName) + 'resultPredictStatisticFromTwoToFive.csv')
resultPredictStatisticMoreFiveDF.to_csv(str(entropyName) + 'resultPredictStatisticMoreFive.csv')