#
# TTP 210 
#
import csv
import math
import random
import sys
from ttputils import *

class StreetMap:
    
    def __init__(self, filename):
        self.TrafficLightInterval = 30.0        # s
        self.IntersectionAcceleration = 4.0     # mph/s
        self.IntersectionDeceleration = 4.0     # mph/s
        self.IntersectionTurnVelocity = 15.0    # mph
        self.Load(filename)
        self.ClearAllBestPaths()
                                                    
    @staticmethod
    def CalculateAngle(src,dest):
        if src[0] != dest[0]:
            ATanAngle = math.atan((dest[1] - src[1])/(dest[0] - src[0]))
            if src[1] <= dest[1]:
                if src[0] < dest[0]:
                    return ATanAngle
                else:
                    return math.pi + ATanAngle
            else:
                if src[0] < dest[0]:
                    return 2.0 * math.pi + ATanAngle
                else:
                    return math.pi + ATanAngle
        else:
            if src[1] <= dest[1]:
                return math.pi * 0.5
            else:
                return math.pi * 1.5
    @staticmethod
    def CalculateAngleDifference(prev,next):
        if next > prev:
            return 2.0 * math.pi + prev - next
        else:
            return prev - next
    
    @staticmethod
    def CalculateAccelDecelDelay(fast,slow,delta):
        AverageSpeed = (fast + slow) * 0.5
        DeltaTime = (fast - slow) / delta
        return (1.0 - AverageSpeed/fast) * DeltaTime
    
    def FindNearestEdgeAndDistance(self,x,y,maxdist=-1):
        BestDistance = self.MaxX * self.MaxX + self.MaxY * self.MaxY
        for Edge in self.EdgeList:
            CurDistance = SegmentPointCalculateDistance(self.PointDB[Edge[0]],self.PointDB[Edge[1]],(x,y))
            if CurDistance <= BestDistance:
                BestSegment = Edge
                BestDistance = CurDistance
        if BestDistance < maxdist or 0 > maxdist:
            return (BestSegment, BestDistance)
        else:
            return ('',-1)
    
    def FindNearestEdge(self,x,y,maxdist=-1):
        return self.FindNearestEdgeAndDistance(x,y,maxdist)[0]
        
    def FindStreetNameFromEdge(self, edge):
        if edge in self.EdgeStreetDB:
            return self.EdgeStreetDB[edge]
        return ''
        
    def FindStreetNameAndIntersectionsFromEdge(self, edge):
        StreetName = self.FindStreetNameFromEdge(edge)
        if 0 == len(StreetName):
            return ('','','')
        Intersection = ['','']
        for Index in range(0, 2):
            StreetsEdge = self.PointStreetDB[edge[Index]][:]
            StreetsEdge.remove(StreetName)
            if 0 < len(StreetsEdge):
                Intersection[Index] = StreetsEdge[0]
            else:
                SeenEdges = [edge[1-Index]]
                CurrentEdge = edge[Index]
                while True:
                    SeenEdges.append(CurrentEdge)
                    for Point in self.ConnectivityDB[CurrentEdge]:
                        if Point not in SeenEdges:
                            CurrentEdge = Point
                            break
                    if CurrentEdge in SeenEdges:
                        break
                    StreetsEdge = self.PointStreetDB[CurrentEdge][:]
                    if StreetName not in StreetsEdge:
                        break
                    StreetsEdge.remove(StreetName)
                    if 0 < len(StreetsEdge):
                        Intersection[Index] = StreetsEdge[0]
                        break

        return (StreetName, Intersection[0], Intersection[1])
        
    def FindNearestStreetLocation(self,x,y,maxdist=-1):    
        Edge =  self.FindNearestEdge(x,y,maxdist)
        if 0 == len(Edge):
            return ('','','',-1, ('', ''))
        StreetInters = self.FindStreetNameAndIntersectionsFromEdge(Edge)
        Percent = SegmentPointCalculateNearestPercent(self.PointDB[Edge[0]], self.PointDB[Edge[1]], (x, y))
        if len(StreetInters[1]):
            if len(StreetInters[2]):
                IntersectionPoints = [self.FindIntersectionPoint(StreetInters[0], StreetInters[1]), self.FindIntersectionPoint(StreetInters[0], StreetInters[2])]
            else:
                IntersectionPoints = [self.FindIntersectionPoint(StreetInters[0], StreetInters[1]), Edge[1]]
        else:
            if len(StreetInters[2]):
                IntersectionPoints = [Edge[0], self.FindIntersectionPoint(StreetInters[0], StreetInters[2])]
            else:
                IntersectionPoints = [Edge[0], Edge[1]]
        if 0 == len(IntersectionPoints[0]):
            IntersectionPoints[0] = Edge[0]
        if 0 == len(IntersectionPoints[1]):
            IntersectionPoints[1] = Edge[1]
        #print(Edge, IntersectionPoints, StreetInters)        
        TotalPath = list(Edge)
        CurrentEdge = Edge[0]
        while CurrentEdge != IntersectionPoints[0]:
            #print(self.ConnectivityDB[CurrentEdge])
            for Point in self.ConnectivityDB[CurrentEdge]:
                if Point not in TotalPath:
                    CurrentEdge = Point
                    TotalPath.insert(0, Point)
                    break
        PathDistance = self.CalculateDistancePath(TotalPath[:-1]) + Percent * self.DistanceDB[Edge] 
        CurrentEdge = Edge[1]
        while CurrentEdge != IntersectionPoints[1]:
            for Point in self.ConnectivityDB[CurrentEdge]:
                if Point not in TotalPath:
                    CurrentEdge = Point
                    TotalPath.append(Point)
                    break
        return (StreetInters[0], StreetInters[1], StreetInters[2], PathDistance/self.CalculateDistancePath(TotalPath), IntersectionPoints)
        
    def CalculateDistancePointName(self, src, dest):
        SrcPoint = self.PointDB[src]
        DestPoint = self.PointDB[dest]
        return CalculateDistancePoint(SrcPoint, DestPoint)
        
    def CalculateDistancePath(self, path):
        if 0 == len(path):
            return 0.0
        PathLength = 0
        LastPoint = path[0]
        for Point in path[1:]:
            PathLength += self.DistanceDB[(LastPoint, Point)] 
            LastPoint = Point
        return PathLength
        
    def CalculateTimePath(self, path, accel = -1.0, decel = -1.0):
        if 0.0 >= accel:
            accel = self.IntersectionAcceleration
        if 0.0 >= decel:
            decel = self.IntersectionDeceleration
        if 0 == len(path):
            return 0.0
        PathTime = 0
        LastPoint = path[0]
        PointBefore = path[0]
        for Point in path[1:]:
            PathTime += self.TimeDB[(LastPoint, Point)] 
            PathTime += self.CalculateAverageIntersectionDelay( (PointBefore, LastPoint, Point, accel, decel) )
            PointBefore = LastPoint
            LastPoint = Point
        return PathTime
    
    def FindIntersectionPoint(self, mainstreet, sidestreet):
        if not mainstreet in self.StreetDB:
            return ''
        if not sidestreet in self.StreetDB:
            return ''
        
        IntersectionNodes = list(set(self.StreetDB[mainstreet]).intersection(set(self.StreetDB[sidestreet])))
        if 1 != len(IntersectionNodes):
            return ''
        return IntersectionNodes[0]
        
    def PathToStreetNames(self, path):
        StreetList = []
        if 0 == len(path):
            return StreetList
        LastPoint = path[0]
        for Point in path[1:]:
            if 0 == len(StreetList):
                StreetList.append(self.EdgeStreetDB[(LastPoint, Point)])
            elif StreetList[-1] != self.EdgeStreetDB[(LastPoint, Point)]:
                StreetList.append(self.EdgeStreetDB[(LastPoint, Point)])
            LastPoint = Point
        return StreetList

    def CalculateIntersectionType(self, path):
        if(path[0] == path[1]):
            return 'none'
        if self.EdgeStreetDB[(path[0], path[1])] == self.EdgeStreetDB[(path[1], path[2])]:
            if 2 < len(self.ConnectivityDB[path[1]]):
                #print("Through intersection on" , self.EdgeStreetDB[(path[0], path[1])])
                return 'through'
            else:
                #print("Stay on" , self.EdgeStreetDB[(path[0], path[1])])
                return 'none'
        elif 2 < len(self.ConnectivityDB[path[1]]):
            IncomingAngle = StreetMap.CalculateAngle(self.PointDB[path[0]], self.PointDB[path[1]])
            OutgoingAngle = StreetMap.CalculateAngle(self.PointDB[path[1]], self.PointDB[path[2]])
            TurnAngle = StreetMap.CalculateAngleDifference(OutgoingAngle, IncomingAngle)
            if math.pi/4.0 > TurnAngle or math.pi * 7.0 / 4.0 < TurnAngle:
                #print(self.EdgeStreetDB[(path[0], path[1])], "go straight onto" , self.EdgeStreetDB[(path[1], path[2])])
                return 'through'
            elif math.pi/4.0 <= TurnAngle and math.pi * 3.0/4.0 > TurnAngle:
                #print(self.EdgeStreetDB[(path[0], path[1])], "turn left onto" , self.EdgeStreetDB[(path[1], path[2])])
                return 'left'
            elif math.pi * 5.0/4.0 < TurnAngle and math.pi * 7.0/4.0 >= TurnAngle:
                #print(self.EdgeStreetDB[(path[0], path[1])], "turn right onto" , self.EdgeStreetDB[(path[1], path[2])])
                return 'right'
            else:
                #print(self.EdgeStreetDB[(path[0], path[1])], "U turn onto" , self.EdgeStreetDB[(path[1], path[2])])
                return 'U'
        else:
            #print(self.EdgeStreetDB[(path[0], path[1])], "becomes" , self.EdgeStreetDB[(path[1], path[2])])
            return 'none'

    def CalculateAverageIntersectionDelay(self, path, accel=-1.0, decel = -1.0):
        if 0.0 >= accel:
            accel = self.IntersectionAcceleration
        if 0.0 >= decel:
            decel = self.IntersectionDeceleration
        PostSpeed = self.SpeedDB[(path[1], path[2])]
        if path[0] == path[1]:
            return StreetMap.CalculateAccelDecelDelay(PostSpeed, 0.0, accel)
        PreSpeed = self.SpeedDB[(path[0], path[1])]
        
        AccelDecelDelay = 0.0
        StopAccelDecelDelay = 0.0
        ExpectedTrafficLightDelay = 0.0
        if path[1] not in self.NonIntersectionPoints:
            if self.EdgeStreetDB[(path[0], path[1])] == self.EdgeStreetDB[(path[1], path[2])]:
                if 2 < len(self.ConnectivityDB[path[1]]):
                    ExpectedTrafficLightDelay = self.TrafficLightInterval * 0.5
                    StopAccelDecelDelay = StreetMap.CalculateAccelDecelDelay(PostSpeed, 0.0, accel)
                    StopAccelDecelDelay += StreetMap.CalculateAccelDecelDelay(PreSpeed, 0.0, decel)
                    if PreSpeed < PostSpeed:
                        AccelDecelDelay = StreetMap.CalculateAccelDecelDelay(PostSpeed, PreSpeed, accel)
                    elif PreSpeed > PostSpeed:
                        AccelDecelDelay = StreetMap.CalculateAccelDecelDelay(PostSpeed, PreSpeed, decel)
            elif 2 < len(self.ConnectivityDB[path[1]]):
                IncomingAngle = StreetMap.CalculateAngle(self.PointDB[path[0]], self.PointDB[path[1]])
                OutgoingAngle = StreetMap.CalculateAngle(self.PointDB[path[1]], self.PointDB[path[2]])
                TurnAngle = StreetMap.CalculateAngleDifference(OutgoingAngle, IncomingAngle)
                ExpectedTrafficLightDelay = self.TrafficLightInterval * 0.5
                StopAccelDecelDelay = StreetMap.CalculateAccelDecelDelay(PostSpeed, 0.0, accel)
                StopAccelDecelDelay += StreetMap.CalculateAccelDecelDelay(PreSpeed, 0.0, decel)
                if math.pi/4.0 > TurnAngle or math.pi * 7.0 / 4.0 < TurnAngle:
                    if PreSpeed < PostSpeed:
                        AccelDecelDelay = StreetMap.CalculateAccelDecelDelay(PostSpeed, PreSpeed, accel)
                    elif PreSpeed > PostSpeed:
                        AccelDecelDelay = StreetMap.CalculateAccelDecelDelay(PostSpeed, PreSpeed, decel)
                else:
                    AccelDecelDelay = StreetMap.CalculateAccelDecelDelay(PreSpeed, self.IntersectionTurnVelocity, decel)
                    AccelDecelDelay += StreetMap.CalculateAccelDecelDelay(PostSpeed, self.IntersectionTurnVelocity, accel)
        return (AccelDecelDelay + (StopAccelDecelDelay + ExpectedTrafficLightDelay)) * 0.5

    def Load(self, filename):
        self.PointDB = {}               # Name of point to location (x,y)
        self.NonIntersectionPoints = [] # List of nonintersection points
        self.StreetDB = {}              # Street name to list of point names
        self.StreetLowercaseDB = {}     # Street name lower case to list of points
        self.EdgeStreetDB = {}          # Edge names (p1, p2) to street name
        self.PointStreetDB = {}         # Point name to street name(s)
        self.ConnectivityDB = {}        # Point name connected to other point names
        self.DistanceDB = {}            # Length of an edge
        self.SpeedDB = {}               # Speed limit of the edge
        self.TimeDB = {}                # Time to traverse at speed limit
        self.EdgeList = []
        self.MaxX = 0.0
        self.MaxY = 0.0
        with open(filename, 'rU') as StreetFile:
            StreetFileReader = csv.reader(StreetFile, delimiter=',')
            Row = next(StreetFileReader)
            TotalPoints = int(Row[0])
            for Index in range(0,TotalPoints):
                Row = next(StreetFileReader)
                CurX = float(Row[1])
                CurY = float(Row[2])
                self.PointDB[Row[0]] = (CurX , CurY)
                self.PointStreetDB[Row[0]] = []
                self.MaxX = max(self.MaxX, CurX)
                self.MaxY = max(self.MaxY, CurY)
                
            Row = next(StreetFileReader)
            TotalStreets = int(Row[0])
            for Index in range(0,TotalStreets):
                Row = next(StreetFileReader)
                self.StreetLowercaseDB[Row[0].lower()] = Row[0]
                self.StreetDB[Row[0]] = tuple( Row[1:] )
                if Row[0] not in self.PointStreetDB[Row[1]]:
                    self.PointStreetDB[Row[1]].append(Row[0])
                for Index in range(2,len(Row)):
                    self.EdgeStreetDB[(Row[Index-1],Row[Index])] = Row[0]
                    self.EdgeStreetDB[(Row[Index],Row[Index-1])] = Row[0]
                    if Row[0] not in self.PointStreetDB[Row[Index]]:
                        self.PointStreetDB[Row[Index]].append(Row[0])
                
            Row = next(StreetFileReader)
            TotalNodes = int(Row[0])
            for Index in range(0,TotalNodes):
                Row = next(StreetFileReader)
                self.ConnectivityDB[Row[0]] = tuple( Row[1:] )
                for Point in Row[1:]:
                    if not (Row[0], Point) in self.DistanceDB:
                        Dist = self.CalculateDistancePointName(Row[0],Point)
                        self.DistanceDB[(Row[0],Point)] = Dist
                        self.DistanceDB[(Point,Row[0])] = Dist
                        self.SpeedDB[(Row[0],Point)] = 25.0
                        self.SpeedDB[(Point,Row[0])] = 25.0
                        self.TimeDB[(Row[0],Point)] = Dist * 3600.0 / 25.0
                        self.TimeDB[(Point,Row[0])] = Dist * 3600.0 / 25.0
                    if Row[0] < Point:
                        if not (Row[0], Point) in self.EdgeList:    
                            self.EdgeList.append( (Row[0], Point) )
            Row = next(StreetFileReader)
            TotalNodes = int(Row[0])
            for Index in range(0,TotalNodes):
                Row = next(StreetFileReader)
                SpeedLimit = float(Row[2])
                Dist = self.DistanceDB[(Row[0],Row[1])]
                self.SpeedDB[(Row[0],Row[1])] = SpeedLimit
                self.SpeedDB[(Row[1],Row[0])] = SpeedLimit
                self.TimeDB[(Row[0],Point)] = Dist * 3600.0 / SpeedLimit
                self.TimeDB[(Point,Row[0])] = Dist * 3600.0 / SpeedLimit
                
        self.Perimeter = self.FindPerimeter()

    def SetUniformSpeedLimit(self, speedlimit):
        for Edge in self.DistanceDB:
            self.SpeedDB[Edge] = speedlimit
            self.TimeDB[Edge] = self.DistanceDB[Edge] * 3600.0 / speedlimit

    def AddNode(self, name, seg1, seg2, dist, nonintersection=False):
        if name in self.PointDB:
            return False
        if (not seg1 in self.PointDB) or (not seg2 in self.PointDB):
            return False
        if (0.0 >= dist) or (1.0 <= dist):
            return False
        if not (seg1, seg2) in self.DistanceDB:
            PossibleStreetNames1 = []
            PossibleStreetNames2 = []
            for Point in self.ConnectivityDB[seg1]:
                PossibleStreetNames1.append(self.EdgeStreetDB[(seg1, Point)])
            for Point in self.ConnectivityDB[seg2]:
                PossibleStreetNames2.append(self.EdgeStreetDB[(seg2, Point)])
            
            PossibleStreetNames = list(set(PossibleStreetNames1).intersection(set(PossibleStreetNames2)))
            #print(PossibleStreetNames)
            if 1 != len(PossibleStreetNames):
                return False
            
            StreetNodeList = list(self.StreetDB[PossibleStreetNames[0]])
            Index1 = StreetNodeList.index(seg1)
            Index2 = StreetNodeList.index(seg2)
            if(Index1 > Index2):
                dist = 1.0 - dist
                seg1, seg2 = seg2, seg1
                Index1, Index2 = Index2, Index1
            TotalDistance = 0.0
            for Index in range(Index1, Index2):
                TotalDistance += self.DistanceDB[(StreetNodeList[Index], StreetNodeList[Index + 1])]
            TotalDistance *= dist
            for Index in range(Index1, Index2):
                if(TotalDistance < self.DistanceDB[(StreetNodeList[Index], StreetNodeList[Index + 1])]):
                    dist = TotalDistance / self.DistanceDB[(StreetNodeList[Index], StreetNodeList[Index + 1])]
                    seg1 = StreetNodeList[Index]
                    seg2 = StreetNodeList[Index + 1]
                    break
                TotalDistance -= self.DistanceDB[(StreetNodeList[Index], StreetNodeList[Index + 1])]
        
        Seg1Point = self.PointDB[seg1]
        Seg2Point = self.PointDB[seg2]
        NodePoint = CalculatePointLocation(Seg1Point, Seg2Point, dist)
        
        self.PointDB[name] = NodePoint
        if nonintersection:
            self.NonIntersectionPoints.append(name)
        StreetName = self.EdgeStreetDB[(seg1, seg2)]
        self.PointStreetDB[name] = [StreetName]
        self.EdgeStreetDB[(seg1, name)] = StreetName
        self.EdgeStreetDB[(name, seg1)] = StreetName
        self.EdgeStreetDB[(seg2, name)] = StreetName
        self.EdgeStreetDB[(name, seg2)] = StreetName
        del self.EdgeStreetDB[(seg1, seg2)]
        del self.EdgeStreetDB[(seg2, seg1)]
        
        StreetNodeList = list(self.StreetDB[StreetName])
        Index1 = StreetNodeList.index(seg1)
        Index2 = StreetNodeList.index(seg2)
        if(Index1 < Index2):
            StreetNodeList.insert(Index2, name)
        else:
            StreetNodeList.insert(Index1, name)
        self.StreetDB[StreetName] = tuple(StreetNodeList)
        
        self.ConnectivityDB[name] = (seg1, seg2)
        Seg1Connect = [name]
        for ConNode in self.ConnectivityDB[seg1]:
            if ConNode != seg2:
                Seg1Connect.append(ConNode)
        self.ConnectivityDB[seg1] = tuple(Seg1Connect)
        Seg2Connect = [name]
        for ConNode in self.ConnectivityDB[seg2]:
            if ConNode != seg1:
                Seg2Connect.append(ConNode)
        self.ConnectivityDB[seg2] = tuple(Seg2Connect)
        
        Dist12 = self.DistanceDB[(seg1, seg2)]
        self.DistanceDB[(seg1, name)] = Dist12 * dist
        self.DistanceDB[(name, seg1)] = Dist12 * dist
        self.DistanceDB[(seg2, name)] = Dist12 * (1.0 - dist)
        self.DistanceDB[(name, seg2)] = Dist12 * (1.0 - dist)
        del self.DistanceDB[(seg1, seg2)]
        del self.DistanceDB[(seg2, seg1)]
        
        Speed12 = self.SpeedDB[(seg1, seg2)]
        self.SpeedDB[(seg1, name)] = Speed12
        self.SpeedDB[(name, seg1)] = Speed12
        self.SpeedDB[(seg2, name)] = Speed12
        self.SpeedDB[(name, seg2)] = Speed12
        del self.SpeedDB[(seg1, seg2)]
        del self.SpeedDB[(seg2, seg1)]   
        
        Time12 = self.TimeDB[(seg1, seg2)]
        self.TimeDB[(seg1, name)] = Time12 * dist
        self.TimeDB[(name, seg1)] = Time12 * dist
        self.TimeDB[(seg2, name)] = Time12 * (1.0 - dist)
        self.TimeDB[(name, seg2)] = Time12 * (1.0 - dist)
        del self.TimeDB[(seg1, seg2)]
        del self.TimeDB[(seg2, seg1)]
        
        if name < seg1:
            self.EdgeList.append((name,seg1))
        else:
            self.EdgeList.append((seg1,name))
        if name < seg2:
            self.EdgeList.append((name,seg2))
        else:
            self.EdgeList.append((seg2,name))
            
        if seg1 < seg2:
            self.EdgeList.remove((seg1,seg2))
        else:
            self.EdgeList.remove((seg2,seg1))
        
        self.ClearAllBestPaths()
        return True
        
    def RemoveNode(self, name):
        if not name in self.PointDB:
            return False
        if 2 != len(self.ConnectivityDB[name]):
            return False
        Segment1 = self.ConnectivityDB[name][0]
        Segment2 = self.ConnectivityDB[name][1]
        
        self.TimeDB[(Segment1, Segment2)] = self.TimeDB[(Segment1, name)] + self.TimeDB[(name, Segment2)]
        self.TimeDB[(Segment2, Segment1)] = self.TimeDB[(Segment2, name)] + self.TimeDB[(name, Segment1)]
        del self.TimeDB[(name, Segment1)]
        del self.TimeDB[(Segment1, name)]
        del self.TimeDB[(name, Segment2)]
        del self.TimeDB[(Segment2, name)]
        
        self.DistanceDB[(Segment1, Segment2)] = self.DistanceDB[(Segment1, name)] + self.DistanceDB[(name, Segment2)]
        self.DistanceDB[(Segment2, Segment1)] = self.DistanceDB[(Segment2, name)] + self.DistanceDB[(name, Segment1)]
        del self.DistanceDB[(name, Segment1)]
        del self.DistanceDB[(Segment1, name)]
        del self.DistanceDB[(name, Segment2)]
        del self.DistanceDB[(Segment2, name)]
        
        self.SpeedDB[(Segment1, Segment2)] = self.SpeedDB[(name, Segment1)]
        self.SpeedDB[(Segment2, Segment1)] = self.SpeedDB[(name, Segment2)]
        del self.SpeedDB[(name, Segment1)]
        del self.SpeedDB[(Segment1, name)]
        del self.SpeedDB[(name, Segment2)]
        del self.SpeedDB[(Segment2, name)]
        
        Seg1Connect = [Segment2]
        for ConNode in self.ConnectivityDB[Segment1]:
            if ConNode != name:
                Seg1Connect.append(ConNode)
        self.ConnectivityDB[Segment1] = tuple(Seg1Connect)
        Seg2Connect = [Segment1]
        for ConNode in self.ConnectivityDB[Segment2]:
            if ConNode != name:
                Seg2Connect.append(ConNode)
        self.ConnectivityDB[Segment2] = tuple(Seg2Connect)

        if name < Segment1:
            self.EdgeList.remove((name,Segment1))
        else:
            self.EdgeList.remove((Segment1,name))
        if name < Segment2:
            self.EdgeList.remove((name,Segment2))
        else:
            self.EdgeList.remove((Segment2,name))
            
        if Segment1 < Segment2:
            self.EdgeList.append((Segment1,Segment2))
        else:
            self.EdgeList.append((Segment2,Segment1))


        StreetName = self.EdgeStreetDB[(name, Segment1)]
        self.EdgeStreetDB[(Segment1, Segment2)] = StreetName
        self.EdgeStreetDB[(Segment2, Segment1)] = StreetName
        del self.EdgeStreetDB[(name, Segment1)]
        del self.EdgeStreetDB[(Segment1, name)]
        del self.EdgeStreetDB[(name, Segment2)]
        del self.EdgeStreetDB[(Segment2, name)]
        
        StreetNodeList = list(self.StreetDB[StreetName])
        StreetNodeList.remove(name)
        self.StreetDB[StreetName] = tuple(StreetNodeList)

        del self.PointDB[name]
        if name in self.NonIntersectionPoints:
            self.NonIntersectionPoints.remove(name)
        del self.PointStreetDB[name]
        del self.ConnectivityDB[name]
        self.ClearAllBestPaths()
        return True
    
    def AddUnattachedNode(self, name, x, y, nonintersection=False):
        if name in self.PointDB:
            return False
        if (0.0 > x) or (0.0 > y) or (self.MaxX < x) or (self.MaxY < y):
            return False
        self.PointDB[name] = (x, y)
        if nonintersection:
            self.NonIntersectionPoints.append(name)
        self.PointStreetDB[name] = []
        self.ConnectivityDB[name] = ()
        self.ClearAllBestPaths()
        return True
        
    def RemoveUnattachedNode(self, name):
        if name not in self.PointDB:
            return False
        if len(self.ConnectivityDB[name]):
            return False
        del self.PointDB[name]
        if name in self.NonIntersectionPoints:
            self.NonIntersectionPoints.remove(name)
        del self.PointStreetDB[name]
        del self.ConnectivityDB[name]
        self.ClearAllBestPaths()
        return True
        
    def AddEdge(self, streetname, seg1, seg2, speedlimit):
        if (not seg1 in self.PointDB) or (not seg2 in self.PointDB):
            return False

        if (seg1, seg2) in self.DistanceDB:
            return False
        
        self.EdgeStreetDB[(seg1, seg2)] = streetname
        if streetname not in self.PointStreetDB[seg1]:
            self.PointStreetDB[seg1].append(streetname)
        if streetname not in self.PointStreetDB[seg2]:
            self.PointStreetDB[seg2].append(streetname)
        self.EdgeStreetDB[(seg1, seg2)] = streetname
        self.EdgeStreetDB[(seg2, seg1)] = streetname
        if streetname in self.StreetDB:
            StreetNodeList = list(self.StreetDB[streetname])
            if seg1 not in StreetNodeList:
                StreetNodeList.append(seg1)
            if seg2 not in StreetNodeList:
                StreetNodeList.append(seg2)        
            self.StreetDB[streetname] = tuple(StreetNodeList)
             
        else:
            self.StreetDB[streetname] = (seg1, seg2)

        Seg1Connect = list(self.ConnectivityDB[seg1])
        Seg1Connect.append(seg2)
        self.ConnectivityDB[seg1] = tuple(Seg1Connect)
        Seg2Connect = list(self.ConnectivityDB[seg2])
        Seg2Connect.append(seg1)
        self.ConnectivityDB[seg2] = tuple(Seg2Connect)
        
        Dist = self.CalculateDistancePointName(seg1,seg2)
        self.DistanceDB[(seg1, seg2)] = Dist
        self.DistanceDB[(seg2, seg1)] = Dist
        self.SpeedDB[(seg1, seg2)] = speedlimit
        self.SpeedDB[(seg2, seg1)] = speedlimit
        self.TimeDB[(seg1, seg2)] = Dist * 3600.0 / speedlimit
        self.TimeDB[(seg2, seg1)] = Dist * 3600.0 / speedlimit
        
        if seg1 < seg2:
            self.EdgeList.append((seg1,seg2))
        else:
            self.EdgeList.append((seg2,seg1))
            
        self.ClearAllBestPaths()
        return True
    
    def RemoveEdge(self, seg1, seg2):
        if (not seg1 in self.PointDB) or (not seg2 in self.PointDB):
            return False

        if (seg1, seg2) not in self.DistanceDB:
            return False
        
        Seg1Point = self.PointDB[seg1]
        Seg2Point = self.PointDB[seg2]
        
        StreetName = self.EdgeStreetDB[(seg1, seg2)]
        del self.EdgeStreetDB[(seg1, seg2)]
        del self.EdgeStreetDB[(seg2, seg1)]
        
        Seg1Connect = list(self.ConnectivityDB[seg1])
        Seg1Connect.remove(seg2)
        self.ConnectivityDB[seg1] = tuple(Seg1Connect)
        Seg2Connect = list(self.ConnectivityDB[seg2])
        Seg2Connect.remove(seg1)
        self.ConnectivityDB[seg2] = tuple(Seg2Connect)
        
        StreetDBList = list(self.StreetDB[StreetName])
        IsStillOnStreet = False
        for Node in self.ConnectivityDB[seg1]:
            if Node in self.StreetDB[StreetName]:
                IsStillOnStreet = True
                break
        if not IsStillOnStreet:
            StreetDBList.remove(seg1)
            self.PointStreetDB[seg1].remove(StreetName)
        IsStillOnStreet = False
        for Node in self.ConnectivityDB[seg2]:
            if Node in self.StreetDB[StreetName]:
                IsStillOnStreet = True
                break
        if not IsStillOnStreet:
            StreetDBList.remove(seg2)
            self.PointStreetDB[seg2].remove(StreetName)

        if 0 < len(StreetDBList):
            self.StreetDB[StreetName] = tuple(StreetDBList)
        else:
            del self.StreetDB[StreetName]
        
        del self.DistanceDB[(seg1, seg2)]
        del self.DistanceDB[(seg2, seg1)]
        del self.SpeedDB[(seg1, seg2)]
        del self.SpeedDB[(seg2, seg1)]
        del self.TimeDB[(seg1, seg2)]
        del self.TimeDB[(seg2, seg1)]
        
        if seg1 < seg2:
            self.EdgeList.remove((seg1,seg2))
        else:
            self.EdgeList.remove((seg2,seg1))
            
        self.ClearAllBestPaths()
        return True
    
    
    def FindPerimeter(self):
       MinPoint = (self.MaxX, self.MaxY)
       for Point in self.PointDB:
           Location = self.PointDB[Point]
           if MinPoint[0] > Location[0]:
               MinPoint = Location
               MinPointName = Point
           elif (MinPoint[0] == Location[0]) and (MinPoint[1] > Location[1]):
               MinPoint = Location
               MinPointName = Point
       PerimeterList = [ MinPointName ]
       LastPoint = (MinPoint[0], MinPoint[1] + 1.0)
       CurrentPoint = MinPoint
       CurrentPointName = MinPointName
       while True:
           BestAngle = 0
           PrevAngle = StreetMap.CalculateAngle(CurrentPoint,LastPoint)
           for Point in self.ConnectivityDB[ CurrentPointName ]:
               NextPoint = self.PointDB[Point]
               if LastPoint != NextPoint:
                   NextAngle = StreetMap.CalculateAngle(CurrentPoint,NextPoint)
                   AngleDelta = StreetMap.CalculateAngleDifference(PrevAngle, NextAngle)
                   if BestAngle < AngleDelta:
                       BestAngle = AngleDelta
                       BestPoint = NextPoint
                       BestPointName = Point
           LastPoint = CurrentPoint
           CurrentPoint = BestPoint
           CurrentPointName = BestPointName
           PerimeterList.append( BestPointName )
           if CurrentPoint == MinPoint:
               break
       return PerimeterList
    
    def UpdatePerimeter(self):
        self.Perimeter = self.FindPerimeter()
    
    def InsidePerimeter(self, x, y):
        if (0.0 > x) or (self.MaxX < x):
            return False;
        if (0.0 > y) or (self.MaxY < y):
            return False;
        Crossings = 0
        LastPoint = self.PointDB[self.Perimeter[0]]
        for Edge in self.Perimeter[1:]:
            CurrentPoint = self.PointDB[Edge]
            MinY = min(LastPoint[1], CurrentPoint[1])
            MaxY = max(LastPoint[1], CurrentPoint[1])
            if (MinY <= y) and (y <= MaxY):
                if MinY == MaxY:
                    if min(LastPoint[0], CurrentPoint[0]) <= x:
                        Crossings = Crossings + 1
                elif LastPoint[0] == CurrentPoint[0]:
                    if LastPoint[0] <= x:
                        Crossings = Crossings + 1
                else:
                    MXB = LineCalculateMB(LastPoint[0], LastPoint[1], CurrentPoint[0], CurrentPoint[1])
                    if ((y - MXB[1]) / MXB[0]) <= x:
                        Crossings = Crossings + 1
            LastPoint = CurrentPoint
        return (Crossings % 2) == 1
        
    def FindNearestLeftRight(self, point):
        Closest = [self.MaxX*2, self.MaxX*2]
        PointLocation = self.PointDB[point]
        for Edge in self.EdgeList:
            if (Edge[0] != point) and (Edge[1] != point):
                Point1 = self.PointDB[Edge[0]]
                Point2 = self.PointDB[Edge[1]]
                MinY = min(Point1[1], Point2[1])
                MaxY = max(Point1[1], Point2[1])
                if (MinY <= PointLocation[1]) and (PointLocation[1] <= MaxY):
                    if MinY == MaxY:
                        MinX = min(Point1[0], Point2[0])
                        MaxX = max(Point1[0], Point2[0])
                        if MaxX < PointLocation[0]:
                            Dist = PointLocation[0] - MaxX
                            Closest[0] = min(Closest[0],Dist)
                        else:
                            Dist = MinX - PointLocation[0]
                            Closest[1] = min(Closest[1],Dist)
                    elif Point1[0] == Point2[0]:
                        if Point1[0] < PointLocation[0]:
                            Closest[0] = min(Closest[0],PointLocation[0]-Point1[0])
                        else:
                            Closest[1] = min(Closest[1],Point1[0]-PointLocation[0])
                    else:
                        MXB = LineCalculateMB(Point1[0], Point1[1], Point2[0], Point2[1])
                        XInt = ((PointLocation[1] - MXB[1])/MXB[0])
                        if XInt < PointLocation[0]:
                            Closest[0] = min(Closest[0],PointLocation[0]-XInt)
                        else:
                            Closest[1] = min(Closest[1],XInt-PointLocation[0])
        return Closest
        
    def FindNearestTopBottom(self, point):
        Closest = [self.MaxX*2, self.MaxX*2]
        PointLocation = self.PointDB[point]
        for Edge in self.EdgeList:
            if (Edge[0] != point) and (Edge[1] != point):
                Point1 = self.PointDB[Edge[0]]
                Point2 = self.PointDB[Edge[1]]
                MinX = min(Point1[0], Point2[0])
                MaxX = max(Point1[0], Point2[0])
                if (MinX <= PointLocation[0]) and (PointLocation[0] <= MaxX):
                    if MinX == MaxX:
                        MinY = min(Point1[1], Point2[1])
                        MaxY = max(Point1[1], Point2[1])
                        if MaxY < PointLocation[1]:
                            Dist = PointLocation[1] - MaxY
                            Closest[0] = min(Closest[0],Dist)
                        else:
                            Dist = MinY - PointLocation[1]
                            Closest[1] = min(Closest[1],Dist)
                    else:
                        MXB = LineCalculateMB(Point1[0], Point1[1], Point2[0], Point2[1])
                        YInt = MXB[0] * PointLocation[0] + MXB[1]
                        if YInt < PointLocation[1]:
                            Closest[0] = min(Closest[0],PointLocation[1]-YInt)
                        else:
                            Closest[1] = min(Closest[1],YInt-PointLocation[1])
        return Closest
        
    def FindShortestPath(self,src,dest,bestlength=-1.0,curdist=0.0,path=[]):
        if (src,dest) in self.ShortestPathDB:
            path = path + self.ShortestPathDB[(src,dest)]
            return path
        path = path + [src]
        if src == dest:
            return path
        if src not in self.ConnectivityDB:
            return None
        if (0.0 <= bestlength) and (bestlength < (self.CalculateDistancePointName(src,dest) + curdist)):
            return None
        Shortest = None
        ShortestLength = -1
        CurrentLength = curdist #self.CalculateDistancePath(path)
        NodesToSearch = []
        for Node in self.ConnectivityDB[src]:
            if Node not in path:
                NodesToSearch.append((self.CalculateDistancePointName(Node,dest),Node))
        NodesToSearch.sort()
        for DistNode in NodesToSearch:
            Node = DistNode[1]
            NextLength = self.DistanceDB[(src, Node)] #self.CalculateDistancePointName(src, Node)
            if Node not in path:
                if (0.0 > bestlength) or (CurrentLength + NextLength < bestlength):
                    NewPath = self.FindShortestPath(Node, dest, bestlength, CurrentLength + NextLength, path)
                    if NewPath:
                        NewLength = self.CalculateDistancePath(NewPath)
                        if not Shortest or (NewLength < ShortestLength):
                            Shortest = NewPath
                            ShortestLength = NewLength
                            bestlength = NewLength
                            
        if Shortest:
            SrcIndex = Shortest.index(src)
            self.ShortestPathDB[(src,dest)] = Shortest[SrcIndex:]
            self.ShortestPathDB[(dest,src)] = list(Shortest[SrcIndex:])[::-1]
            self.ShortestPathDistanceDB[(src,dest)] = self.CalculateDistancePath(Shortest[SrcIndex:])
            self.ShortestPathDistanceDB[(dest,src)] = self.ShortestPathDistanceDB[(src,dest)]
            self.ShortestPathDurationDB[(src,dest)] = self.CalculateTimePath(Shortest[SrcIndex:])
            self.ShortestPathDurationDB[(dest,src)] = self.ShortestPathDurationDB[(src,dest)]
        return Shortest
        
    def FindFastestPath(self,src,dest,besttime=-1.0,curtime=0.0,path=[]):
        if (src,dest) in self.FastestPathDB:
            path = path + self.FastestPathDB[(src,dest)]
            return path
        if len(path):
            IncomingNode = path[-1]
        else:
            IncomingNode = src
        path = path + [src]
        if src == dest:
            return path
        if src not in self.ConnectivityDB:
            return None
        if (0.0 <= besttime) and (besttime < (self.CalculateDistancePointName(src,dest) * 3600.0/25.0 + curtime)):
            return None
        Shortest = None
        ShortestTime = -1
        CurrentTime = curtime 
        NodesToSearch = []
        for Node in self.ConnectivityDB[src]:
            if Node not in path:
                NodesToSearch.append((self.CalculateDistancePointName(Node,dest),Node))
        NodesToSearch.sort()
        for DistNode in NodesToSearch:
            Node = DistNode[1]
            NextTime = self.TimeDB[(src, Node)] + self.CalculateAverageIntersectionDelay((IncomingNode, src, Node))
            if Node not in path:
                if (0.0 > besttime) or (CurrentTime + NextTime < besttime):
                    NewPath = self.FindFastestPath(Node, dest, besttime, CurrentTime + NextTime, path)
                    if NewPath:
                        NewTime = self.CalculateTimePath(NewPath)
                        if not Shortest or (NewTime < ShortestTime):
                            Shortest = NewPath
                            ShortestTime = NewTime
                            besttime = NewTime
        if Shortest:
            SrcIndex = Shortest.index(src)
            self.FastestPathDB[(src,dest)] = Shortest[SrcIndex:]
            self.FastestPathDB[(dest,src)] = list(Shortest[SrcIndex:])[::-1]
            self.FastestPathDistanceDB[(src,dest)] =  self.CalculateDistancePath(Shortest[SrcIndex:])
            self.FastestPathDistanceDB[(dest,src)] = self.FastestPathDistanceDB[(src,dest)]
            self.FastestPathDurationDB[(src,dest)] =  self.CalculateTimePath(Shortest[SrcIndex:])
            self.FastestPathDurationDB[(dest,src)] = self.FastestPathDurationDB[(src,dest)]
        return Shortest
        
    def CalculateAllBestPathsToDestination(self,dest,updatefun=None):
        TotalPaths = (len(self.PointDB) - 1) * 2
        CalcedPaths = 0
        LastUpdate = 0
        for Node in self.PointDB:
            if(Node != dest):
                Path = self.FindShortestPath(Node,dest)
                CalcedPaths += 1
                if LastUpdate != int(CalcedPaths * 100 / TotalPaths):
                    LastUpdate += 1
                    if updatefun:
                        updatefun()
                Path = self.FindFastestPath(Node,dest)
                CalcedPaths += 1
                if LastUpdate != int(CalcedPaths * 100 / TotalPaths):
                    LastUpdate += 1
                    if updatefun:
                        updatefun()
                
    def ClearAllBestPaths(self):
        self.ShortestPathDB = {}
        self.ShortestPathDistanceDB = {}
        self.ShortestPathDurationDB = {}
        self.FastestPathDB = {}
        self.FastestPathDistanceDB = {}
        self.FastestPathDurationDB = {}
        
    def GenerateSpeedTrace(self, path, accel, decel):
        Velocity = 0.0
        SpeedTrace = [0.0, 0.0, 0.0]
        CurInter = path[0]
        PrevInter = path[0]
        PrevSpeedLimit = 0.0
        CurDistance = 0.0
        SegDistance = 0.0
        SpeedLimits = {}
        TargetSpeedTimes = {}
        SegmentNames = []
        for NextInter in path[1:]:
            SegmentNames.append((CurInter, NextInter))
            NextSpeedLimit = self.SpeedDB[(CurInter, NextInter)]
            SpeedLimits[(CurInter, NextInter)] = NextSpeedLimit
            InterType = self.CalculateIntersectionType((PrevInter, CurInter, NextInter))
            TimeAtInter = 0
            TargetSpeedNext = NextSpeedLimit
            if InterType != 'none':
                if random.random() < 0.5: 
                    TimeAtInter = int(math.ceil(random.random() * self.TrafficLightInterval))
                    TargetSpeedNext = 0.0
                elif InterType != 'through':
                    TimeAtInter = 1
                    TargetSpeedNext = self.IntersectionTurnVelocity
                    
            TargetSpeedTimes[(CurInter, NextInter)] = (TargetSpeedNext, TimeAtInter)
            PrevInter = CurInter
            CurInter = NextInter
        SpeedLimitAfter = 0.0
        TargetSpeedNext = 0.0
        ReducedSpeeds = False
        for SegName in SegmentNames[::-1]:
            NextSpeedLimit = SpeedLimits[SegName]
            if TargetSpeedNext < NextSpeedLimit:
                NextSegDistance = self.DistanceDB[SegName]
                Values =  QuadraticEquation(decel/3600.0, TargetSpeedNext/3600.0, -NextSegDistance)
                if 0 == len(Values):                        
                    TimeToAccel = 100.0
                else:
                    TimeToAccel = math.floor(max(Values))
                if NextSpeedLimit > TargetSpeedNext + TimeToAccel * decel:
                    NextSpeedLimit = min(NextSpeedLimit, TargetSpeedNext + TimeToAccel * decel)
                    ReducedSpeeds = True
            TargetSpeedTimes[SegName] = (min(TargetSpeedTimes[SegName][0],NextSpeedLimit), TargetSpeedTimes[SegName][1])
            TargetSpeedNext = TargetSpeedTimes[SegName][0]
            SpeedLimits[SegName] = NextSpeedLimit
            SpeedLimitAfter = NextSpeedLimit
        CurInter = path[0]
        PrevInter = path[0]
        TruePrevSpeedLimit = 0
        for NextInter in path[1:]:
            #NextSpeedLimit = self.SpeedDB[(CurInter, NextInter)]
            TrueNextSpeedLimit = self.SpeedDB[(CurInter, NextInter)]
            NextSpeedLimit = SpeedLimits[(CurInter, NextInter)]
            NextInterIndex = path.index(NextInter)
            #InterType = self.CalculateIntersectionType((PrevInter, CurInter, NextInter))
            #TimeAtInter = 0
            TargetSpeedNext = TargetSpeedTimes[(CurInter, NextInter)][0]
            TimeAtInter = TargetSpeedTimes[(CurInter, NextInter)][1]
            if PrevInter != CurInter:
                #TargetSpeedNext = NextSpeedLimit
                #if InterType != 'none':
                #    if random.random() < 0.5: 
                #        TimeAtInter = int(math.ceil(random.random() * self.TrafficLightInterval))
                #        TargetSpeedNext = 0.0
                #    elif InterType != 'through':
                #        TimeAtInter = 1
                #        TargetSpeedNext = self.IntersectionTurnVelocity
                        
                CurDistance = 0.0
                Decellerating = False
                DecelRate = 0.0
                while CurDistance < SegDistance:
                    SecondsToAccel = math.ceil((PrevSpeedLimit - Velocity) / accel)
                    CurAccel = accel
                    if 0.0 < SecondsToAccel:
                        CurAccel = (PrevSpeedLimit - Velocity) / SecondsToAccel
                    if (TruePrevSpeedLimit > PrevSpeedLimit) or (((Velocity + decel)/3600.0) > (SegDistance - CurDistance)):
                        MaxRandomSpeed = PrevSpeedLimit
                    else:
                        MaxRandomSpeed = round(PrevSpeedLimit + random.random() * 2.01 - 1.0)
                    MaxRandomSpeed = max(1.0, MaxRandomSpeed)    
                    NextVelocity = min(Velocity + CurAccel, MaxRandomSpeed)
                    if Decellerating:
                        if 0 < DecelSeconds:
                            #DecelRate = (Velocity - TargetSpeedNext) / TimeToDecel
                            NextVelocity = max(Velocity - DecelRate, TargetSpeedNext)
                            DecelSeconds = DecelSeconds - 1
                        else:
                            NextVelocity = TargetSpeedNext
                            CurDistance = SegDistance
                    elif Velocity > TargetSpeedNext:
                        AverageVelocity = (Velocity + TargetSpeedNext) * 0.5
                        TimeToDecel = math.ceil((Velocity - TargetSpeedNext) / decel)
                        TimeToCoverDistance = ((SegDistance - CurDistance) / AverageVelocity) * 3600.0
                        if (TimeToDecel + 1) > TimeToCoverDistance:
                            DecelRate = (Velocity - TargetSpeedNext) / TimeToCoverDistance
                            DecelRate = min(DecelRate, decel)
                            NextVelocity = max(Velocity - DecelRate, TargetSpeedNext)
                            DecelSeconds = TimeToDecel - 1
                            if 0.0 < DecelRate:
                                DecelSeconds = min(DecelSeconds, int(math.ceil((Velocity - TargetSpeedNext) / decel)))
                            Decellerating = True
                    elif (Velocity == TargetSpeedNext) and ((Velocity/1800.0) > (SegDistance - CurDistance)):
                        DecelSeconds = 2
                        Decellerating = True
                        DecelRate = 0.0
                    CurDistance += (Velocity + NextVelocity) * 0.5 / 3600.0
                    if NextVelocity < 0.0:
                        print(path)
                        print(CurInter)
                        print("NextVelocity", NextVelocity, "Velocity ",Velocity, "PrevSpeedLimit", PrevSpeedLimit, "CurAccel", CurAccel, "accel", accel, "SecondsToAccel", SecondsToAccel)
                        print("TargetSpeedNext", TargetSpeedNext, "Decellerating", Decellerating, "DecelRate", DecelRate, "DecelSeconds", DecelSeconds)
                        H = h
                    
                    Velocity = NextVelocity
                    SpeedTrace.append(Velocity)
                    
                for Index in range(0,TimeAtInter):
                    SpeedTrace.append(Velocity)
                    
            SegDistance = self.DistanceDB[(CurInter, NextInter)]
            PrevSpeedLimit = NextSpeedLimit
            TruePrevSpeedLimit = TrueNextSpeedLimit
            PrevInter = CurInter
            CurInter = NextInter
        TargetSpeedNext = 0.0
        CurDistance = 0.0
        Decellerating = False
        while CurDistance < SegDistance:
            SecondsToAccel = math.ceil((PrevSpeedLimit - Velocity) / accel)
            CurAccel = accel
            if 0.0 < SecondsToAccel:
                CurAccel = (PrevSpeedLimit - Velocity) / SecondsToAccel
            if (TruePrevSpeedLimit > PrevSpeedLimit) or (((Velocity + decel)/3600.0) > (SegDistance - CurDistance)):
                MaxRandomSpeed = PrevSpeedLimit
            else:
                MaxRandomSpeed = round(PrevSpeedLimit + random.random() * 2.01 - 1.0)
            MaxRandomSpeed = max(1.0, MaxRandomSpeed)    
            NextVelocity = min(Velocity + CurAccel, MaxRandomSpeed)
            if Decellerating:
                if 0 < DecelSeconds:
                    #DecelRate = (Velocity - TargetSpeedNext) / TimeToDecel
                    NextVelocity = max(Velocity - DecelRate, TargetSpeedNext)
                    DecelSeconds = DecelSeconds - 1
                else:
                    NextVelocity = TargetSpeedNext
                    CurDistance = SegDistance
            elif Velocity > TargetSpeedNext:
                AverageVelocity = (Velocity + TargetSpeedNext) * 0.5
                TimeToDecel = math.ceil((Velocity - TargetSpeedNext) / decel)
                TimeToCoverDistance = ((SegDistance - CurDistance) / AverageVelocity) * 3600.0
                if (TimeToDecel + 1) > TimeToCoverDistance:
                    DecelRate = (Velocity - TargetSpeedNext) / TimeToCoverDistance
                    DecelRate = min(DecelRate, decel)
                    NextVelocity = max(Velocity - DecelRate, TargetSpeedNext)
                    DecelSeconds = TimeToDecel - 1
                    if 0.0 < DecelRate:
                        DecelSeconds = min(DecelSeconds, int(math.ceil((Velocity - TargetSpeedNext) / decel)))
                    Decellerating = True
                    
            CurDistance += (Velocity + NextVelocity) * 0.5 / 3600.0
            Velocity = NextVelocity
            if 0.0 > Velocity and not Decellerating:
                print(path)
                print("NextVelocity", NextVelocity, "Velocity ",Velocity, "PrevSpeedLimit", PrevSpeedLimit, "CurAccel", CurAccel, "accel", accel, "SecondsToAccel", SecondsToAccel)
                print("TargetSpeedNext", TargetSpeedNext, "Decellerating", Decellerating, "DecelRate", DecelRate, "DecelSeconds", DecelSeconds)
                J = j
            SpeedTrace.append(Velocity)
        for Index in range(0,2):
            SpeedTrace.append(Velocity)
        return SpeedTrace


#InputFile = 'streetmap.csv' #input("Enter filename: ")
#CityMap = StreetMap(InputFile)
#CityMap.AddNode('S1','P3','P5',0.5)
#
#print(CityMap.PointDB)     
#print(CityMap.StreetDB)
#print(CityMap.EdgeList)

#CityMap.CalculateAllBestPathsToDestination('P9')
#
#print(CityMap.ShortestPathDB[('P51','P9')])
#print(CityMap.PathToStreetNames(CityMap.ShortestPathDB[('P51','P9')]), CityMap.CalculateTimePath(CityMap.ShortestPathDB[('P51','P9')]))
#print(CityMap.FastestPathDB[('P51','P9')])
#print(CityMap.PathToStreetNames(CityMap.FastestPathDB[('P51','P9')]), CityMap.CalculateTimePath(CityMap.FastestPathDB[('P51','P9')]))
#
#Trace = CityMap.GenerateSpeedTrace(CityMap.FastestPathDB[('P51','P9')], 4.0, 5.0) 
#print(Trace, len(Trace))


