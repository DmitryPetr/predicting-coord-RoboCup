import matplotlib.pyplot as plt
import seaborn as sns
from config import resultColumn, resultStatisticColumn, resultPredictColumn, numPeople, resultForPlayerColumn
from getCoords import *
from saveModule import infoForTick, storeAgent
from random import randint
from statistic import createDataForPlt, addDataForStatDist, paramsCreateStats
from processInputData import readFile, createMapViewFlag, createMapViewMove, \
    calcInfoForTick, paramsForCalcPosition, createDataTickWithPredictVal, paramsForDataTickWithPredictVal, \
    separateObjectField, separateObjectFieldInput
from enum import Enum

from calculateAction import isInsideRadius, CoordinateObject, nearGoalWithCoordinate

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
# resultPredictStatisticLessTwoDF = pd.DataFrame(columns=resultStatisticColumn)
# resultPredictStatisticFromTwoToFiveDF = pd.DataFrame(columns=resultStatisticColumn)
# resultPredictStatisticMoreFiveDF = pd.DataFrame(columns=resultStatisticColumn)
# resultPredictLessTwoDF = pd.DataFrame(columns=resultPredictColumn)
# resultPredictFromTwoToFiveDF = pd.DataFrame(columns=resultPredictColumn)
# resultPredictMoreFiveDF = pd.DataFrame(columns=resultPredictColumn)

# resultPredictLessTwoBallDF = pd.DataFrame(columns=resultPredictColumn)
# resultPredictFromTwoToFiveBallDF = pd.DataFrame(columns=resultPredictColumn)
# resultPredictMoreFiveBallDF = pd.DataFrame(columns=resultPredictColumn)

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

class returnLenOfObject:
    def __init__(self, lenOfNearTeam, lenOfNearOp, lenMidOfTeam, lenMidOfOp, nearGoal):
        self.lenOfNearTeam = lenOfNearTeam
        self.lenOfNearOp = lenOfNearOp
        self.lenMidOfTeam = lenMidOfTeam
        self.lenMidOfOp = lenMidOfOp
        self.nearGoal = nearGoal

    def toStr(self):
        return f"\nlenOfNearTeam: {self.lenOfNearTeam},\n lenOfNearOp: {self.lenOfNearOp},\n lenMidOfTeam: {self.lenMidOfTeam},\n lenMidOfOp: {self.lenMidOfOp}, \nnearGoal: {self.nearGoal}"

def calculatePlayerNearBall(nowPlayer: str, nowArrayPlayer: otherPlayer) -> returnLenOfObject:
    lenOfNearTeam = 0
    lenOfNearOp = 0
    lenMidOfTeam = 0
    lenMidOfOp = 0

    ballCoords: posPlayer = nowArrayPlayer.mapPlayer['b dist']

    nowSide = listSide[0] if teams[0] in nowPlayer else listSide[1]

    coordBallObject = CoordinateObject(ballCoords.x, ballCoords.y)

    for player in nowArrayPlayer.viewPlayer:
        if player == 'b dist':
            continue

        playerSide = listSide[0] if teams[0] in player else listSide[1]
        playerCoords: posPlayer = nowArrayPlayer.mapPlayer[player]

        inNearRadius = isInsideRadius(coordBallObject, CoordinateObject(playerCoords.x, playerCoords.y), nearestRadius)

        if inNearRadius: 
            if nowSide == playerSide:
                lenOfNearTeam += 1
            else: 
                lenOfNearOp += 1
            continue

        inMiddleRadius = isInsideRadius(coordBallObject, CoordinateObject(playerCoords.x, playerCoords.y), middleRadius)

        if inMiddleRadius: 
            if nowSide == playerSide:
                lenMidOfTeam += 1
            else: 
                lenMidOfOp += 1
            continue

    nearGoal = nearGoalWithCoordinate(coordBallObject)

    return returnLenOfObject(lenOfNearTeam, lenOfNearOp, lenMidOfTeam, lenMidOfOp, nearGoal)



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
    

    nowArrayPlayer = ansInfoForTick.arrPlayer
    containBall = 'b dist' in nowArrayPlayer.viewPlayer
    lenViewPlayer = len(nowArrayPlayer.viewPlayer)

    print("test viewPlayer tick info", nowArrayPlayer.viewPlayer)

    print(f"after viewPlayer tick info field: {containBall} {lenViewPlayer}")

    if ( not containBall):
        print("test not a ball")
        return None

    print("after calc tick info after", nowArrayPlayer.mapPlayer)

    if (containBall and lenViewPlayer < 2):
        print("small people number near ball")
        return None

                

    print("after calc tick info after two check", nowArrayPlayer.mapPlayer)

    returnCalcLen: returnLenOfObject = calculatePlayerNearBall(nowPlayer, nowArrayPlayer)

    print("after calc tick info after returnCalLen", returnCalcLen.toStr())

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
    #params.resultDF = params.resultDF.append(new_row, ignore_index=True)

