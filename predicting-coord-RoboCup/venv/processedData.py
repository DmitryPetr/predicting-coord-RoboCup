import matplotlib.pyplot as plt
import seaborn as sns
from config import resultColumn, resultStatisticColumn, resultPredictColumn, numPeople, resultForPlayerColumn
from getCoords import *
from saveModule import infoForTick, storeAgent
from random import randint
from statistic import createDataForPlt, addDataForStatDist, paramsCreateStats
from processInputData import readFile, createMapViewFlag, createMapViewMove, \
    calcInfoForTick, paramsForCalcPosition, createDataTickWithPredictVal, paramsForDataTickWithPredictVal
from enum import Enum

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
# resultPredictDF = pd.DataFrame(columns=resultPredictColumn)
# resultPredictStatisticDF = pd.DataFrame(columns=resultStatisticColumn)
resultPredictStatisticLessTwoDF = pd.DataFrame(columns=resultStatisticColumn)
resultPredictStatisticFromTwoToFiveDF = pd.DataFrame(columns=resultStatisticColumn)
resultPredictStatisticMoreFiveDF = pd.DataFrame(columns=resultStatisticColumn)
resultPredictLessTwoDF = pd.DataFrame(columns=resultPredictColumn)
resultPredictFromTwoToFiveDF = pd.DataFrame(columns=resultPredictColumn)
resultPredictMoreFiveDF = pd.DataFrame(columns=resultPredictColumn)

resultPredictLessTwoBallDF = pd.DataFrame(columns=resultPredictColumn)
resultPredictFromTwoToFiveBallDF = pd.DataFrame(columns=resultPredictColumn)
resultPredictMoreFiveBallDF = pd.DataFrame(columns=resultPredictColumn)

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

class mainInItParamsForPlayer:
    def __init__(self):
        self.varianceArray = []
        self.absoluteCoordArray = []
        self.difference = []
        self.angleOrientation = None
        self.angleFlag = None
        self.valueLackFlag = 0

class calcCoordForPlayerI:
    def __init__(self, nowPlayer, absoluteX, absoluteY, averageX, averageY, newObj: infoForTick):
        self.nowPlayer = nowPlayer
        self.absoluteX = absoluteX
        self.absoluteY = absoluteY
        self.averageX = averageX
        self.averageY = averageY
        self.newObj = newObj

    def toPrint(self):
       return str(self.nowPlayer) + '\nabsolute: ' + str(self.absoluteX) + ', ' + str(self.absoluteY) + '\naverage: ' + str(self.averageX) + ', ' + str(self.averageY) + '\nangle: ' + str(self.newObj.angle)

class startInfoAboutI:
    def __init__(self,
                 playerList,
                 teams,
                 team,
                 indexPlayer,
                 player):
        self.playerList = playerList # playerList
        self.teams = teams # teams
        self.team = team # item
        self.indexPlayer = indexPlayer # ind
        self.player = player # elems

def calcCoordForPlayer(params: mainInItParamsForPlayer, commonInfo: startInfoAboutI):
    nowPlObj = commonInfo.playerList[item][(ind + 1)]
    # timeRow = absolute_Coordinate[absolute_Coordinate['# time'] == elems['time']]
    absoluteCoord = getAbsolutedCoordinate(item, (ind + 1), elems['time'], params.angleOrientation, False)
    # print('calcCoordForPlayer st 1: ', absoluteCoord)
    if (absoluteCoord == None):
        return None

    params.angleOrientation = absoluteCoord.angleFlag
    params.angleFlag = absoluteCoord.angleOrientation
    nowPlayer = absoluteCoord.nowPlayer
    absoluteX = absoluteCoord.absoluteX
    absoluteY = absoluteCoord.absoluteY

    params.absoluteCoordArray.append({'x': absoluteX, 'y': absoluteY})
    paramsTick = paramsForCalcPosition(commonInfo.player, nowPlObj, params.angleOrientation,
                                       params.valueLackFlag, params.varianceArray, params.angleFlag, absoluteX, absoluteY)
    ansInfoForTick = calcInfoForTick(paramsTick, resMovePTeam, item, ind, params.absoluteCoordArray)
    # print('calcCoordForPlayer st 2: ', ansInfoForTick, params.varianceArray)
    if (ansInfoForTick == None):
        return None
    params.angleOrientation = ansInfoForTick.angleOrientation
    params.valueLackFlag = ansInfoForTick.valueLackFlag
    averageX = ansInfoForTick.averageX
    averageY = ansInfoForTick.averageY
    params.varianceArray = ansInfoForTick.varianceArray

    newObj = infoForTick(averageX, averageY, absoluteX, absoluteY, ansInfoForTick.radian,
                         ansInfoForTick.speedX, ansInfoForTick.speedY, ansInfoForTick.arrPlayer)

    return calcCoordForPlayerI(nowPlayer, absoluteX, absoluteY, averageX, averageY, newObj)

