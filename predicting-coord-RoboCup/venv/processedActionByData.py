import matplotlib.pyplot as plt
#import seaborn as sns
from config import resultColumn, resultStatisticColumn, numPeople
from getCoords import *
#from saveModule import infoForTick, storeAgent
import pandas as pd
from random import randint
from processInputData import readFile
from calculateAction import calculateNearestPlayerToBall, getMapActionForPlayerByTick, haveOtherSide
from enums import ACTION_PLAYER

absolute_Coordinate = pd.read_csv(pathDefault+prefixFiles+'groundtruth.csv', sep=',')

mapPlayerTemplate = getMapActionForPlayerByTick()

#print(absolute_Coordinate)

times = absolute_Coordinate.shape[0]

#print(times)

for index, row in absolute_Coordinate.iterrows():
    mapPlayerTick = dict(mapPlayerTemplate)
    if index < 120:
        print(f'test new tick time {index}______\n')
        mapNowTime = row.to_dict()

        print(f'test playmode: ', mapNowTime[' playmode'])

        if mapNowTime[' playmode'] != ' play_on':
            print(f'test playmode is not play_on, skipping...')
            continue


        nearestPlayers = calculateNearestPlayerToBall(row)

        #print('test dribling: ', len(nearestPlayers) == 1)

        if len(nearestPlayers) == 1:
            mapPlayerTick[nearestPlayers[0]] = ACTION_PLAYER.DRIBLING.value
            
        #print('test haveOtherSide: ', haveOtherSide(nearestPlayers))
        
        if haveOtherSide(nearestPlayers):
            for player in nearestPlayers:
                mapPlayerTick[player] = ACTION_PLAYER.BALL_FIGHT.value
        #mapPlayerTick
        #print(row, index)
        print(nearestPlayers)
        for player in nearestPlayers:
            print(f"{player}: {mapPlayerTick[player]}")

    else:
        break

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