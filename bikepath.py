#
# TTP 210 
#
import csv
import math
import glob
import os
from copy import deepcopy
from streetmap import *
from ttputils import *


class BikePaths:
    def __init__(self, strmap):
        self.SpeedLimit = 10.0
        self.StreetMap = deepcopy(strmap)
        self.StreetMap.SetUniformSpeedLimit(self.SpeedLimit)
        self.StreetMap.IntersectionAcceleration = 1.0     # mph/s
        self.StreetMap.IntersectionDeceleration = 1.0     # mph/s
        self.StreetMap.IntersectionTurnVelocity = 5.0     # mph
        self.AddedPoints = {}
        self.AddedEdges = {}
        self.PointEdges = {}
        self.PointsOnEdge = {}
        self.EndPointsToEdge = {}
        self.FreePointToName = {}

    def Load(self, filename):
        self.AddedPoints = {}
        self.AddedEdges = {}
        self.PointEdges = {}
        self.PointsOnEdge = {}
        self.EndPointsToEdge = {}
        self.FreePointToName = {}
                                          
        with open(filename, 'rU') as BikePathFile:
            BikePathFileReader = csv.reader(BikePathFile, delimiter=',')
            Row = next(BikePathFileReader)
            PointCount = int(Row[0])
            LoadingUnattachedPoints = []
            LoadingEdgePoints = []
            for CurrentPoint in range(0,PointCount):
                Row = next(BikePathFileReader)
                if 3 == len(Row):
                    LoadingUnattachedPoints.append(Row)
                elif 5 == len(Row):
                    LoadingEdgePoints.append(Row)
                else:
                    return False
            Row = next(BikePathFileReader)
            EdgeCount = int(Row[0])
            LoadingUnattachedEdges = []
            LoadingAttachedEdges = []
            for CurrentPoint in range(0,EdgeCount):
                Row = next(BikePathFileReader)
                if 3 != len(Row):
                    return False
                if Row[1] in LoadingUnattachedPoints and Row[2] in LoadingUnattachedPoints:
                    LoadingUnattachedEdges.append(Row)
                else:
                    LoadingAttachedEdges.append(Row)
                    
            PointTranslation = {}
            EdgeTranslation = {}
            AllAddedPoints = []
            AllAddedEdges = []
            for Point in LoadingUnattachedPoints:
                PointTranslation[Point[0]] = self.AddPointXY(float(Point[1]), float(Point[2]))
                AllAddedPoints.append(PointTranslation[Point[0]])    
                if 0 == len(PointTranslation[Point[0]]):
                    return False
                #print('Added point ' + Point[0] + ' as ' + PointTranslation[Point[0]])
            for Edge in LoadingUnattachedEdges:
                if Edge[1] not in PointTranslation or Edge[2] not in PointTranslation:
                    return False
                EdgeTranslation[Edge[0]] = self.AddEdge(PointTranslation[Edge[1]], PointTranslation[Edge[2]])
                AllAddedEdges.append(EdgeTranslation[Edge[0]])
                #print('Added edge ' + Edge[0] + ' as ' + EdgeTranslation[Edge[0]])
            while len(LoadingAttachedEdges) or len(LoadingEdgePoints):
                PointsAdded = []
                for Point in LoadingEdgePoints:
                    Point1 = ''
                    Point2 = ''
                    if (Point[4] in EdgeTranslation):
                        # Edge has been added
                        if Point[1] in PointTranslation:
                            Point1 = PointTranslation[Point[1]]
                        elif (Point[1] not in AllAddedPoints) and (Point[1] in self.StreetMap.PointDB):
                            Point1 = Point[1]
                        if Point[2] in PointTranslation:
                            Point2 = PointTranslation[Point[2]]
                        elif (Point[2] not in AllAddedPoints) and (Point[2] in self.StreetMap.PointDB):
                            Point2 = Point[2]
                    elif (Point[4] in self.StreetMap.StreetDB) and (Point[4] not in AllAddedEdges):
                        # Edge is original street name
                        if Point[1] in PointTranslation:
                            Point1 = PointTranslation[Point[1]]
                        elif (Point[1] not in AllAddedPoints) and (Point[1] in self.StreetMap.PointDB):
                            Point1 = Point[1]
                        if Point[2] in PointTranslation:
                            Point2 = PointTranslation[Point[2]]
                        elif (Point[2] not in AllAddedPoints) and (Point[2] in self.StreetMap.PointDB):
                            Point2 = Point[2]
                    if len(Point1) and len(Point2):
                        PointTranslation[Point[0]] = self.AddPointOnEdge(Point1, Point2, float(Point[3]))
                        AllAddedPoints.append(PointTranslation[Point[0]])
                        PointsAdded.append(Point)
                        #print('Added point ' + Point[0] + ' as ' + PointTranslation[Point[0]])
                for Point in PointsAdded:
                    LoadingEdgePoints.remove(Point)
                EdgesAdded = []
                for Edge in LoadingAttachedEdges:
                    Point1 = ''
                    Point2 = ''
                    if Edge[1] in PointTranslation:
                        Point1 = PointTranslation[Edge[1]]
                    elif (Edge[1] not in AllAddedPoints) and (Edge[1] in self.StreetMap.PointDB):
                        Point1 = Edge[1]
                    if Edge[2] in PointTranslation:
                        Point2 = PointTranslation[Edge[2]]
                    elif (Edge[2] not in AllAddedPoints) and (Edge[2] in self.StreetMap.PointDB):
                        Point2 = Edge[2]
                    if len(Point1) and len(Point2):
                        EdgeTranslation[Edge[0]] = self.AddEdge(Point1, Point2)
                        AllAddedEdges.append(EdgeTranslation[Edge[0]])
                        EdgesAdded.append(Edge)
                        #print('Added edge ' + Edge[0] + ' as ' + EdgeTranslation[Edge[0]])
                for Edge in EdgesAdded:
                    LoadingAttachedEdges.remove(Edge)
        return True

    def Save(self, filename): 
        OutputFile = open(filename, 'w', newline='')
        BikePathFileWriter = csv.writer(OutputFile, quoting=csv.QUOTE_ALL)
        TempList = [len(self.AddedPoints)]
        BikePathFileWriter.writerow(TempList)
        for PointName in self.AddedPoints:
            if PointName in self.PointEdges and len(self.PointEdges[PointName]):
                BikePathFileWriter.writerow(list(self.AddedPoints[PointName]))
        TempList = [len(self.AddedEdges)]
        BikePathFileWriter.writerow(TempList)
        for EdgeName in self.AddedEdges:
            TempList = [EdgeName]
            TempList.extend(list(self.AddedEdges[EdgeName]))
            BikePathFileWriter.writerow(list(TempList))
        OutputFile.close()

    def TotalPathLength(self):
        TotalLength = 0.0
        for Edge, Points in self.AddedEdges.items():
            TotalLength += CalculateDistancePoint(self.StreetMap.PointDB[Points[0]], self.StreetMap.PointDB[Points[1]])
        return TotalLength

    def FindNearestPointInArea(self, x, y, dx, dy):
        MinX = x - dx
        MaxX = x + dx
        MinY = y - dy
        MaxY = y + dy
        BestPoint = ''
        BestDist = -1
        for Point in self.AddedPoints:
            Coord = self.StreetMap.PointDB[Point]
            if MinX <= Coord[0] and MaxX >= Coord[0] and MinY <= Coord[1] and MaxY >= Coord[1]:
                CurrentDist = CalculateDistance(x, y, Coord[0], Coord[1])
                if 0 > BestDist or CurrentDist < BestDist:
                    BestDist = CurrentDist
                    BestPoint = Point
        if 0 <= BestDist:
            return BestPoint
        for PointName, Coord in self.StreetMap.PointDB.items():
            if MinX <= Coord[0] and MaxX >= Coord[0] and MinY <= Coord[1] and MaxY >= Coord[1]:
                CurrentDist = CalculateDistance(x, y, Coord[0], Coord[1])
                if 0 > BestDist or CurrentDist < BestDist:
                    BestDist = CurrentDist
                    BestPoint = PointName
        return BestPoint

    def FindNearestEdgeLocationInArea(self, x, y, maxdist):
        LocationData = self.StreetMap.FindNearestStreetLocation(x, y, maxdist)
        if 0 == len(LocationData[0]):
            return ('', '', -1)
        
        #print("FNELIA ", LocationData, self.StreetMap.StreetDB[LocationData[0]])
        #if 0 == len(LocationData[1]) and 0 == len(LocationData[2]):
        #    Point1 = self.StreetMap.StreetDB[LocationData[0]][0]
        #    Point2 = self.StreetMap.StreetDB[LocationData[0]][1]
        #elif 0 == len(LocationData[1]):
        #    Point2 = self.StreetMap.FindIntersectionPoint(LocationData[0], LocationData[2])
        #    if Point2 != self.StreetMap.StreetDB[LocationData[0]][0]:
        #        Point1 = self.StreetMap.StreetDB[LocationData[0]][0]
        #    else:
        #        Point1 = self.StreetMap.StreetDB[LocationData[0]][1]
        #elif 0 == len(LocationData[2]):
        #    Point1 = self.StreetMap.FindIntersectionPoint(LocationData[0], LocationData[1])
        #    if Point1 != self.StreetMap.StreetDB[LocationData[0]][0]:
        #        Point2 = self.StreetMap.StreetDB[LocationData[0]][0]
        #    else:
        #        Point2 = self.StreetMap.StreetDB[LocationData[0]][1]            
        #else:
        #    Point1 = self.StreetMap.FindIntersectionPoint(LocationData[0], LocationData[1])
        #    Point2 = self.StreetMap.FindIntersectionPoint(LocationData[0], LocationData[2])
            
            
        return (LocationData[4][0], LocationData[4][1], LocationData[3])

    def GetLocationBetweenPoints(self, pt1, pt2, dist):
        if pt1 not in self.StreetMap.PointDB:
            return (-1, -1)
        if pt2 not in self.StreetMap.PointDB:              
            return (-1, -1)
        XY1 = self.StreetMap.PointDB[pt1]
        XY2 = self.StreetMap.PointDB[pt2]
        return (XY1[0] + (XY2[0] - XY1[0])*dist, XY1[1] + (XY2[1] - XY1[1])*dist)
        

    def AddPointOnEdge(self, pt1, pt2, dist):
        NewPointNumber = 1
        while "BPEP" + str(NewPointNumber) in self.AddedPoints:
            NewPointNumber += 1
        NewPointName = "BPEP" + str(NewPointNumber)
        PathName = ''
        if (pt1, pt2) in self.StreetMap.EdgeStreetDB:
            PathName = self.StreetMap.EdgeStreetDB[(pt1, pt2)]
        if not self.StreetMap.AddNode(NewPointName, pt1, pt2, dist, True):
            return ''
        if (pt1, pt2) in self.EndPointsToEdge:
            PathName = self.EndPointsToEdge[(pt1, pt2)]
            if PathName in self.PointsOnEdge:
                self.PointsOnEdge[PathName].append(NewPointName)
            else:
                self.PointsOnEdge[PathName] = [ NewPointName ]
            self.EndPointsToEdge[(pt1, NewPointName)] = PathName
            self.EndPointsToEdge[(NewPointName, pt1)] = PathName
            self.EndPointsToEdge[(pt2, NewPointName)] = PathName
            self.EndPointsToEdge[(NewPointName, pt2)] = PathName
        elif len(PathName) == 0:
            print("Error unknown edge for " + NewPointName, pt1, pt2, dist)
            print(self.StreetMap.EdgeStreetDB)
            quit()
        self.AddedPoints[NewPointName] = (NewPointName, pt1, pt2, dist, PathName)
        return NewPointName
        
    def AddPointXY(self, x, y):
        if (x, y) in self.FreePointToName:
            return self.FreePointToName[(x, y)]
        NewPointNumber = 1
        while "BPFP" + str(NewPointNumber) in self.AddedPoints:
            NewPointNumber += 1
        NewPointName = "BPFP" + str(NewPointNumber)
        if not self.StreetMap.AddUnattachedNode(NewPointName, x, y, True):
            return ''
        self.AddedPoints[NewPointName] = (NewPointName, x, y)
        self.FreePointToName[(x, y)] = NewPointName
        return NewPointName
        
    def RemovePoint(self, name):
        if not name in self.AddedPoints:
            return False
        if name in self.PointEdges:
            if len(self.PointEdges[name]):
                return False
            del self.PointEdges[name]
            
        if 5 == len(self.AddedPoints[name]):
            if not self.StreetMap.RemoveNode(name):
                return False
            PathName = self.AddedPoints[name][4]
            if len(PathName):
                self.PointsOnEdge[PathName].remove(name)
                if 0 == len(self.PointsOnEdge[PathName]):
                    del self.PointsOnEdge[PathName]
        else:
            if not self.StreetMap.RemoveUnattachedNode(name):
                return False
            Loc = (self.AddedPoints[name][1], self.AddedPoints[name][2])
            del self.FreePointToName[Loc]
        del self.AddedPoints[name]
        return True

    def AddEdge(self, pt1, pt2):
        if pt1 == pt2:
            return ''
        if pt1 not in self.StreetMap.PointDB:
            return ''
        if pt2 not in self.StreetMap.PointDB:
            return ''
        NewEdgeNumber = 1
        while "BPE" + str(NewEdgeNumber) in self.AddedEdges:
            NewEdgeNumber += 1
        NewEdgeName = "BPE" + str(NewEdgeNumber)
        if not self.StreetMap.AddEdge(NewEdgeName, pt1, pt2, self.SpeedLimit):
            return ''
        self.AddedEdges[NewEdgeName] = (pt1, pt2)
        if pt1 in self.AddedPoints:
            if pt1 in self.PointEdges:
                self.PointEdges[pt1].append(NewEdgeName)
            else:
                self.PointEdges[pt1] = [NewEdgeName]
        if pt2 in self.AddedPoints:
            if pt2 in self.PointEdges:
                self.PointEdges[pt2].append(NewEdgeName)
            else:
                self.PointEdges[pt2] = [NewEdgeName]
        self.EndPointsToEdge[(pt1, pt2)] = NewEdgeName
        self.EndPointsToEdge[(pt2, pt1)] = NewEdgeName
        return NewEdgeName

    def RemoveEdge(self, edgename):
        if edgename not in self.AddedEdges:
            return False
        if edgename in self.PointsOnEdge:
            if len(self.PointsOnEdge[edgename]):
                return False
            del self.PointsOnEdge[edgename]
        
        
        EndPoints = self.AddedEdges[edgename]
        if not self.StreetMap.RemoveEdge(EndPoints[0], EndPoints[1]):
            return False
            
        del self.EndPointsToEdge[EndPoints]
        del self.EndPointsToEdge[(EndPoints[1], EndPoints[0])]
        del self.AddedEdges[edgename]
        # remove dangling unattached points
        for Point in EndPoints:
            if Point in self.PointEdges:
                self.PointEdges[Point].remove(edgename)
                if 0 == len(self.PointEdges[Point]):
                    self.RemovePoint(Point)
                    
        return True


                