class statisticAndPredictOnCalcCoordI:
    def __init__(self,
                 predictObj,
                 resultDF,
                 averageCoordArrayGlobalGoalie,
                 absoluteCoordArrayGlobalGoalie,
                 averageCoordArrayGlobal,
                 absoluteCoordArrayGlobal):
        self.predictObj = predictObj
        self.resultDF = resultDF
        self.averageCoordArrayGlobalGoalie = averageCoordArrayGlobalGoalie
        self.absoluteCoordArrayGlobalGoalie = absoluteCoordArrayGlobalGoalie
        self.averageCoordArrayGlobal = averageCoordArrayGlobal
        self.absoluteCoordArrayGlobal = absoluteCoordArrayGlobal

def addStatisticAndPredictOnCalcCoord (params: statisticAndPredictOnCalcCoordI,
                                       paramsInit: mainInItParamsForPlayer,
                                       commonInfo: startInfoAboutI,
                                       resultCoord: calcCoordForPlayerI):
    commonInfo.playerList[commonInfo.team][(commonInfo.indexPlayer + 1)].addNewTickInfo(resultCoord.newObj)
    if (commonInfo.team == commonInfo.teams[0] and (commonInfo.indexPlayer + 1) == numberTeamGoalie[0]) or \
            (commonInfo.team == commonInfo.teams[1] and (commonInfo.indexPlayer + 1) == numberTeamGoalie[1]):
        params.averageCoordArrayGlobalGoalie.append({'x': resultCoord.averageX, 'y': resultCoord.averageY})
        params.absoluteCoordArrayGlobalGoalie.append({'x': resultCoord.absoluteX, 'y': resultCoord.absoluteY})
    else:
        params.averageCoordArrayGlobal.append({'x': resultCoord.averageX, 'y': resultCoord.averageY})
        params.absoluteCoordArrayGlobal.append({'x': resultCoord.absoluteX, 'y': resultCoord.absoluteY})
    removeList = commonInfo.playerList[commonInfo.team][(commonInfo.indexPlayer + 1)].removeList()
    listPredict = commonInfo.playerList[commonInfo.team][(commonInfo.indexPlayer + 1)].predictForDisappearedPlayer(removeList)
    commonInfo.playerList[commonInfo.team][(commonInfo.indexPlayer + 1)].savePredictCoords(listPredict)
    for nn in commonInfo.playerList[commonInfo.team][(commonInfo.indexPlayer + 1)].removePlayer:
        removePlayer = commonInfo.playerList[commonInfo.team][(commonInfo.indexPlayer + 1)].removePlayer[nn]

    valueTickWithPredictVal = paramsForDataTickWithPredictVal(listPredict, commonInfo.player, params.predictObj, paramsInit.angleOrientation)
    params.predictObj = createDataTickWithPredictVal(valueTickWithPredictVal, resultCoord.nowPlayer)

    differenceX = np.abs(np.abs(resultCoord.averageX) - np.abs(resultCoord.absoluteX))
    differenceY = np.abs(np.abs(resultCoord.averageY) - np.abs(resultCoord.absoluteY))
    paramsInit.difference.append({'x': differenceX, 'y': differenceY})

    new_row = {'time': elems['time'], 'player': resultCoord.nowPlayer, 'calc x': round(resultCoord.averageX, 4),
               'calc y': round(resultCoord.averageY, 4), 'absolute x': resultCoord.absoluteX, 'absolute y': resultCoord.absoluteY,
               'differenceX': round(differenceX, 4), 'differenceY': round(differenceY, 4)}
    #print('______________________________________ resultDF', new_row)
    params.resultDF = params.resultDF.append(new_row, ignore_index=True)

class sEnum(Enum):
     CurT = 'CurrentTeam'
     OppT = 'OpponntTeam'
     CurPl = 'CurrentPl'
     Ball = 'Ball'

