import unittest
from saveModule import *
from processInputData import *

class TestStringMethods(unittest.TestCase):

  def testForGetAnswerForTwoFlags(self):
      distFlagOne = 20.1
      distFlagTwo = 7.52
      # x1 != x2 && y1 != y2
      coordinate = getAnswerForTwoFlags(Flags['ftl50'], Flags['flt20'], distFlagOne, distFlagTwo)
      self.assertEqual(round(coordinate['x'], 4), -50.0609)
      self.assertEqual(round(coordinate['y'], 4), 18.9001)
      distFlagOne = 12.6
      distFlagTwo = 11.63
      # x1 == x2 && y1 != y2
      coordinate = getAnswerForTwoFlags(Flags['flt'], Flags['flb'], distFlagOne, distFlagTwo)
      self.assertEqual(round(coordinate['x'], 4), -20.7349)
      self.assertEqual(round(coordinate['y'], 4), -0.1728)
      distFlagOne = 31.43
      distFlagTwo = 5.67
      # x1 != x2 && y1 == y2
      coordinate = getAnswerForTwoFlags(Flags['flb'], Flags['fcb'], distFlagOne, distFlagTwo)
      self.assertEqual(round(coordinate['x'], 4), -17.1481)
      self.assertEqual(round(coordinate['y'], 4), -17.8164)

  def testForGetAnswerForThreeFlags(self):
      distFlagOne = 19.2
      distFlagTwo = 7.71
      distFlagThree = 11.53
      # x1 = x2 && x1 != x3 && x2 != x3 && y1 != y2 && y1 != y3 && y2 != y3
      coordinate = getAnswerForThreeFlags(Flags['ftl50'], Flags['flt20'], Flags['fbl30'], distFlagOne, distFlagTwo, distFlagThree)
      self.assertEqual(round(coordinate['x'], 4), -13.2065)
      self.assertEqual(round(coordinate['y'], 4), 5.3592)
      distFlagOne = 12.6
      distFlagTwo = 11.63
      distFlagThree = 7.8
      # x1 == x2 && x1 != x3 && x2 != x3 && y1 != y2 && y1 != y3 && y2 != y3
      coordinate = getAnswerForThreeFlags(Flags['flt'], Flags['flb'], Flags['fprt'], distFlagOne, distFlagTwo,
                                          distFlagThree)
      self.assertEqual(round(coordinate['x'], 4), -20.7349)
      self.assertEqual(round(coordinate['y'], 4), -0.1728)
      # x1 != x2 && x1 != x3 && x2 == x3 && y1 != y2 && y1 != y3 && y2 != y3
      coordinate = getAnswerForThreeFlags(Flags['fprt'], Flags['flb'], Flags['flt'], distFlagOne, distFlagTwo,
                                          distFlagThree)
      self.assertEqual(round(coordinate['x'], 4), -19.9692)
      self.assertEqual(round(coordinate['y'], 4), 0.5472)
      # x1 != x2 && x1 == x3 && x2 != x3 && y1 != y2 && y1 != y3 && y2 != y3
      coordinate = getAnswerForThreeFlags(Flags['flb'], Flags['fprt'], Flags['flt'], distFlagOne, distFlagTwo,
                                          distFlagThree)
      self.assertEqual(round(coordinate['x'], 4), -20.147)
      self.assertEqual(round(coordinate['y'], 4), 0.72)
      distFlagOne = 6.61
      distFlagTwo = 23.2
      distFlagThree = 14.87
      # x1 != x2 && x1 != x3 && x2 != x3 && y1 == y2 && y1 != y3 && y2 != y3
      coordinate = getAnswerForThreeFlags(Flags['flb'], Flags['fcb'], Flags['fprc'], distFlagOne, distFlagTwo,
                                          distFlagThree)
      self.assertEqual(round(coordinate['x'], 4), -30.96)
      self.assertEqual(round(coordinate['y'], 4), -13.4993)
      # x1 != x2 && x1 != x3 && x2 != x3 && y1 != y2 && y1 == y3 && y2 != y3
      coordinate = getAnswerForThreeFlags(Flags['flb'], Flags['fprc'], Flags['fcb'], distFlagOne, distFlagTwo,
                                          distFlagThree)
      self.assertEqual(round(coordinate['x'], 4), -27.9398)
      self.assertEqual(round(coordinate['y'], 4), -10.346)
      # x1 != x2 && x1 != x3 && x2 != x3 && y1 != y2 && y1 != y3 && y2 == y3
      coordinate = getAnswerForThreeFlags(Flags['fprc'], Flags['flb'], Flags['fcb'], distFlagOne, distFlagTwo,
                                          distFlagThree)
      self.assertEqual(round(coordinate['x'], 4), -23.2298)
      self.assertEqual(round(coordinate['y'], 4), -16.1533)

  def testOtherPlayer(self):
      objPlayer = otherPlayer()
      self.assertEqual(len(objPlayer.viewPlayer), 0)
      self.assertEqual(objPlayer.mapPlayer, {})
      newPos = posPlayer(11.2, 5.3, 10)
      objPlayer.addNewViewPlayer('testUnit', newPos)
      self.assertEqual(objPlayer.viewPlayer, ['testUnit'])
      self.assertEqual(objPlayer.mapPlayer, {'testUnit': newPos})

  def testStoreAgentAddNewTickInfo(self):
      store = storeAgent()
      self.assertEqual(len(store.storeCoord), 0)
      self.assertEqual(store.removePlayer, {})
      objPlayer = otherPlayer()
      newPos = posPlayer(11.2, 5.3, 10)
      objPlayer.addNewViewPlayer('testUnitOne', newPos)
      newPos = posPlayer(5.2, 7.5, 15)
      objPlayer.addNewViewPlayer('testUnitTwo', newPos)
      newPos = infoForTick(11.2, 5.3, 11.51, 5.31, 3.21, 0.431, 0.721, objPlayer)
      store.addNewTickInfo(newPos)
      self.assertEqual(len(store.storeCoord), 1)
      self.assertEqual(store.removePlayer, {})

  def testStoreRemoveList(self):
      store = storeAgent()
      objPlayer = otherPlayer()
      newPos = posPlayer(11.2, 5.3, 10)
      objPlayer.addNewViewPlayer('testUnitOne', newPos)
      newPos = posPlayer(5.2, 7.5, 15)
      objPlayer.addNewViewPlayer('testUnitTwo', newPos)
      newPos = infoForTick(11.2, 5.3, 11.51, 5.31, 3.21, 0.431, 0.721, objPlayer)
      store.addNewTickInfo(newPos)
      newPos = infoForTick(11.2, 5.3, 11.51, 5.31, 3.21, 0.431, 0.721, objPlayer)
      store.addNewTickInfo(newPos)
      newPos = infoForTick(11.2, 5.3, 11.51, 5.31, 3.21, 0.431, 0.721, objPlayer)
      store.addNewTickInfo(newPos)
      objPlayer = otherPlayer()
      newPos = posPlayer(11.1, 5.9, 8)
      objPlayer.addNewViewPlayer('testUnitOne', newPos)
      newPos = infoForTick(11.2, 5.3, 11.51, 5.31, 3.21, 0.431, 0.721, objPlayer)
      store.addNewTickInfo(newPos)
      removeList = store.removeList()
      self.assertEqual(removeList, ['testUnitTwo'])

  def testPredictValue(self):
      store = storeAgent()
      self.assertEqual(len(store.storeCoord), 0)
      self.assertEqual(store.removePlayer, {})
      objPlayer = otherPlayer()
      newPos = posPlayer(11.2, 5.3, 10)
      objPlayer.addNewViewPlayer('testUnitOne', newPos)
      newPos = posPlayer(5.2, 7.5, 15)
      objPlayer.addNewViewPlayer('testUnitTwo', newPos)
      newPos = infoForTick(11.2, 5.3, 11.51, 5.31, 3.21, 0.431, 0.721, objPlayer)
      store.addNewTickInfo(newPos)
      self.assertEqual(len(store.storeCoord), 1)
      self.assertEqual(store.removePlayer, {})
      newPos = infoForTick(11.2, 5.3, 11.51, 5.31, 3.21, 0.431, 0.721, objPlayer)
      store.addNewTickInfo(newPos)
      newPos = infoForTick(11.2, 5.3, 11.51, 5.31, 3.21, 0.431, 0.721, objPlayer)
      store.addNewTickInfo(newPos)
      objPlayer = otherPlayer()
      newPos = posPlayer(11.1, 5.9, 8)
      objPlayer.addNewViewPlayer('testUnitOne', newPos)
      newPos = infoForTick(11.2, 5.3, 11.51, 5.31, 3.21, 0.431, 0.721, objPlayer)
      store.addNewTickInfo(newPos)
      removeList = store.removeList()
      self.assertEqual(removeList, ['testUnitTwo'])
      listPredict = store.predictForDisappearedPlayer(removeList)
      needArray = [{'name': 'testUnitTwo', 'x': 5.2, 'y': 7.5, 'beforeX': 5.2, 'beforeY': 7.5, 'angle': 15, 'predictTick': 1}]
      self.assertEqual(listPredict, needArray)

  def testCalcInfoForTick(self):
      elems = {'time': 125, 'flags': [{'column': 'f b 0 dist', 'dist': '58.6', 'angle': '67'}, {'column': 'f b l 10 dist', 'dist': '51.9', 'angle': '76'}, {'column': 'f b l 20 dist', 'dist': '47', 'angle': '86'}, {'column': 'f b r 10 dist', 'dist': '65.4', 'angle': '61'}, {'column': 'f b r 20 dist', 'dist': '73.7', 'angle': '56'}, {'column': 'f b r 30 dist', 'dist': '81.5', 'angle': '52'}, {'column': 'f b r 40 dist', 'dist': '90', 'angle': '48'}, {'column': 'f b r 50 dist', 'dist': '99.5', 'angle': '46'}, {'column': 'f c dist', 'dist': '39.6', 'angle': '26'}, {'column': 'f c b dist', 'dist': '54.6', 'angle': '64'}, {'column': 'f c t dist', 'dist': '49.4', 'angle': '-17'}, {'column': 'f g r b dist', 'dist': '92.8', 'angle': '27'}, {'column': 'f g r t dist', 'dist': '91.8', 'angle': '18'}, {'column': 'f p l c dist', 'dist': '5.3', 'angle': '68'}, {'column': 'f p l t dist', 'dist': '16.6', 'angle': '-58'}, {'column': 'f p r b dist', 'dist': '79', 'angle': '38'}, {'column': 'f p r c dist', 'dist': '75.9', 'angle': '23'}, {'column': 'f p r t dist', 'dist': '77.5', 'angle': '8'}, {'column': 'f r 0 dist', 'dist': '97.5', 'angle': '22'}, {'column': 'f r b dist', 'dist': '99.5', 'angle': '42'}, {'column': 'f r b 10 dist', 'dist': '98.5', 'angle': '28'}, {'column': 'f r b 20 dist', 'dist': '99.5', 'angle': '34'}, {'column': 'f r b 30 dist', 'dist': '102', 'angle': '39'}, {'column': 'f r t dist', 'dist': '96.5', 'angle': '2'}, {'column': 'f r t 10 dist', 'dist': '97.5', 'angle': '16'}, {'column': 'f r t 20 dist', 'dist': '98.5', 'angle': '11'}, {'column': 'f r t 30 dist', 'dist': '100', 'angle': '5'}, {'column': 'f t 0 dist', 'dist': '53', 'angle': '-22'}, {'column': 'f t l 10 dist', 'dist': '45.6', 'angle': '-30'}, {'column': 'f t l 20 dist', 'dist': '40', 'angle': '-41'}, {'column': 'f t l 30 dist', 'dist': '36.2', 'angle': '-55'}, {'column': 'f t l 40 dist', 'dist': '35.2', 'angle': '-71'}, {'column': 'f t l 50 dist', 'dist': '36.6', 'angle': '-87'}, {'column': 'f t r 10 dist', 'dist': '60.9', 'angle': '-15'}, {'column': 'f t r 20 dist', 'dist': '69.4', 'angle': '-10'}, {'column': 'f t r 30 dist', 'dist': '77.5', 'angle': '-7'}, {'column': 'f t r 40 dist', 'dist': '86.5', 'angle': '-4'}, {'column': 'f t r 50 dist', 'dist': '96.5', 'angle': '-1'}]}
      nowPlObj = storeAgent()
      newPos = infoForTick(-39.6734, 2.4588, -39.5189, -3.9545, 4.196, 0.0, 0.0, otherPlayer())
      nowPlObj.addNewTickInfo(newPos)
      newPos = infoForTick(-39.6694, 2.5194, -39.5189, -3.9545, 4.3633, 0.0, 0.0, otherPlayer())
      nowPlObj.addNewTickInfo(newPos)
      newPos = infoForTick(-39.6674, 2.54971, -39.5189, -3.9545, 4.3633, 0.0, 0.0, otherPlayer())
      nowPlObj.addNewTickInfo(newPos)
      newPos = infoForTick(-39.6663, 2.5649, -39.5189, -3.9545, 4.3633, 0.0, 0.0, otherPlayer())
      nowPlObj.addNewTickInfo(newPos)
      newPos = infoForTick(-39.6658, 2.5724, -39.5189, -3.9545, 4.3633, 0.0, 0.0, otherPlayer())
      nowPlObj.addNewTickInfo(newPos)
      varianceArray = [ 779.2408333333334, 779.2408333333334]
      paramsTick = paramsForCalcPosition(elems, nowPlObj, -110.003,
                                         0, varianceArray, -110.003, -39.5189, -3.9545)
      team = 'HELIOS2017'
      indexPlayer = 0
      resMovePTeam = {
          team: {
              (indexPlayer+1): {
                  125: [{'column': 'b dist', 'dist': '60.3', 'angle': '19'},
       {'column': 'p "HELIOS2017" 3 dist', 'dist': '27.1', 'angle': '1'},
       {'column': 'p "HELIOS2017" 4 dist', 'dist': '36.6', 'angle': '-23'},
       {'column': 'p "Oxsy" 9 dist', 'dist': '30', 'angle': '3'}]
              }
          }
      }
      absoluteCoordArray =  [{'x': -39.5189, 'y': -3.9545}, {'x': -39.5189, 'y': -3.9545},
                             {'x': -39.5189, 'y': -3.9545}, {'x': -39.5189, 'y': -3.9545}]
      ansInfoForTick = calcInfoForTick(paramsTick, resMovePTeam, team, indexPlayer, absoluteCoordArray)
      self.assertEqual(round(ansInfoForTick.averageX, 4), -39.6656)
      self.assertEqual(round(ansInfoForTick.averageY, 4), 2.5762)
      self.assertEqual(ansInfoForTick.arrPlayer.viewPlayer,
                       ['b dist', 'p "HELIOS2017" 3 dist', 'p "HELIOS2017" 4 dist', 'p "Oxsy" 9 dist'])
      testPlArr = {
        'b dist': posPlayer(20.609574027359404, -5.098775305457144, 19),
        'p "HELIOS2017" 3 dist': posPlayer(-14.177650282083633, -12.826020080714315, 1),
        'p "HELIOS2017" 4 dist': posPlayer(-13.458047257353936, -28.307032011177125, -23),
        'p "Oxsy" 9 dist': posPlayer(-11.128962991453692, -12.770660206535416, 3),
      }
      for otherPl in ansInfoForTick.arrPlayer.mapPlayer:
          otherPlElem = ansInfoForTick.arrPlayer.mapPlayer[otherPl]
          otherPlElemTest = testPlArr[otherPl]
          self.assertEqual(otherPlElem.x, otherPlElemTest.x)
          self.assertEqual(otherPlElem.y, otherPlElemTest.y)
          self.assertEqual(int(otherPlElem.angle), otherPlElemTest.angle)

if __name__ == '__main__':
    unittest.main()