import pandas as pd
import numpy as np

# data = pd.read_csv('32081resultPredictFromTwoToFive.csv', ',')
# data = pd.read_csv('32081resultPredictMoreFive.csv', ',')
# data = pd.read_csv('32081resultPredictLessTwo.csv', ',')


#data = pd.read_csv('43007resultPredictFromTwoToFive.csv', ',')
# data = pd.read_csv('43007resultPredictMoreFive.csv', ',')
data = pd.read_csv('43007resultPredictLessTwo.csv', ',')

calcData = []

for index, row in data.iterrows():
    newObj = {}
    for index, value in row.items():
        if index.find('nowDiffX') != -1:
            newObj['nowDiffX'] = value

        if index.find('nowDiffY') != -1:
            newObj['nowDiffY'] = value

        if index.find('predictDiffX') != -1:
            newObj['predictDiffX'] = value

        if index.find('predictDiffY') != -1:
            newObj['predictDiffY'] = value

    newObj['nowDiff'] = np.sqrt((newObj['nowDiffX'] - newObj['nowDiffY']) ** 2)
    newObj['predictDiff'] = np.sqrt((newObj['predictDiffX'] - newObj['predictDiffY']) ** 2)

    calcData.append(newObj)

midNowDiff = 0
midPredictDiff = 0
minNowDiff = None
minPredictDiff = None

for item in calcData:
    if minNowDiff == None or minNowDiff > item['nowDiff']:
        minNowDiff = item['nowDiff']
    if minPredictDiff == None or minPredictDiff > item['predictDiff']:
        minPredictDiff = item['predictDiff']
    midNowDiff += item['nowDiff']
    midPredictDiff += item['predictDiff']

print('minNowDiff', minNowDiff)
print('minPredictDiff', minPredictDiff)

print('midNowDiff', midNowDiff/len(calcData))
print('midPredictDiff', midPredictDiff/len(calcData))