def processCurrentState(
        resultCoord: calcCoordForPlayerI,
        time,
        team,
        indexInteam
    ):
    # print('resultCoord flags: ', flags)
    # print('resultCoord: ', resultCoord.toPrint())
    returnValue = None
    # and (time % 2 == 0)
    if len(resultCoord.newObj.Players.viewPlayer) > 11 and (time % 2 == 0):
        # print('resultCoord otherPl: ', resultCoord.newObj.Players.viewPlayer)

        # if len(resultCoord.newObj.Players.viewPlayer):
        #     sns.scatterplot(data=resultCoord.newObj.Players.viewPlayer, x="calc x", y="calc y")
        #     plt.show()
        resultTestColumn = ['x', 'y', 'angle', 'statusPlayer']
        resultForGridColumn = ['x', 'y']
        resultTestDF = pd.DataFrame(columns=resultTestColumn)
        resultOpponentDF = pd.DataFrame(columns=resultForGridColumn)
        resultTeamDF = pd.DataFrame(columns=resultForGridColumn)
        xBall = None
        yBall = None
        # print('item value nowPlayer :  ', resultCoord.nowPlayer)
        isLeftTeam = teams[0] in resultCoord.nowPlayer
        nowTeam = teams[0] if isLeftTeam else teams[1]
        sideTeam = 'left' if isLeftTeam else 'rigth'
        # print('item value nowPlayer :  ', resultCoord.nowPlayer, nowTeam)
        sizeStatus = 1

        currentPlayerCoord = {
            'x': resultCoord.newObj.x,
            'y': resultCoord.newObj.y,
        }

        resultTestDF = resultTestDF.append({
                **currentPlayerCoord,
                'angle': resultCoord.newObj.angle,
                'statusPlayer': resultCoord.nowPlayer#sEnum.CurPl.value
        }, ignore_index=True)

    #if len(resultCoord.newObj.Players.viewPlayer) > 10:
        for item in resultCoord.newObj.Players.viewPlayer:
            #print('item name: ', item)
            value = resultCoord.newObj.Players.mapPlayer[item]
            statusPlayer = sEnum.Ball.value  if 'b dist' in item else (sEnum.CurT.value if nowTeam in item else sEnum.OppT.value)
            # print('item value: ', item, value.x, value.y, value.angle, statusPlayer)

            currentObj = {
                    'x': value.x,
                    'y': value.y,
            }
            resultTestDF = resultTestDF.append({
                **currentObj,
                'angle': value.angle,
                'statusPlayer': statusPlayer
            }, ignore_index=True)
            if statusPlayer == sEnum.OppT.value:
                #print('in add OppT: ', resultOpponentDF)
                resultOpponentDF = resultOpponentDF.append(currentObj, ignore_index=True)
                #print('in add OppT after: ', resultOpponentDF)
            if statusPlayer == sEnum.CurT.value:
                #print('in add CurT: ')
                resultTeamDF = resultTeamDF.append(currentObj, ignore_index=True)
                #print('in add CurT after: ', resultTeamDF)
            if statusPlayer == sEnum.Ball.value:
                xBall = value.x
                yBall = value.y
    # print('_______ resultTestDF: ', len(resultTestDF))
    #if len(resultTestDF) > 10:
        # print('_______ resultTestDF: ', resultTestDF)

        resultTeamDF = resultTeamDF.sort_values(by=['x'], ascending=False)
        resultTeamDF = resultTeamDF.reset_index(drop=True)

        # print('resultTeamDF: ', resultTeamDF)

        # print('resultTeamDF process: ', getVectorWithObject(resultTeamDF))

        resultOpponentDF = resultOpponentDF.sort_values(by=['x'], ascending=False)
        resultOpponentDF = resultOpponentDF.reset_index(drop=True)

        # print('resultOpponentDF: ', resultOpponentDF)

        # print('resultOpponentDF process: ', getVectorWithObject(resultOpponentDF))

        # График старт
        # color = ['red', 'royalblue', 'orange', 'black']
        #
        # fig = plt.figure(figsize=(13, 6))



        #print('test resultTestDF uqin', len(resultTestDF['statusPlayer'].unique()))

        # График основа
        # scatter = sns.scatterplot(data=resultTestDF, x="x", y="y", hue="statusPlayer", palette=sns.color_palette(color, len(resultTestDF['statusPlayer'].unique())))



        # plt.legend([el.value for el in statusPlayerEnum], bbox_to_anchor=(1.15, 0.5), loc='upper right')
        # plt.legend([0:13], [0:13], bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
        # scatter.legend(fontsize=15, \
        #                bbox_to_anchor=(1.03, 1), \
        #                title="Delivery Type", \
        #                title_fontsize=18, \
        #                shadow=True, \
        #                facecolor='white');
        # plt.legend(
        #            loc='upper left',
        #            borderaxespad=0)

        # График вывод
        # scatter.set_xlim(-54, 54)
        # scatter.set_ylim(-32, 32)
        # plt.legend(bbox_to_anchor=(0.80, 1), loc='upper left', borderaxespad=0)
        # plt.savefig('./img/' + str(time) + '_' + team + '_' + str(indexInteam) + '_' + 'resultStaticsImg.png',
        #             format='png', dpi=600)
        # plt.close(fig)


        #plt.show()

        returnValue = {
          'time': time,
          **currentPlayerCoord,
          'angle': resultCoord.newObj.angle,
          'xBall': xBall,
          'yBall': yBall,
          'opponentVector': getVectorWithObject(resultOpponentDF),
          'teamVector': getVectorWithObject(resultTeamDF),
          'sideTeam': sideTeam,
          'strategyOpponent': None
        }


        # 'x', 'y', 'angle', 'xBall', 'yBall', 'opponentVector', 'teamVector', 'strategyOpponent'

    # print('returnValue: ', returnValue)
    return returnValue


