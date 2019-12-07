#
# TTP 210 
#
import csv
import math
import glob
import os
from streetmap import *
from ttputils import *

class BusRoute:    
    def __init__(self, strmap, anchor):
        self.StreetMap = strmap
        self.RouteAnchor = anchor
        self.MaxAcceleration = 2.0
        self.MaxDeceleration = 4.0
        self.RouteName = ''
        self.BusType = ''
        self.RoutePath = []
        self.RouteTimes = []
        self.RouteStartTimes = [] 
        self.RouteDuration = [] 

    def CopyRoute(self, oldroute):
        self.BusType = oldroute.BusType
        self.StreetMap = oldroute.StreetMap
        self.RouteAnchor = oldroute.RouteAnchor
        self.MaxAcceleration = oldroute.MaxAcceleration
        self.MaxDeceleration = oldroute.MaxDeceleration
        self.RoutePath = list(oldroute.RoutePath)
        self.RouteTimes = list(oldroute.RouteTimes)
        self.RouteStartTimes = list(oldroute.RouteStartTimes)
        self.RouteDuration = list(oldroute.RouteDuration)

    def Load(self, filename):
        self.RoutePath = []
        self.RouteTimes = []
        self.RouteStartTimes = []
        with open(filename, 'rU') as RouteFile:
            RouteFileReader = csv.reader(RouteFile, delimiter=',')
            Row = next(RouteFileReader)
            self.RouteName = Row[0]
            Row = next(RouteFileReader)
            self.BusType = Row[0]
            Row = next(RouteFileReader)
            for Location in Row:
                if 0 < len(Location):
                    if not Location in self.StreetMap.PointDB:
                        return False
                    self.RoutePath.append(Location)
            Row = next(RouteFileReader)
            for StartTime in Row:
                if not IsInt(StartTime):
                    break
                self.RouteStartTimes.append(int(StartTime))
            self.CalculateDurationTimes()
            self.CalculateRouteTimes()
            return True

    def Save(self, filename):
        OutputFile = open(filename, 'w', newline='')
        RouteFileWriter = csv.writer(OutputFile, quoting=csv.QUOTE_ALL)
        TempList = [self.RouteName]
        RouteFileWriter.writerow(TempList)
        TempList = [self.BusType]
        RouteFileWriter.writerow(TempList)
        TempList = self.RoutePath
        RouteFileWriter.writerow(TempList)
        TempList = self.RouteStartTimes
        RouteFileWriter.writerow(TempList)
        OutputFile.close()
        
    def AddStop(self, stopname):
        if not stopname in self.StreetMap.PointDB:
            return False
        self.RoutePath.append(stopname)
        self.CalculateDurationTimes()
        self.CalculateRouteTimes()
        return True
        
    def RemoveStop(self, stopname):
        if not stopname in self.RoutePath:
            return False
        self.RoutePath.remove(stopname)
        self.CalculateDurationTimes()
        self.CalculateRouteTimes()
        return True

    def ReverseStops(self):
        self.RoutePath = self.RoutePath[::-1]
        self.CalculateDurationTimes()
        self.CalculateRouteTimes()
        return True
        
    def AddStartTime(self, starttime):
        if starttime in self.RouteStartTimes:
            return False
        self.RouteStartTimes.append(starttime)
        self.RouteStartTimes.sort()
        self.CalculateRouteTimes()
        return True
        
    def RemoveStartTime(self, starttime):
        if not starttime in self.RouteStartTimes:
            return False
        self.RouteStartTimes.remove(starttime)
        self.CalculateRouteTimes()
        return True
    
    def CalculateFullPath(self):  
        FullPath = []
        if(0 != len(self.RoutePath)):
            LastStop = self.RouteAnchor   
            FullPath = [LastStop]
            for CurrentStop in self.RoutePath:
                Path = self.StreetMap.FindShortestPath(LastStop, CurrentStop)
                FullPath.extend(Path[1:])
                LastStop = CurrentStop
            Path = self.StreetMap.FindShortestPath(LastStop, self.RouteAnchor)
            FullPath.extend(Path[1:])
        return FullPath
    
    def CalculateDurationTimes(self):  
        self.RouteDuration = []
        if(0 != len(self.RoutePath)):
            LastStop = self.RouteAnchor    
            for CurrentStop in self.RoutePath:
                Path = self.StreetMap.FindShortestPath(LastStop, CurrentStop)
                SegmentTime = int(math.ceil(self.StreetMap.CalculateTimePath(Path, self.MaxAcceleration, self.MaxDeceleration)))
                self.RouteDuration.append(SegmentTime)
                LastStop = CurrentStop
            Path = self.StreetMap.FindShortestPath(LastStop, self.RouteAnchor)
            SegmentTime = int(math.ceil(self.StreetMap.CalculateTimePath(Path, self.MaxAcceleration, self.MaxDeceleration)))
            self.RouteDuration.append(SegmentTime) 
        
    def CalculateRouteTimes(self):
        self.RouteTimes = []
        for StartTime in self.RouteStartTimes:
            CurrentRoute = [StartTime]
            for Duration in self.RouteDuration:
                CurrentRoute.append(CurrentRoute[-1] + Duration + 15)
            self.RouteTimes.append(tuple(CurrentRoute))

