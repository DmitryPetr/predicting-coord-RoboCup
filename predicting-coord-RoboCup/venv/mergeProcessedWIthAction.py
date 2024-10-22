import pandas as pd
import numpy as np
from config import listSide, strategyMergeList, pathDefault

dfNUmber = ['472', '898', '1690']

lenResultDf = 3060
numPeople = 11
gridLen = 6
gridWidth = 4

def calcStats(calcDf):
    uniqueStrategy = calcDf['strategyOpponent'].unique()
    #print(' test read len', len(uniqueStrategy), uniqueStrategy)
    dicStatsUnique = {}
    for item in uniqueStrategy:
      print('strategy', item, len(calcDf[calcDf['strategyOpponent'] == item]))
      dicStatsUnique[item] = len(calcDf[calcDf['strategyOpponent'] == item])
    return dicStatsUnique

#generalDfHidden = pd.read_csv(f'./general_df_process_more_{lenResultDf}_withHead.csv', ',')

#generalDf = pd.read_csv(f'./dataGeneral/general_df_process_more_{lenResultDf}_withHead.csv', ',')
#generalDfWithMerged = pd.read_csv(f'./withInfluence/general_df_process_more_{lenResultDf}_withHead.csv', ',')
generalDfWithMerged = pd.read_csv(f'./general_df_process_more_{lenResultDf}_withHead_withHidden.csv', ',')
print(generalDfWithMerged)
print('Start before length: ', len(generalDfWithMerged))

stats = calcStats(generalDfWithMerged)

for strategy in strategyMergeList:
    for mergeItem in strategy['valueMerge']:
        #print('test testDf: ', mergeItem)
        query = generalDfWithMerged['strategyOpponent'] == mergeItem
        #print('test testDf query: ', query)
        generalDfWithMerged[query] = generalDfWithMerged[query].assign(strategyOpponent=strategy['value'])
        #print('test testDf query: ', generalDfWithMerged[query])
        #resultDf = resultDf.assign(strategyOpponent=strategy['value'])
        #resultDf['strategyOpponent'] = strategy['value']
        #print('test testDf: ', len(resutDf))
        #print('test testDf: ', resutDf['strategyOpponent'])
        #print('test testDf query fast before: ', generalDfWithMerged[query]['strategyOpponent'])
        #generalDfWithMerged[query]['strategyOpponent'] = strategy['value']
        #print('test testDf query fast: ', generalDfWithMerged[query]['strategyOpponent'])


print('Start after: ', generalDfWithMerged)

print('Start after length: ', len(generalDfWithMerged))

stats = calcStats(generalDfWithMerged)

generalDfWithMerged.to_csv(
    f'./general_df_process_more_{len(generalDfWithMerged)}_withHead_withMerged.csv',
    index=False)

# teams = ['Gliders2016', 'HELIOS2016']
#teams = ['Oxsy', 'HfutEngine2017']
#teams = ['Gliders2016', 'HELIOS2016']
teams = ['Oxsy', 'HfutEngine2017']
#teams = ['Oxsy', 'HELIOS2016']

numPeople = 11

for indexTeam, value in teams:
    for index in range(numPeople):
        processedDf = pd.read_csv(f'{pathDefault}{value}_{str(index)}__resultStaticsDf_ok_process.csv', sep=',')
        actionDf = pd.read_csv(f'{teams[0]}-{teams[1]}-action-groundtruth.csv', sep=',')
        nameCurrent = f'{listSide[indexTeam]}{index+1}' 
        processDf['strategyOpponent'] = processedDf['strategyOpponent']

        processDf.to_csv(
            f'./data/output6x4/{item}_{str(index)}__resultStaticsDf_ok_process.csv',
            index=False)    