class sEnum(Enum):
     CurT = 'CurrentTeam'
     CurPrT = 'CurrentPredictTeam'
     OppT = 'OpponntTeam'
     OppPrT = 'OpponntPredictTeam'
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
        infoPlayer = commonInfo.playerList[commonInfo.team][(commonInfo.indexPlayer + 1)]
        removePlayerArray = infoPlayer.removePlayer

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
        # Видимые игроки
        for item in resultCoord.newObj.Players.viewPlayer:
            #print('item name: ', item)
            value = resultCoord.newObj.Players.mapPlayer[item]
            outputSeparete = separateObjectField(
                separateObjectFieldInput(
                    item,
                    value,
                    nowTeam,
                    sEnum,
                    resultTestDF,
                    resultOpponentDF,
                    resultTeamDF,
                    xBall, yBall, False))
            resultTestDF = outputSeparete.resultTestDF
            resultOpponentDF = outputSeparete.resultOpponentDF
            resultTeamDF = outputSeparete.resultTeamDF
            xBall = outputSeparete.xBall
            yBall = outputSeparete.yBall

        color = ['red', 'royalblue', 'orange', 'black', 'green', 'yellow']
        #fig = plt.figure(figsize=(13, 6))

        # scatter = sns.scatterplot(data=resultTestDF, x="x", y="y", hue="statusPlayer",
        #                           palette=sns.color_palette(color, len(resultTestDF['statusPlayer'].unique())))
        #
        # scatter.set_xlim(-54, 54)
        # scatter.set_ylim(-32, 32)
        # scatter.set_xlabel("x", fontsize=20)
        # scatter.set_ylabel("y",fontsize=20)
        # -----------------


        #scatter.set_title(fontsize=20)
        #scatter.set_context("paper", rc={"axes.labelsize": 36})
        #figtest, axtest = plt.subplots()
        #axtest.plot(fontsize=20)


        #plt.legend(bbox_to_anchor=(0.80, 1), loc='upper left', borderaxespad=0, fontsize=18)
        # plt.savefig('./img/' + str(time) + '_' + team + '_' + str(indexInteam) + '_' + 'resultStaticsImg.png',
        #             format='png', dpi=600)

        #plt.show()

        # С недавно исчезнувшими игроками
        # for rmPlayer in removePlayerArray:
        #     valuesPlayer = removePlayerArray[rmPlayer]
        #
        #     if len(valuesPlayer) > 0:
        #         curPl = removePlayerArray[rmPlayer]
        #         print('test rmPlayer: ', rmPlayer)
        #         # print('test rmPlayer value: ', curPl)
        #         value = valuesPlayer[len(valuesPlayer)-1]
        #         if len(curPl) > 1:
        #             print('________________ test len(curPl) > 1: ', len(curPl))
        #             calcDiffWithStartX = np.abs(np.abs(curPl[0].x) - np.abs(curPl[len(curPl) - 1].x))
        #             print('________________ test calcDiffWithStartX: ', calcDiffWithStartX)
        #             calcDiffWithStartY = np.abs(np.abs(curPl[0].y) - np.abs(curPl[len(curPl) - 1].y))
        #             print('________________ over test calcDiffWithStartX: ', calcDiffWithStartY)
        #             if (calcDiffWithStartX > 5 or calcDiffWithStartY > 5):
        #                 print('________________ over five dist')
        #                 continue
        #
        #         outputSeparete = separateObjectField(
        #             separateObjectFieldInput(item,
        #                                      value,
        #                                      nowTeam,
        #                                      sEnum,
        #                                      resultTestDF,
        #                                      resultOpponentDF,
        #                                      resultTeamDF, xBall, yBall, True))
        #         resultTestDF = outputSeparete.resultTestDF
        #         resultOpponentDF = outputSeparete.resultOpponentDF
        #         resultTeamDF = outputSeparete.resultTeamDF
        #         xBall = outputSeparete.xBall
        #         yBall = outputSeparete.yBall

        resultTeamDF = resultTeamDF.sort_values(by=['x'], ascending=False)
        resultTeamDF = resultTeamDF.reset_index(drop=True)

        resultOpponentDF = resultOpponentDF.sort_values(by=['x'], ascending=False)
        resultOpponentDF = resultOpponentDF.reset_index(drop=True)

        # _____________________- График старт
        #color = ['red', 'royalblue', 'orange', 'black', 'blue', 'yellow']
        #
        # fig = plt.figure(figsize=(13, 6))



        #print('test resultTestDF uqin', len(resultTestDF['statusPlayer'].unique()))

        # График основа
        # scatter = sns.scatterplot(data=resultTestDF, x="x", y="y", hue="statusPlayer", palette=sns.color_palette(color, len(resultTestDF['statusPlayer'].unique())))

        # График вывод
        #scatter.set(fontsize=20)
        # scatter.set_xlim(-54, 54)
        # scatter.set_ylim(-32, 32)
        # scatter.set_xlabel("x", fontsize=20)
        # scatter.set_ylabel("y",fontsize=20)
        # -----------------


        # plt.legend(bbox_to_anchor=(0.80, 1), loc='upper left', borderaxespad=0, fontsize=18)
        # plt.savefig('./img/' + str(time) + '_' + team + '_' + str(indexInteam) + '_' + 'resultStaticsImg_withHidden.png',
        #             format='png', dpi=600)
        #
        # #plt.show()
        # plt.close(fig)

        returnValue = {
          'time': time,
          **currentPlayerCoord,
          'angle': resultCoord.newObj.angle,
          'xBall': xBall,
          'yBall': yBall,

          #'opponentVector': getVectorWithObject(resultOpponentDF),
          'opponentInfluenceVector': getInfluenceVectorWithObject(getVectorWithObject(resultOpponentDF), getVectorWithObject(resultTeamDF)),
          #'teamVector': getVectorWithObject(resultTeamDF),
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
                #print('paramsForAddStatistics: ', paramsForAddStatistics.predictObj)
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
                    #print('test resultProcessCurState: ', resultProcessCurState)
                # print('resultCoord: ', resultCoord.toPrint())
            # if (item == teams[0] and ind < 2):
            #     continue
            #resultForPlayerDF.to_csv(f'./dataCSV/{item}_{str(ind)}_resultStaticsDf{str(gridLen)}_{str(gridWidth)}.csv', index=False)
            resultForPlayerDF.to_csv(f'./dataCSV/{item}_{str(ind)}_resultStaticsDf{str(gridLen)}_{str(gridWidth)}_withHidden.csv', index=False)

#print(resultDF)

# sns.scatterplot(data = resultDF, x = "calc x", y = "calc y")
# plt.show()
# print('predictObj: ', predictObj)