class BusStops:
    def __init__(self, strmap):
        self.StreetMap = strmap
        self.StopNames = []
        self.StopDB = {}

    def Load(self, filename):
        self.StopNames = []
        self.StopDB = {}
        with open(filename, 'rU') as StopFile:
            StopFileReader = csv.reader(StopFile, delimiter=',')
            Row = next(StopFileReader)
            StopCount = int(Row[0])
            for CurrentStop in range(0,StopCount):
                Row = next(StopFileReader)
                if 5 > len(Row):
                    return False
                Intersection1 = self.StreetMap.FindIntersectionPoint(Row[1], Row[2])
                if 0 == len(Intersection1):
                    return False
                Intersection2 = self.StreetMap.FindIntersectionPoint(Row[1], Row[3])
                if 0 == len(Intersection2):
                    return False
                if not IsFloat(Row[4]):
                    return False
                Distance = float(Row[4])
                if not self.StreetMap.AddNode(Row[0], Intersection1, Intersection2, Distance):
                    return False
                
                self.StopDB[Row[0]] = tuple(Row[1:])
                self.StopNames.append(Row[0])
            return True

    def Save(self, filename):
        OutputFile = open(filename, 'w', newline='')
        StopFileWriter = csv.writer(OutputFile, quoting=csv.QUOTE_ALL)
        TempList = [len(self.StopNames)]
        StopFileWriter.writerow(TempList)
        for StopName in self.StopNames:
            TempList = [StopName]
            TempList.extend(list(self.StopDB[StopName]))
            StopFileWriter.writerow(list(TempList))

        OutputFile.close()

    def AddStop(self, name, street, intsect1, intsect2, dist):
        Intersection1 = self.StreetMap.FindIntersectionPoint(street, intsect1)
        if 0 == len(Intersection1):
            return False
        Intersection2 = self.StreetMap.FindIntersectionPoint(street, intsect2)
        if 0 == len(Intersection2):
            return False
        if not self.StreetMap.AddNode(name, Intersection1, Intersection2, dist):
            return False
        self.StopDB[name] = (street, intsect1, intsect2, dist)
        self.StopNames.append(name)
        return True
        
    def RemoveStop(self, name):
        if not name in self.StopDB:
            return False
        if not name in self.StopNames:
            print(self.StopNames)
            return False
        if not self.StreetMap.RemoveNode(name):
            return False
        del self.StopDB[name]
        self.StopNames.remove(name)
        return True

    def DistanceToStops(self, location):
        StopDistances = []
        for CurStop in self.StopNames:
            DestPoint = self.StreetMap.PointDB[CurStop]
            StopDistances.append( (CalculateDistancePoint(location, DestPoint), CurStop) )
        return StopDistances