if __name__ == '__main__':
    #print('test resMoveBTeam: ', resMoveBTeam)
    for item in teams:
        print('team - ', item)
        playerList[item] = {}
        for ind in range(numPeople):
            print('player', ind)
            playerList[item][(ind + 1)] = storeAgent()
            paramsPlayerStart = mainInItParamsForPlayer()
            resultForPlayerDF = pd.DataFrame(columns=resultForPlayerColumn)
            for elems in resProcessTeam[item][(ind + 1)]:
                print('time - ', elems['time'], item, ind)
                # if (elems['time'] < 900):
                #     continue
                # if (teams[0] == item):
                #     break
                # if (elems['time'] < 1995):
                #     continue
                # if (item == teams[0] and ind < 2):
                #     break
                if (elems['time'] > 3000):
                    break
                commonInfo = startInfoAboutI(playerList, teams, item, ind, elems)
                resultCoord = calcCoordForPlayer(paramsPlayerStart, commonInfo)
                if resultCoord == None:
                    continue
                paramsForAddStatistics = statisticAndPredictOnCalcCoordI(
                    predictObj,
                    resultDF,
                    averageCoordArrayGlobalGoalie,
                    absoluteCoordArrayGlobalGoalie,
                    averageCoordArrayGlobal,
                    absoluteCoordArrayGlobal)
                # print('test elems[time]: ', elems)
                addStatisticAndPredictOnCalcCoord(paramsForAddStatistics, paramsPlayerStart, commonInfo, resultCoord)
                #resultDF = pd.concat([resultDF, paramsForAddStatistics.resultDF])
                #print('______________________________________ resultDF', paramsForAddStatistics.resultDF)
                #print('test resMoveBTeam[item]: ', len(resMoveBTeam[item]))
                # print('test elems[time]: ',type(elems['time']), resMoveBTeam[item][str(elems['time'])])
                resultProcessCurState = processCurrentState(
                    resultCoord,
                    # resMoveBTeam[item][(ind + 1)][elems['time']],
                    # elems['flags'],
                    elems['time'],
                    item,
                    ind
                )
                if resultProcessCurState != None:
                    resultForPlayerDF = resultForPlayerDF.append(resultProcessCurState, ignore_index=True)
                    print('test resultProcessCurState: ', resultProcessCurState)
                # print('resultCoord: ', resultCoord.toPrint())
            if (item == teams[0] and ind < 2):
                continue
            resultForPlayerDF.to_csv(f'./dataCSV/{item}_{str(ind)}_resultStaticsDf{str(gridLen)}_{str(gridWidth)}.csv', index=False)

#print(resultDF)

# sns.scatterplot(data = resultDF, x = "calc x", y = "calc y")
# plt.show()
# print('predictObj: ', predictObj)