class BusSchedule:
    def __init__(self, stops, routes, maxdist, starttime, endtime, vehicles):
        self.BusStops = stops
        self.StreetMap = stops.StreetMap
        self.BusRoutes = routes
        self.MaxDistance = maxdist
        self.ArrivalRouteInfo = {}
        self.DepartureRouteInfo = {}
        self.ArrivalLoop = {}
        self.DepartureLoop = {}
        self.LineOccupancy = {}
        self.LoopIndices = {}
        self.Ridership = {}
        
        for CurRoute in self.BusRoutes:
            self.LineOccupancy[CurRoute] = int(vehicles.GetParameter(self.BusRoutes[CurRoute].BusType,'Capacity'))
            LoopIndex = 0
            for LoopTimes in self.BusRoutes[CurRoute].RouteTimes: 
                StopIndex = 1
                for StopName in self.BusRoutes[CurRoute].RoutePath:
                    self.LoopIndices[(CurRoute, StopName, LoopTimes[StopIndex])] = LoopIndex
                    StopIndex = StopIndex + 1
                for CurHour in range(starttime, endtime+1):
                    TimeInSeconds = CurHour * 3600
                    if LoopTimes[-1] <= TimeInSeconds:
                        Index = 1
                        for CurStop in self.BusRoutes[CurRoute].RoutePath:
                            if (TimeInSeconds - LoopTimes[Index]) < 7200:
                                if (CurHour, CurStop) in self.ArrivalRouteInfo:
                                    self.ArrivalRouteInfo[(CurHour, CurStop)].append( (LoopTimes[Index], self.BusRoutes[CurRoute].RouteName) )
                                else:
                                    self.ArrivalRouteInfo[(CurHour, CurStop)] = [ (LoopTimes[Index], self.BusRoutes[CurRoute].RouteName) ]
                            Index = Index + 1
                        if (self.BusRoutes[CurRoute].RouteName, CurHour) in self.ArrivalLoop:
                            self.ArrivalLoop[(self.BusRoutes[CurRoute].RouteName, CurHour)].append(LoopIndex)
                        else:
                            self.ArrivalLoop[(self.BusRoutes[CurRoute].RouteName, CurHour)]= [LoopIndex]
                    if LoopTimes[0] >= TimeInSeconds:
                        Index = 1
                        for CurStop in self.BusRoutes[CurRoute].RoutePath:
                            if (LoopTimes[Index] - TimeInSeconds) < 7200:
                                if (CurHour, CurStop) in self.DepartureRouteInfo:
                                    self.DepartureRouteInfo[(CurHour, CurStop)].append( (LoopTimes[Index], self.BusRoutes[CurRoute].RouteName) )
                                else:
                                    self.DepartureRouteInfo[(CurHour, CurStop)] = [ (LoopTimes[Index], self.BusRoutes[CurRoute].RouteName) ]
                            Index = Index + 1
                        if (self.BusRoutes[CurRoute].RouteName, CurHour) in self.DepartureLoop:
                            self.DepartureLoop[(self.BusRoutes[CurRoute].RouteName, CurHour)].append(LoopIndex)
                        else:
                            self.DepartureLoop[(self.BusRoutes[CurRoute].RouteName, CurHour)]= [LoopIndex]
                LoopIndex = LoopIndex + 1            
        for ArrivalCombo in self.ArrivalRouteInfo:
            self.ArrivalRouteInfo[ArrivalCombo].sort(reverse=True)
        for DepartureCombo in self.DepartureRouteInfo:
            self.DepartureRouteInfo[DepartureCombo].sort()

    def ClosestStops(self, location):
        StopAndDistanceList = self.BusStops.DistanceToStops(location)
        StopAndDistanceList.sort()
        ReturnStops = []
        for CurStop in StopAndDistanceList:
            if CurStop[0] <= self.MaxDistance:
                ReturnStops.append(CurStop)
            else:
                break
        return ReturnStops
        
    def RouteOptionsToStation(self, location, arrivaltime):
        AvailableStops = self.ClosestStops(location)
        Options = []
        for CurStop in AvailableStops:
            if (arrivaltime, CurStop[1]) in self.ArrivalRouteInfo:
               LeaveTimes = self.ArrivalRouteInfo[(arrivaltime, CurStop[1]) ]
               for LeaveTime in LeaveTimes:
                   Options.append( (LeaveTime[0], CurStop, LeaveTime[1]))
                   
        return Options
        
    def RouteOptionsFromStation(self, location, departuretime):
        AvailableStops = self.ClosestStops(location)
        Options = []
        for CurStop in AvailableStops:
            if (departuretime, CurStop[1]) in self.DepartureRouteInfo:
               LeaveTimes = self.DepartureRouteInfo[(departuretime, CurStop[1]) ]
               for LeaveTime in LeaveTimes:
                   Options.append( (LeaveTime[0], CurStop, LeaveTime[1]))
                   
        return Options
        
    def BusNeededForRiderToStation(self, busline, onstop, ontime): 
        LoopIndex = self.LoopIndices[(busline, onstop, ontime)]
        StopIndex = len(self.BusRoutes[busline].RoutePath) - self.BusRoutes[busline].RoutePath[::-1].index(onstop) 
        if not (busline, LoopIndex) in self.Ridership:
            Riders = [0]
            for StopName in self.BusRoutes[busline].RoutePath:
                Riders.append(0)
            Riders.append(0)
            self.Ridership[(busline, LoopIndex)] = Riders
        RiderList = self.Ridership[(busline, LoopIndex)]
        MaxRidersWithout = max(RiderList)
        MaxRidersWith = MaxRidersWithout
        for Index in range(StopIndex, len(RiderList)):
            MaxRidersWith = max(RiderList[Index] + 1, MaxRidersWith)
        BusesWithout = max(1,(MaxRidersWithout + self.LineOccupancy[busline] - 1) / self.LineOccupancy[busline])
        BusesWith = max(1,(MaxRidersWith + self.LineOccupancy[busline] - 1) / self.LineOccupancy[busline])
        return (BusesWith, BusesWithout)
            
    def AddRiderToStation(self, busline, onstop, ontime):
        LoopIndex = self.LoopIndices[(busline, onstop, ontime)]
        StopIndex = len(self.BusRoutes[busline].RoutePath) - self.BusRoutes[busline].RoutePath[::-1].index(onstop) 
        if not (busline, LoopIndex) in self.Ridership:
            Riders = [0]
            for StopName in self.BusRoutes[busline].RoutePath:
                Riders.append(0)
            Riders.append(0)
            self.Ridership[(busline, LoopIndex)] = Riders
        RiderList = self.Ridership[(busline, LoopIndex)]
        for Index in range(StopIndex, len(RiderList)):
            RiderList[Index] = RiderList[Index] + 1
    
    def BusNeededForRiderFromStation(self, busline, offstop, offtime):
        LoopIndex = self.LoopIndices[(busline, offstop, offtime)]
        StopIndex = self.BusRoutes[busline].RoutePath.index(offstop) + 1 
        if not (busline, LoopIndex) in self.Ridership:
            Riders = [0]
            for StopName in self.BusRoutes[busline].RoutePath:
                Riders.append(0)
            Riders.append(0)
            self.Ridership[(busline, LoopIndex)] = Riders
        RiderList = self.Ridership[(busline, LoopIndex)]
        MaxRidersWithout = max(RiderList)
        MaxRidersWith = MaxRidersWithout
        for Index in range(0, StopIndex):
            MaxRidersWith = max(RiderList[Index] + 1, MaxRidersWith)
        BusesWithout = max(1,(MaxRidersWithout + self.LineOccupancy[busline] - 1) / self.LineOccupancy[busline])
        BusesWith = max(1,(MaxRidersWith + self.LineOccupancy[busline] - 1) / self.LineOccupancy[busline])
        return (BusesWith, BusesWithout)
        
    def AddRiderFromStation(self, busline, offstop, offtime):
        LoopIndex = self.LoopIndices[(busline, offstop, offtime)]
        StopIndex = self.BusRoutes[busline].RoutePath.index(offstop) + 1 
        if not (busline, LoopIndex) in self.Ridership:
            Riders = [0]
            for StopName in self.BusRoutes[busline].RoutePath:
                Riders.append(0)
            Riders.append(0)
            self.Ridership[(busline, LoopIndex)] = Riders
        RiderList = self.Ridership[(busline, LoopIndex)]
        for Index in range(0, StopIndex):
            RiderList[Index] = RiderList[Index] + 1
            
    def GetArrivalLoops(self, hour):
        ReturnBusLoops = []
        for Loops in self.ArrivalLoop:
            if Loops[1] == hour:
                ReturnBusLoops.append((Loops[0],self.ArrivalLoop[Loops]))
        return ReturnBusLoops
        
    def GetDepartureLoops(self, hour):
        ReturnBusLoops = []
        for Loops in self.DepartureLoop:
            if Loops[1] == hour:
                ReturnBusLoops.append((Loops[0],self.DepartureLoop[Loops]))
        return ReturnBusLoops
        
    def GenerateDriveTrace(self, busline):
        ColdTrace = []
        HotTrace = []
        BusCounts = []
        if busline in self.BusRoutes:
            MaxRidership = 0
            WorstCapacity = []
            AverageCapacity = []
            WorstBusCount = 0
            AverageBusCount = 0
            RouteTimesForDivision = max(len(self.BusRoutes[busline].RouteTimes), 1)
            for StopIndex in range(0,len(self.BusRoutes[busline].RoutePath) + 2):
                AverageCapacity.append(0)
                WorstCapacity.append(0)
            for LoopIndex in range(0,len(self.BusRoutes[busline].RouteTimes)):
                if (busline, LoopIndex) in self.Ridership:
                    StopIndex = 0
                    for Occupancy in self.Ridership[(busline, LoopIndex)]:
                        AverageCapacity[StopIndex] += Occupancy
                        StopIndex = StopIndex + 1
                    CurBusCount = int(max(1,(max(self.Ridership[(busline, LoopIndex)]) + self.LineOccupancy[busline] - 1) / self.LineOccupancy[busline]))
                    BusCounts.append(CurBusCount)
                    AverageBusCount += CurBusCount
                    if MaxRidership < max(self.Ridership[(busline, LoopIndex)]):
                        MaxRidership = max(self.Ridership[(busline, LoopIndex)])
                        WorstCapacity = list(self.Ridership[(busline, LoopIndex)])
                        WorstBusCount = max(1,(MaxRidership + self.LineOccupancy[busline] - 1) / self.LineOccupancy[busline])
                else:
                    BusCounts.append(1)
            AverageBusCount = AverageBusCount / RouteTimesForDivision
            StopIndex = 0
            for Occupancy in AverageCapacity:
                AverageCapacity[StopIndex] = Occupancy / RouteTimesForDivision
                AverageCapacity[StopIndex] = min(AverageCapacity[StopIndex], self.LineOccupancy[busline])
                StopIndex = StopIndex + 1    
            StopIndex = 0
            for Occupancy in WorstCapacity:
                if 0 < Occupancy:
                    WorstCapacity[StopIndex] = Occupancy / WorstBusCount
                StopIndex = StopIndex + 1 
            StopIndex = 0
            LastStop = self.BusRoutes[busline].RouteAnchor
            for CurStop in self.BusRoutes[busline].RoutePath:
                ShortestPath = self.StreetMap.FindShortestPath(LastStop, CurStop)
                CapacityRatio = float(WorstCapacity[StopIndex]) / float(self.LineOccupancy[busline])
                AccelRatio = 1.0 - 0.9 * CapacityRatio
                SegTrace = self.StreetMap.GenerateSpeedTrace(ShortestPath, self.BusRoutes[busline].MaxAcceleration * AccelRatio, self.BusRoutes[busline].MaxDeceleration)
                ColdTrace.append((WorstCapacity[StopIndex],SegTrace))
                CapacityRatio = float(AverageCapacity[StopIndex]) / float(self.LineOccupancy[busline])
                AccelRatio = 1.0 - 0.9 * CapacityRatio
                SegTrace = self.StreetMap.GenerateSpeedTrace(ShortestPath, self.BusRoutes[busline].MaxAcceleration * AccelRatio, self.BusRoutes[busline].MaxDeceleration)
                HotTrace.append((AverageCapacity[StopIndex],SegTrace))
                LastStop = CurStop
                StopIndex = StopIndex + 1
            ShortestPath = self.StreetMap.FindShortestPath(LastStop, self.BusRoutes[busline].RouteAnchor)
            SegTrace = self.StreetMap.GenerateSpeedTrace(ShortestPath, self.BusRoutes[busline].MaxAcceleration, self.BusRoutes[busline].MaxDeceleration)
            ColdTrace.append((WorstCapacity[StopIndex],SegTrace))
            SegTrace = self.StreetMap.GenerateSpeedTrace(ShortestPath, self.BusRoutes[busline].MaxAcceleration, self.BusRoutes[busline].MaxDeceleration)
            HotTrace.append((AverageCapacity[StopIndex],SegTrace))
            StopIndex = StopIndex + 1
                
        return (ColdTrace, HotTrace, BusCounts)                
                
                
