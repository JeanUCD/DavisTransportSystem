#
#   TTP 210 Utility Functions
#
import math
from operator import itemgetter, attrgetter, methodcaller

# Funciton to determine if string can be converted to float
def IsFloat(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

# Funciton to determine if string can be converted to int
def IsInt(string):
    try:
        int(string)
        return True
    except ValueError:
        return False

# Function to convert RPM and torque to power
def RotationalPower(rpm, nm):
    return rpm * nm * 2 * math.pi / 60.0

# Function to convert Power and RPM to Torque
def RotationalTorque(power, rpm):
    return power / (rpm * 2 * math.pi / 60.0)

# Function to convert Power (W) and Time to Wh
def PowerTimeToWh(power,time):
    return power * ConvertSecondsToHours(time)

# Function to convert Power (W) and Time to kWh
def PowerTimeTokWh(power,time):
    return (power / 1000.0) * ConvertSecondsToHours(time)

# Function to convert Power (W) to (kW)
def ConvertWTokW(power):
    return power / 1000.0

# Function to convert Power (kW) to (W)
def ConvertkWToW(power):
    return power * 1000.0

# Function to convert Energy (J) to (kWh)
def ConvertJTokWh(energy):
    return energy / 3.6e6

# Function to convert Energy (kWh) to (J)
def ConvertkWhToJ(energy):
    return energy * 3.6e6

# Function to convert miles per hour to meters per second
def ConvertMPHToMPS(speed):
    return speed * 0.44704

# Function to convert meters per second to miles per hour
def ConvertMPSToMPH(speed):
    return speed * 2.2369362920544
    
# Function to convert meters to miles
def ConvertMetersToMiles(distance):
    return distance * 0.00062137119

# Function to convert miles to meters
def ConvertMilesToMeters(distance):
    return distance * 1609.344

# Function to convert seconds to hours
def ConvertSecondsToHours(time):
    return time / 3600.0

# Function to convert hours to seconds
def ConvertHoursToSeconds(time):
    return time * 3600.0

# Function to convert celcius to kelvin
def ConvertCToK(temp):
    return temp + 273.15

# Function to convert kelvin to celcius
def ConvertKToC(temp):
    return temp - 273.15

# Function to convert farenheit to kelvin
def ConvertFToK(temp):
    return ((temp - 32.0) * 5.0 / 9.0) + 273.15

# Function to convert kelvin to farenheit
def ConvertKToF(temp):
    return ((temp - 273.15) * 1.8) + 32.0

# Function to get gravity constant
def ConstantGravity():
    return 9.80665          # m/s^2
    
# Funciton to get standard air density
def ConstantAirDensity():
    return 1.3              # kg/m^3

# Funciton to get standard air density
def ConstantRinJmolK():
    return 8.3145           # J/mol K

# Function to convert volume to radius
def ConvertVolumeToRadius(volume):
    return ((volume * 0.75) / math.pi)**(1.0/3.0)

# Function to convert Liters to cm3
def ConvertLTocm3(volume):
    return (volume * 1000.0)

# Function to convert Liters to cm3
def Convertcm3ToL(volume):
    return (volume / 1000.0)

# Function to solve distance between two points
def CalculateDistance(x1, y1, x2, y2):
    DeltaX = x1 - x2
    DeltaY = y1 - y2
    return math.sqrt((DeltaX * DeltaX) + (DeltaY * DeltaY))

# Function to solve distance between two points
def CalculateDistancePoint(src, dest):
    return CalculateDistance(src[0],src[1],dest[0],dest[1])

# Function to solve M and B for line given two points
def LineCalculateMB(x1, y1, x2, y2):
    M = (y2 - y1)/(x2 - x1)
    B = y1 - M * x1
    return (M, B)

def CalculateDistanceFromLine(seg1, seg2, pt):
    return abs((seg2[1] - seg1[1])*pt[0] - (seg2[0]-seg1[0])*pt[1] + seg2[0]*seg1[1] - seg2[1]*seg1[0]) / math.sqrt( (seg2[1] - seg1[1])**2 +  (seg2[0] - seg1[0])**2)

# Function to calculate distance between point and segment
def SegmentPointCalculateDistance(seg1,seg2,pt):
    DistEnds = min(CalculateDistancePoint(seg1,pt),CalculateDistancePoint(seg2,pt))
    
    # if vertical line
    if seg1[0] == seg2[0]:
        if (seg1[1] <= pt[1]) and (pt[1] <= seg2[1]):
            return abs(pt[0] - seg1[0])
        elif (seg1[1] >= pt[1]) and (pt[1] >= seg2[1]):
            return abs(pt[0] - seg1[0])
        else:
            return DistEnds
    # else if horizontal line
    elif seg1[1] == seg2[1]:
        if (seg1[0] <= pt[0]) and (pt[0] <= seg2[0]):
            return abs(pt[1] - seg1[1])
        elif (seg1[0] >= pt[0]) and (pt[0] >= seg2[0]):
            return abs(pt[1] - seg1[1])
        else:
            return DistEnds
    else:
        MBSeg = LineCalculateMB(seg1[0],seg1[1],seg2[0],seg2[1])
        MBTan = (-1.0/MBSeg[0], pt[1] + (1.0/MBSeg[0]) * pt[0] )
        InterX = (MBSeg[1]-MBTan[1])/(MBTan[0]-MBSeg[0])
        InterY = InterX * MBTan[0] + MBTan[1]
        if (seg1[0] <= InterX) and (InterX <= seg2[0]):
            return CalculateDistancePoint(pt, (InterX, InterY))
        elif (seg1[0] >= InterX) and (InterX >= seg2[0]):
            return CalculateDistancePoint(pt, (InterX, InterY))
        else:
            return DistEnds

# Function to calculate nearest on segment to another point
def SegmentPointCalculateNearest(seg1,seg2,pt):
    DistEnds = min(CalculateDistancePoint(seg1,pt),CalculateDistancePoint(seg2,pt))
    
    # if vertical line
    if seg1[0] == seg2[0]:
        MinY = min(seg1[1], seg2[1])
        MaxY = max(seg1[1], seg2[1])
        if (MinY <= pt[1]) and (pt[1] <= MaxY):
            return (seg1[0], pt[1])
        elif MinY > pt[1]:
            return (seg1[0], MinY)
        else:
            return (seg1[0], MaxY)
    # else if horizontal line
    elif seg1[1] == seg2[1]:
        MinX = min(seg1[0], seg2[0])
        MaxX = max(seg1[0], seg2[0])
        if (MinX <= pt[0]) and (pt[0] <= MaxX):
            return (pt[0], seg1[1])
        elif MinX > pt[0]:
            return (MinX, seg1[1])
        else:
            return (MaxX, seg1[1])
    else:
        MinX = min(seg1[0], seg2[0])
        MaxX = max(seg1[0], seg2[0])
        MBSeg = LineCalculateMB(seg1[0],seg1[1],seg2[0],seg2[1])
        MBTan = (-1.0/MBSeg[0], pt[1] + (1.0/MBSeg[0]) * pt[0] )
        InterX = (MBSeg[1]-MBTan[1])/(MBTan[0]-MBSeg[0])
        InterY = InterX * MBTan[0] + MBTan[1]
        if (MinX <= InterX) and (InterX <= MaxX):
            return (InterX, InterY)
        return seg1 if CalculateDistancePoint(seg1, (InterX, InterY)) < CalculateDistancePoint(seg2, (InterX, InterY)) else seg2
            
# Function to calculate nearest point on segment and return percent between seg1 & 2
def SegmentPointCalculateNearestPercent(seg1,seg2,pt):
    # if vertical line
    if seg1[0] == seg2[0]:
        MinY = min(seg1[1], seg2[1])
        MaxY = max(seg1[1], seg2[1])
        if (MinY <= pt[1]) and (pt[1] <= MaxY):
            return (pt[1] - seg1[1]) / (seg2[1] - seg1[1])
        elif MinY > pt[1]:
            return 0.0 if MinY == seg1[0] else 1.0
        else:
            return 0.0 if MaxY == seg1[0] else 1.0
    # else if horizontal line
    elif seg1[1] == seg2[1]:
        MinX = min(seg1[0], seg2[0])
        MaxX = max(seg1[0], seg2[0])
        if (MinX <= pt[0]) and (pt[0] <= MaxX):
            return (pt[0] - seg1[0]) / (seg2[0] - seg1[0])
        elif MinX > pt[0]:
            return 0.0 if MinX == seg1[0] else 1.0
        else:
            return 0.0 if MaxX == seg1[0] else 1.0
    else:
        MinX = min(seg1[0], seg2[0])
        MaxX = max(seg1[0], seg2[0])
        MBSeg = LineCalculateMB(seg1[0],seg1[1],seg2[0],seg2[1])
        MBTan = (-1.0/MBSeg[0], pt[1] + (1.0/MBSeg[0]) * pt[0] )
        InterX = (MBSeg[1]-MBTan[1])/(MBTan[0]-MBSeg[0])
        InterY = InterX * MBTan[0] + MBTan[1]
        if (MinX <= InterX) and (InterX <= MaxX):
            return (InterX - seg1[0]) / (seg2[0] - seg1[0])
        return 0.0 if CalculateDistancePoint(seg1, (InterX, InterY)) < CalculateDistancePoint(seg2, (InterX, InterY)) else 1.0

def CalculatePointLocation(src, dest, dist):
    # if vertical line
    if src[0] == dest[0]:
        return (src[0], src[1] + (dest[1] - src[1]) * dist) 
    else:
        MB = LineCalculateMB(src[0],src[1],dest[0],dest[1])
        X = src[0] + ((dest[0] - src[0]) * dist)
        return (X, MB[0] * X + MB[1])

# Solve the quadratic equation, return tuple of solutions
def QuadraticEquation(a, b, c):
    if(a == 0.0):
        if(b == 0.0):
            return ()
        RetVal = -c/b
        return (RetVal,)
    UnderSquareRt = b**2 - 4 * a * c
    if(UnderSquareRt == 0.0):
        return ((-b/(2 * a)),)
    elif(UnderSquareRt < 0.0):
        return ()
    else:
        UnderSquareRt = math.sqrt(UnderSquareRt)
        PlusVal = (-b + UnderSquareRt)/(2 * a)
        MinusVal =(-b - UnderSquareRt)/(2 * a)
        return (PlusVal, MinusVal)


# Cuberoot and PolyCubicRoots from:
# author  Dr. Ernesto P. Adorio
#		 University of the Philippines at Clarkfield, Pampanga
# version 2010.01.01  first version
#		 2013.01.11  debugged version.

def Cuberoot(x):
	if x >= 0:
	   return x**(1/3.0)
	else: # negative argument!
	   return -(-x)**(1/3.0)
 
def PolyCubicRoots(a, b, c):
    #print "input=", a,b,c
    aby3 = a / 3.0
    p = b - a*aby3
    q = (2*aby3**2- b)*(aby3) + c
    X =(p/3.0)**3
    Y = (q/2.0)**2
    Q = X + Y
    #print "Q=", Q
    if Q >= 0:
        sqQ = math.sqrt(Q)
        # Debug January 11, 2013. Thanks to a reader!
        t = (-q/2.0 + sqQ)
        A = Cuberoot(t)
        t = (-q/2.0 - sqQ)
        B = Cuberoot(t)
        
        r1 = A + B- aby3
        re = -(A+B)/2.0-aby3
        im = math.sqrt(3.0)/2.0*(A-B)
        r2 = (re,im)
        r3 = (re,-im)
    else:
        # This part has been tested.
        p3by27= math.sqrt(-p**3/27.0)
        costheta = -q/2.0/ p3by27
        #print "@@@ costheta=", costheta
        alpha = math.acos(costheta)
        mag = 2 * math.sqrt(-p/3.0)
        alphaby3 = alpha/3.0
        r1 = mag  * math.cos(alphaby3) - aby3
        r2 = -mag * math.cos(alphaby3+ math.pi/3)-aby3
        r3 = -mag * math.cos(alphaby3- math.pi/3) -aby3
    return (r1, r2, r3)

# Do interpolation based on x value lookup for y value
def Interpolate(x, xvals, yvals):
    if(x < xvals[0]):
        return yvals[0]
        
    for Index in range(1,len(xvals)):
        if((xvals[Index-1] <= x)and(x <= xvals[Index])):
            return yvals[Index-1] + (yvals[Index] - yvals[Index - 1])*(x - xvals[Index-1])/(xvals[Index] - xvals[Index -1])
        Index = Index + 1
    return yvals[-1]

# Cubic interpolation based on four values [0, 1]
def CubicInterpolation(p, x):
    return p[1] + 0.5 * x*(p[2] - p[0] + x*(2.0*p[0] - 5.0*p[1] + 4.0*p[2] - p[3] + x*(3.0*(p[1] - p[2]) + p[3] - p[0])))

# Bicubic interpolation based on 4x4 grid ([0, 1], [0, 1])
def BicubicToCubicInterpolation(p, x):
    Parameters = []
    for Index in range(0, 4):
        Parameters.append(CubicInterpolation(p[Index], x))
    return Parameters
    
def BicubicInterpolation(p, x, y):
    return CubicInterpolation(BicubicToCubicInterpolation(p, y), x)

def BicubicInterpolation2(p, x, y):
    PTrans = list(map(list, zip(*p))) 
    return CubicInterpolation(BicubicToCubicInterpolation(Parameters, x), y)

def CubicInterpolationIntersections(p, val):
    A = 0.5*(3.0*(p[1] - p[2]) + p[3] - p[0])
    B = 0.5*(2.0*p[0] - 5.0*p[1] + 4.0*p[2] - p[3])
    C = 0.5*(p[2] - p[0])
    D = p[1] - val
    if(A == 0.0):
        return QuadraticEquation(B, C, D)
    Values = PolyCubicRoots(B/A, C/A, D/A)

    return Values

def CubicInterpolationInflections(p):
    A = 0.5*(3.0*(p[1] - p[2]) + p[3] - p[0])
    B = 0.5*(2.0*p[0] - 5.0*p[1] + 4.0*p[2] - p[3])
    C = 0.5*(p[2] - p[0])
    Values = QuadraticEquation(3.0*A, 2.0*B, C)
    #print(Values)
    return Values

def BicubicInterpolationDiagonalIntersections(p, val):
    PosSlopeParams = []
    NegSlopeParams = []
    for Index in range(0, 4):
        PosSlopeParams.append(p[Index][Index])
        NegSlopeParams.append(p[Index][3-Index])

    DiagIntersections = []
    #print("PosDiag")
    for Intersection in CubicInterpolationIntersections(PosSlopeParams, val):
        if type(Intersection) == float:
            if(0.0 <= Intersection) and (1.0 >= Intersection):
                MinPoint = 0.0
                MinErrorNeg = 0.0 >  val - PosSlopeParams[1]
                MaxPoint = 1.0
                MaxErrorNeg = 0.0 > val - PosSlopeParams[2]
                CurrentPoint = Intersection
                while MinPoint < MaxPoint:
                    ActualVal = BicubicInterpolation(p, CurrentPoint, CurrentPoint)
                    Error =  val - ActualVal
                    if 0.0 == Error:
                        break
                    #Gradient = BicubicGradient(p, CurrentPoint, CurrentPoint)
                    ErrorIsNeg = 0.0 > Error
                    #print(CurrentPoint, val, Error, ActualVal, Gradient)
                    if MaxErrorNeg != ErrorIsNeg:
                        MinPoint = CurrentPoint
                        MinErrorNeg = ErrorIsNeg
                    else:
                        MaxPoint = CurrentPoint
                        MaxErrorNeg = ErrorIsNeg
                    CurrentPoint = (MinPoint + MaxPoint) * 0.5
                    if(CurrentPoint == MinPoint) or (CurrentPoint == MaxPoint):
                        break
                DiagIntersections.append((CurrentPoint, CurrentPoint))
    #print("NegDiag")
    for Intersection in CubicInterpolationIntersections(NegSlopeParams, val):
        if type(Intersection) == float:
            if(0.0 <= Intersection) and (1.0 >= Intersection):
                MinPoint = 0.0
                MinErrorNeg = 0.0 >  val - NegSlopeParams[1]
                MaxPoint = 1.0
                MaxErrorNeg = 0.0 > val - NegSlopeParams[2]
                CurrentPoint = Intersection
                while MinPoint < MaxPoint:
                    ActualVal = BicubicInterpolation(p, CurrentPoint, 1.0 - CurrentPoint)
                    Error =  val - ActualVal
                    if 0.0 == Error:
                        break
                    #Gradient = BicubicGradient(p, CurrentPoint, CurrentPoint)
                    ErrorIsNeg = 0.0 > Error
                    #print(CurrentPoint, val, Error, ActualVal, Gradient)
                    if MaxErrorNeg != ErrorIsNeg:
                        MinPoint = CurrentPoint
                        MinErrorNeg = ErrorIsNeg
                    else:
                        MaxPoint = CurrentPoint
                        MaxErrorNeg = ErrorIsNeg
                    CurrentPoint = (MinPoint + MaxPoint) * 0.5
                    if(CurrentPoint == MinPoint) or (CurrentPoint == MaxPoint):
                        break
                DiagIntersections.append((CurrentPoint, 1.0 - CurrentPoint))

    return DiagIntersections

# Cubic interpolation gradient based on four values [0, 1]
def CubicGradient(p, x):
    return 0.5 * (p[2] - p[0] + x*(4.0*p[0] - 10.0*p[1] + 8.0*p[2] - 2.0*p[3] + x*(3.0*(3.0*(p[1] - p[2]) + p[3] - p[0]))))

def BicubicGradient(p, x, y):
    PTrans = list(map(list, zip(*p))) 
    #ParametersX = []
    #ParametersY = []
    #for Index in range(0, 4):
    #    PTrans = [p[0][Index], p[1][Index], p[2][Index], p[3][Index]]  
    #    ParametersX.append(CubicInterpolation(p[Index], y))
    #    ParametersY.append(CubicInterpolation(PTrans, x))
    ParametersX = BicubicToCubicInterpolation(PTrans, x)
    ParametersY = BicubicToCubicInterpolation(p, y)
    return (CubicGradient(ParametersX, x), CubicGradient(ParametersY, y))

# Clip value to within min/max
def ClipValue(val, minval, maxval):
    if(val < minval):
        return minval
    if(val > maxval):
        return maxval
    return val
    
# Find the array index that val is between
def ArrayValueToIndex(val, array):
    if(val < array[0]):
        return -1
    if(val > array[-1]):
        return len(array)
    for Index in range(1,len(array)):
        if((array[Index-1] <= val)and(val <= array[Index])):
            return Index -1
    return -2
    
# Find the array indices (float) that val is between
def ArrayValuesToIndices(val, array):
    ListOfIndices = []
    for Index in range(1,len(array)):
        if((array[Index-1] <= val)and(val <= array[Index])):
            Delta = array[Index] - array[Index-1]
            if(Delta > 0.0):
                ListOfIndices.append( float(Index-1) + (val - array[Index-1]) / Delta )
            else:
                ListOfIndices.append( float(Index-1) )
                ListOfIndices.append( float(Index) )
        elif((array[Index-1] >= val)and(val >= array[Index])):
            Delta = array[Index-1] - array[Index]
            ListOfIndices.append( float(Index-1) + (array[Index-1] - val) / Delta )
    return tuple( ListOfIndices )


def ConvertTimeToSeconds(timestr):
    if 3 > len(timestr):
        return -1
    timestr = timestr.strip()
    ColonIndex = timestr.find(":")
    if 0 > ColonIndex:
        return -1
    if IsInt(timestr[:ColonIndex]) and IsInt(timestr[ColonIndex+1:]):
        Hour = int(timestr[:ColonIndex])
        Minute = int(timestr[ColonIndex+1:])
        if 0 > Hour or 23 < Hour:
            return -1
        if 0 > Minute or 59 < Minute:
            return -1
        return Hour * 3600 + Minute * 60
    return -1

def ConvertSecondsToTime(timeinsec):
    Hour = int(timeinsec/3600)
    Minute = int((timeinsec/60) % 60)
    if 10 > Hour:
        RetStr = '0' + str(Hour)
    else:
        RetStr = str(Hour)
    RetStr += ":"
    if 10 > Minute:
        RetStr += '0' + str(Minute)
    else:
        RetStr += str(Minute)
    return RetStr
    
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

def PerimeterOrderPoints(pts):
    XVals = []
    YVals = []
    for Point in pts:
        XVals.append(Point[0])
        YVals.append(Point[1])
    MinPoint = (max(XVals), max(YVals))
    for Point in pts:
        if MinPoint[0] > Point[0]:
            MinPoint = Point
        elif(MinPoint[0] == Point[0]) and (MinPoint[1] > Point[1]):
           MinPoint = Point
    PointsLeft = pts[:]
    PointsLeft.remove(MinPoint)
    PerimeterList = [ MinPoint ]
    LastPoint = (MinPoint[0], MinPoint[1] + 1.0)
    CurrentPoint = MinPoint
    while True:
       BestAngle = 0
       PrevAngle = CalculateAngle(CurrentPoint,LastPoint)
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
    
def PrintListFixed(outlist, maxwidth, linewidth):
    OutString = '\n'
    ItemsPerLine = int(linewidth / (maxwidth + 1))
    ItemCount = 0
    for Item in outlist:
        ItemStr = Item
        for Index in range(len(ItemStr),maxwidth+1):
            ItemStr += ' '
        OutString += ItemStr
        ItemCount = ItemCount + 1
        if ItemCount >= ItemsPerLine:
            ItemCount = 0
            OutString += '\n'
    print(OutString)
    
def OutputHTMLHead(htmlfile,title):
    htmlfile.write('<!DOCTYPE html>\n<HTML>\n<HEAD>\n<TITLE>'+title+'</TITLE>\n</HEAD>\n<BODY>\n')

def OutputHTMLTail(htmlfile):
    htmlfile.write('</BODY>\n</HTML>\n')

def OutputHTMLAnchor(htmlfile,target,text):
    htmlfile.write('<A HREF="'+target+'">'+text+'</A>')

def OutputHTMLParagrah(htmlfile):
    htmlfile.write('<P>\n')

def OutputHTMLText(htmlfile,text):
    htmlfile.write(text)

def OutputHTMLBoldText(htmlfile,text):
    htmlfile.write('<B>'+text+'</B>')

def OutputHTMLHeader1(htmlfile,text):
    htmlfile.write('<H1>'+str(text)+'</H1>\n')

def OutputHTMLHeader2(htmlfile,text):
    htmlfile.write('<H2>'+str(text)+'</H2>\n')

def OutputHTMLImage(htmlfile,filename,width, height):
    htmlfile.write('<IMG SRC="'+filename+'" ALT="'+filename+'" HEIGHT="'+str(height)+'" WIDTH="'+str(width)+'"/>\n')

def OutputHTMLIndent(htmlfile,spacestoadd):
    for Index in range(0,spacestoadd):
        htmlfile.write(' ')

def OutputHTMLTableBegin(htmlfile,border):
    if 0 < border:
        htmlfile.write('<TABLE BORDER="'+str(border)+'">\n')
    else:
        htmlfile.write('<TABLE>\n')

def OutputHTMLTableEnd(htmlfile):
    htmlfile.write('</TABLE>\n')

def OutputHTMLTableData(htmlfile, data, indent = 4):
    OutputHTMLIndent(htmlfile,indent)
    htmlfile.write('<TD>'+str(data)+'</TD>\n')
    
def OutputHTMLTableRow(htmlfile, row, indent = 2, align='center'):
    OutputHTMLIndent(htmlfile,indent)
    htmlfile.write('<TR ALIGN="'+str(align)+'">\n')
    for Item in row:
        OutputHTMLTableData(htmlfile,Item,indent*2)
    OutputHTMLIndent(htmlfile,indent)
    htmlfile.write('</TR>\n')

def OutputSVGDocType(svgfile):
    svgfile.write('<?xml version="1.0" standalone="no"?>\n')
    svgfile.write('<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n')

def OutputSVGHead(svgfile, width, height, standalone=False):
    if(standalone):
        LineEnd = '" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink= "http://www.w3.org/1999/xlink">\n'
    else:
        LineEnd = '">\n'
    svgfile.write('<svg height="'+str(height)+'" width="'+str(width)+LineEnd)

def OutputSVGTail(svgfile):
    svgfile.write('</svg>\n')

def OutputSVGLine(svgfile,src,dest,rgb,width):
    svgfile.write('<line x1="'+str(src[0])+'" y1="'+str(src[1])+'" x2="'+str(dest[0])+'" y2="'+str(dest[1])+'" stroke="rgb('+str(rgb[0])+','+str(rgb[1])+','+str(rgb[2])+')" stroke-width="'+str(width)+'" />\n')

def OutputSVGPolyline(svgfile,pts,rgb,width,dashed=()):
    
    for Index,Point in enumerate(pts):
        if(0 == Index):
            PointString = str(Point[0])+','+str(Point[1])
        else:
            PointString += ' '+str(Point[0])+','+str(Point[1])
    if 0 == len(dashed):
        svgfile.write('<polyline points="'+PointString+'" stroke="rgb('+str(rgb[0])+','+str(rgb[1])+','+str(rgb[2])+')" stroke-width="'+str(width)+'" fill="none"/>\n')
    else:
        svgfile.write('<polyline points="'+PointString+'" stroke="rgb('+str(rgb[0])+','+str(rgb[1])+','+str(rgb[2])+')" stroke-width="'+str(width)+'" fill="none" stroke-dasharray="'+ str(dashed[0]) + ', ' + str(dashed[1]) + '"/>\n')

def OutputSVGCircle(svgfile,center,radius,rgb):
    svgfile.write('<circle cx="'+str(center[0])+'" cy="'+str(center[1])+'" r="'+str(radius)+'" stroke="rgb('+str(rgb[0])+','+str(rgb[1])+','+str(rgb[2])+')" stroke-width="1" fill="rgb('+str(rgb[0])+','+str(rgb[1])+','+str(rgb[2])+')" />\n')

def OutputSVGSquare(svgfile,center,halfwidth,rgb):
    svgfile.write('<rect x="'+str(center[0] - halfwidth)+'" y="'+str(center[1] - halfwidth)+'" width="'+str(halfwidth*2)+'" height="'+str(halfwidth*2)+'" stroke="rgb('+str(rgb[0])+','+str(rgb[1])+','+str(rgb[2])+')" stroke-width="1" fill="rgb('+str(rgb[0])+','+str(rgb[1])+','+str(rgb[2])+')" />\n')

def OutputSVGText(svgfile,x,y,rgb,vert,horz,text,rotate=0):
    if vert.lower() == 'bottom':
        vert = 'hanging'
    elif vert.lower() == 'middle':
        vert = 'central'
    else:
        vert = 'baseline'
    if horz.lower() == 'left':
        horz = 'end'
    elif horz.lower() == 'center':
        horz = 'middle'
    else:
        horz = 'start'    
    if 0 == rotate:
        svgfile.write('<text x="'+str(x)+'" y="'+str(y)+'" text-anchor="'+horz+'" alignment-baseline="'+vert+'" fill="rgb('+str(rgb[0])+','+str(rgb[1])+','+str(rgb[2])+')">'+text+'</text>\n')
    else:
        svgfile.write('<text transform="translate('+str(x)+','+str(y)+')rotate(' + str(rotate) + ')" text-anchor="'+horz+'" alignment-baseline="'+vert+'" fill="rgb('+str(rgb[0])+','+str(rgb[1])+','+str(rgb[2])+')">'+text+'</text>\n')
    
    
    
def OutputEfficiencyMap(filename, width, height, effmap, showiol = False, oppts=[]):
    with open(filename, 'w') as OutputFile:
        AssumedTextHeight = 20
        AssumedTextWidth = 10
        AxisColor = (0, 0, 0)
        AxisWidth = 2
        MaxPowerColor = (0, 0, 0)
        MaxPowerWidth = 3
        EfficiencyColor = (0, 0, 0) #(0, 0, 255)
        EfficiencyWidth = 2
        IdealPowerColor = (0, 0, 0) #(0, 255, 0)
        IdealPowerWidth = 2
        OpPointColor = (64, 64, 64) #(0, 255, 0)
        OpPointWidth = 2
        OpPointLength = AssumedTextWidth/2
        LabelDistance = 3

        MaxRPMDelta = 0
        for RPMIndex in range(0, len(effmap.MapRPMs)-1):
            MaxRPMDelta = max(MaxRPMDelta, effmap.MapRPMs[RPMIndex+1] - effmap.MapRPMs[RPMIndex])
        MaxRPMDelta *= 0.50000001
        
        MaxTorqueDelta = 0
        for TorqueIndex in range(0, len(effmap.MapTorques)-1):
            MaxTorqueDelta = max(MaxTorqueDelta, effmap.MapTorques[TorqueIndex+1] - effmap.MapTorques[TorqueIndex])
        MaxTorqueDelta *= 0.50000001
        
        MaxTorqueWidth = 0
        TorqueDigits = 0
        for TorqueValue in effmap.MapTorques:
            TorqueString = '{:g}'.format(TorqueValue)
            DecimalPointIndex = TorqueString.find(".")
            if(0 < DecimalPointIndex):
                TorqueDigits = max(TorqueDigits, len(TorqueString) - DecimalPointIndex - 1)
            MaxTorqueWidth = max(MaxTorqueWidth,len(TorqueString))
        
        RPMScaling = effmap.MapRPMs[-1] - effmap.MapRPMs[0]
        TorqueScaling = effmap.MapTorques[-1] - effmap.MapTorques[0]
        
        OriginX = (MaxTorqueWidth + 2) * AssumedTextWidth
        OriginY = AssumedTextHeight * 3
        RenderWidth = width - OriginX * 2
        RenderHeight = height - AssumedTextHeight * 4
        OutputSVGDocType(OutputFile)
        OutputSVGHead(OutputFile, width, height, True)
        def FlipY(y):
            return height - y
        # Draw X Axis
        OutputSVGLine(OutputFile, (OriginX, FlipY(OriginY)), (OriginX + RenderWidth, FlipY(OriginY)), AxisColor, AxisWidth)
        OutputSVGLine(OutputFile, (OriginX, FlipY(OriginY)), (OriginX, FlipY(OriginY+RenderHeight)), AxisColor, AxisWidth)
        
        XVal = OriginX + RenderWidth/2
        YVal = OriginY - AssumedTextWidth * 2 - AssumedTextHeight
        OutputSVGText(OutputFile, XVal, FlipY(YVal), AxisColor, 'bottom', 'center', "RPM")
        XVal = OriginX - MaxTorqueWidth * AssumedTextWidth
        YVal = OriginY + RenderHeight/2
        OutputSVGText(OutputFile, XVal, FlipY(YVal), AxisColor, 'top', 'center', "Torque", 270)
        
        DeltaRangeTorque = effmap.MapTorques[-1] - effmap.MapTorques[0]
        LeftTick = OriginX - AssumedTextWidth/2
        RightTick = OriginX + AssumedTextWidth/2
        FormatString = '{:.' + str(TorqueDigits) + 'f}'
        for TorqueValue in effmap.MapTorques:
            YVal = OriginY +(TorqueValue - effmap.MapTorques[0])/DeltaRangeTorque * RenderHeight
            OutputSVGText(OutputFile, OriginX - AssumedTextWidth, FlipY(YVal), AxisColor, 'middle', 'left', FormatString.format(TorqueValue))
            OutputSVGLine(OutputFile, (LeftTick, FlipY(YVal)), (RightTick, FlipY(YVal)), AxisColor, AxisWidth)
        DeltaRangeRPM = effmap.MapRPMs[-1] - effmap.MapRPMs[0] 
        YVal = OriginY - AssumedTextWidth
        TopTick = OriginY + AssumedTextWidth/2
        BottomTick = OriginY - AssumedTextWidth/2
        for RPMValue in effmap.MapRPMs:
            XVal = OriginX + (RPMValue - effmap.MapRPMs[0])/DeltaRangeRPM * RenderWidth
            OutputSVGText(OutputFile, XVal, FlipY(YVal), AxisColor, 'bottom', 'center', str(int(RPMValue)))
            OutputSVGLine(OutputFile, (XVal, FlipY(TopTick)), (XVal, FlipY(BottomTick)), AxisColor, AxisWidth)

        OutputPoints = []
        for Index in range(0,len(effmap.MapRPMs)):
            SubIncrements = 4
            for SubIndex in range(0, SubIncrements):
                RPMTarget = effmap.MaxPowerRPMs[Index] 
                if(Index + 1 >= len(effmap.MapRPMs) and 0 < SubIndex):
                    continue
                if 0 < SubIndex:
                    RPMTarget += (effmap.MaxPowerRPMs[Index+1] - effmap.MaxPowerRPMs[Index]) * SubIndex / SubIncrements
                MaxTorqueForTarget = effmap.CalculateMaxTorqueCubic(RPMTarget)
            
                XVal = OriginX + (RPMTarget - effmap.MapRPMs[0])/DeltaRangeRPM * RenderWidth
                YVal = OriginY + (MaxTorqueForTarget - effmap.MapTorques[0])/DeltaRangeTorque * RenderHeight
                OutputPoints.append((XVal, FlipY(YVal)))
        OutputSVGPolyline(OutputFile,OutputPoints,MaxPowerColor,MaxPowerWidth)
        
        OutputPoints = []
        for Index in range(0,len(effmap.IdealCubicTorques)):
            SubIncrements = 4
            for SubIndex in range(0, SubIncrements):
                RPMTarget = effmap.IdealCubicTorqueRPMs[Index] 
                if(Index + 1 >= len(effmap.IdealCubicTorqueRPMs) and 0 < SubIndex):
                    continue
                if 0 < SubIndex:
                    RPMTarget += (effmap.IdealCubicTorqueRPMs[Index+1] - effmap.IdealCubicTorqueRPMs[Index]) * SubIndex / SubIncrements
                MaxTorqueForTarget = effmap.CalculateIdealTorqueCubic(RPMTarget)
            
                XVal = OriginX + (RPMTarget - effmap.MapRPMs[0])/DeltaRangeRPM * RenderWidth
                YVal = OriginY + (MaxTorqueForTarget - effmap.MapTorques[0])/DeltaRangeTorque * RenderHeight
                OutputPoints.append((XVal, FlipY(YVal)))
        if showiol:
            OutputSVGPolyline(OutputFile,OutputPoints,IdealPowerColor,IdealPowerWidth, (10, 5))
        
        #OutputPoints = []
        #for Index in range(0,len(effmap.IdealTorques)):
        #    SubIncrements = 4
        #    for SubIndex in range(0, SubIncrements):
        #        RPMTarget = effmap.MapRPMs[Index] 
        #        if(Index + 1 >= len(effmap.MapRPMs) and 0 < SubIndex):
        #            continue
        #        if 0 < SubIndex:
        #            RPMTarget += (effmap.MapRPMs[Index+1] - effmap.MapRPMs[Index]) * SubIndex / SubIncrements
        #        MaxTorqueForTarget = effmap.CalculateIdealTorque(RPMTarget)
        #    
        #        XVal = OriginX + (RPMTarget - effmap.MapRPMs[0])/DeltaRangeRPM * RenderWidth
        #        YVal = OriginY + (MaxTorqueForTarget - effmap.MapTorques[0])/DeltaRangeTorque * RenderHeight
        #        OutputPoints.append((XVal, FlipY(YVal)))
        #OutputSVGPolyline(OutputFile,OutputPoints, (0, 255, 0),IdealPowerWidth, (10, 5))
        
        MinEff = -1
        MaxEff = -1
        for EffRow in effmap.MapEfficiencies:
            for EffVal in EffRow:
                if(0 < EffVal):
                    if(0 > MinEff):
                        MinEff = EffVal
                    MinEff = min(MinEff, EffVal)
                    MaxEff = max(MaxEff, EffVal)
        DeltaEff = MaxEff - MinEff
        EffMult = 1
        while((DeltaEff / 10.0) > 100.0):
            EffMult *= 10.0
            DeltaEff /= 10.0
        while((DeltaEff / 10.0) < 10.0):
            EffMult /= 10.0
            DeltaEff *= 10.0
        if((DeltaEff / 10.0) > 75.0):
            EffStep = 100.0 * EffMult
        elif((DeltaEff / 10.0) > 37.5):
            EffStep = 50.0 * EffMult
        elif((DeltaEff / 10.0) > 17.5):
            EffStep = 25.0 * EffMult
        else:
            EffStep = 10.0 * EffMult
            
        EffIndex = int(MinEff / EffStep) + 1
        EffToFind = []
        while(EffIndex * EffStep < MaxEff):
            EffToFind.append(EffIndex * EffStep)
            EffIndex += 1
            
        EffLabels = []
        for TargetEff in EffToFind:
            Crossings = []
            for RPMIndex in range(0, len(effmap.MapRPMs)):
                if(RPMIndex + 1 < len(effmap.MapRPMs)):
                    MaxRPMsMeetingTarget = effmap.FindMaxPowerConsumptionRPMs(TargetEff, effmap.MapRPMs[RPMIndex], effmap.MapRPMs[RPMIndex+1])
                    if 2 < len(MaxRPMsMeetingTarget):
                        DeltaRPM = effmap.MapRPMs[RPMIndex+1] - effmap.MapRPMs[RPMIndex]
                        MaxRPMsMeetingTarget.sort()
                        RPMGroups = [[MaxRPMsMeetingTarget[0]]]
                        for RPM in MaxRPMsMeetingTarget[1:]:
                            if (RPMGroups[-1][-1] - RPM) < DeltaRPM * 0.001:
                                RPMGroups[-1].append(RPM)
                            else:
                                RPMGroups.append([RPM])
                        MaxPowerMeetingTarget = []
                        for Group in RPMGroups:
                            BestRPM = Group[0]
                            BestTorque = effmap.CalculateMaxTorqueCubic(BestRPM)
                            BestEff = effmap.CalculateEfficiencyBicubic(BestRPM, BestTorque)
                            for RPM in Group[1:]:
                                CurTorque = effmap.CalculateMaxTorqueCubic(RPM)
                                CurEff = effmap.CalculateEfficiencyBicubic(RPM, CurTorque)
                                if abs(TargetEff - CurEff) < abs(TargetEff - BestEff):
                                   BestRPM = RPM
                                   BestTorque = CurTorque
                                   BestEff = CurEff
                            Crossings.append( ( (BestRPM, BestTorque), True) )
                
                for TorqueIndex in range(0, len(effmap.MapTorques)):
                    if effmap.CalculateMaxTorque(effmap.MapRPMs[RPMIndex]) >=  effmap.MapTorques[TorqueIndex]:
                        Intersections = CubicInterpolationIntersections(effmap.MapCubicEfficiencies[RPMIndex][TorqueIndex][1], TargetEff)
                        for Val in Intersections:
                            if type(Val) == float:
                                if(0.0 <= Val) and (1.0 > Val):
                                    if(TorqueIndex + 1 < len(effmap.MapTorques)):
                                        NewPoint = (effmap.MapRPMs[RPMIndex], Val * (effmap.MapTorques[TorqueIndex+1] - effmap.MapTorques[TorqueIndex]) + effmap.MapTorques[TorqueIndex])
                                        if effmap.CalculateMaxTorque(NewPoint[0]) > NewPoint[1]:
                                            Crossings.append( (NewPoint, RPMIndex == len(effmap.MapRPMs)-1) ) #, BicubicGradient(effmap.MapCubicEfficiencies[RPMIndex][TorqueIndex], 0.0, Val)) )
    
                        Intersections = CubicInterpolationIntersections(effmap.MapCubicEfficienciesTranspose[RPMIndex][TorqueIndex][1], TargetEff)
                        for Val in Intersections:
                            if type(Val) == float:
                                if(0.0 <= Val) and (1.0 > Val):
                                    if(RPMIndex + 1 < len(effmap.MapRPMs)):
                                        NewPoint = (Val * (effmap.MapRPMs[RPMIndex+1] - effmap.MapRPMs[RPMIndex]) + effmap.MapRPMs[RPMIndex], effmap.MapTorques[TorqueIndex])
                                        if effmap.CalculateMaxTorque(NewPoint[0]) > NewPoint[1]:
                                            Crossings.append( (NewPoint, RPMIndex == len(effmap.MapRPMs)-1) ) #, BicubicGradient(effmap.MapCubicEfficiencies[RPMIndex][TorqueIndex], Val, 0.0)) )
                        VHalfCoefs = BicubicToCubicInterpolation(effmap.MapCubicEfficienciesTranspose[RPMIndex][TorqueIndex], 0.5)
                        Intersections = CubicInterpolationIntersections(VHalfCoefs, TargetEff)
                        for Val in Intersections:
                            if type(Val) == float:
                                if(0.0 <= Val) and (1.0 > Val):
                                    if(RPMIndex + 1 < len(effmap.MapRPMs)) and (TorqueIndex + 1 < len(effmap.MapTorques)):
                                        NewPoint = ((effmap.MapRPMs[RPMIndex] + effmap.MapRPMs[RPMIndex+1]) * 0.5, Val * (effmap.MapTorques[TorqueIndex+1] - effmap.MapTorques[TorqueIndex]) + effmap.MapTorques[TorqueIndex])
                                        if effmap.CalculateMaxTorque(NewPoint[0]) > NewPoint[1]:
                                            Crossings.append( (NewPoint, RPMIndex == len(effmap.MapRPMs)-1) ) #, BicubicGradient(effmap.MapCubicEfficiencies[RPMIndex][TorqueIndex], 0.5, Val)) )
                        HHalfCoefs = BicubicToCubicInterpolation(effmap.MapCubicEfficiencies[RPMIndex][TorqueIndex], 0.5)
                        Intersections = CubicInterpolationIntersections(HHalfCoefs, TargetEff)
                        for Val in Intersections:
                            if type(Val) == float:
                                if(0.0 <= Val) and (1.0 > Val):
                                    if(RPMIndex + 1 < len(effmap.MapRPMs)) and (TorqueIndex + 1 < len(effmap.MapTorques)):
                                        NewPoint = (Val * (effmap.MapRPMs[RPMIndex+1] - effmap.MapRPMs[RPMIndex]) + effmap.MapRPMs[RPMIndex], (effmap.MapTorques[TorqueIndex] + effmap.MapTorques[TorqueIndex+1]) * 0.5)
                                        if effmap.CalculateMaxTorque(NewPoint[0]) > NewPoint[1]:
                                            Crossings.append( (NewPoint, RPMIndex == len(effmap.MapRPMs)-1) ) #, BicubicGradient(effmap.MapCubicEfficiencies[RPMIndex][TorqueIndex], Val, 0.5)) )
                        Intersections = BicubicInterpolationDiagonalIntersections(effmap.MapCubicEfficiencies[RPMIndex][TorqueIndex], TargetEff)   
                        for Val in Intersections:
                            if(RPMIndex + 1 < len(effmap.MapRPMs)) and (TorqueIndex + 1 < len(effmap.MapTorques)):
                                if(1.0 > Val[0]) and (1.0 > Val[1]):
                                    NewPoint = (Val[0] * (effmap.MapRPMs[RPMIndex+1] - effmap.MapRPMs[RPMIndex]) + effmap.MapRPMs[RPMIndex], Val[1] * (effmap.MapTorques[TorqueIndex+1] - effmap.MapTorques[TorqueIndex]) + effmap.MapTorques[TorqueIndex])
                                    if effmap.CalculateMaxTorque(NewPoint[0]) > NewPoint[1]:
                                        Crossings.append( (NewPoint, RPMIndex == len(effmap.MapRPMs)-1) ) #, BicubicGradient(effmap.MapCubicEfficiencies[RPMIndex][TorqueIndex], Val[0], Val[1])) )
                        
            Crossings = list(set(Crossings))
            PointDictionary = {}
            for Point in Crossings:
                if Point[0] not in PointDictionary:
                    PointDictionary[Point[0]] = Point
            Crossings = []
            AllRPMS = []
            for Point in PointDictionary:
                Crossings.append(PointDictionary[Point])
                AllRPMS.append(Point[0])
            AllRPMS = list(set(AllRPMS))
            AllRPMS.sort()
            #print(MaxRPMDelta, AllRPMS)
            #Crossings = list(set(Crossings))
            Crossings.sort()
            def VectorToAngle(x, y):
                YSquared = y**2 / (x**2 + y**2)
                if 0.0 <= x:
                    if 0.0 <= y:
                        return YSquared
                    else:
                        return -YSquared
                else:
                    if 0.0 <= y:
                        return 2.0 - YSquared
                    else:
                        return -2.0 + YSquared
            def AngleDelta(a1, a2):
                AngDel = abs(a1 - a2)
                if 2.0 < AngDel:
                    return 4.0 - AngDel
                else:
                    return AngDel
            Topolines = []    
            while len(Crossings):
                Topoline = []
                CurrentPoint = FirstPoint = Crossings[0]
                Topoline.append(CurrentPoint[0])
                Crossings = Crossings[1:]
                AllPointsAboveCurrent = True
                LastAngle = -1.0 #VectorToAngle(TanVector[0], TanVector[1])
                for Point in Crossings:
                    if abs(Point[0][0] - CurrentPoint[0][0]) <= MaxRPMDelta:
                        if Point[0][1] <= CurrentPoint[0][1]:
                            AllPointsAboveCurrent = False
                            break
                if AllPointsAboveCurrent:
                    LastAngle = 1.0
                while len(Crossings):
                    DirCandidates = []
                    for Point in Crossings:
                        if abs(Point[0][0] - CurrentPoint[0][0]) <= MaxRPMDelta and abs(Point[0][1] - CurrentPoint[0][1]) <= MaxTorqueDelta:
                            NextAngle = VectorToAngle( (Point[0][0] - CurrentPoint[0][0])/RPMScaling, (Point[0][1] - CurrentPoint[0][1])/TorqueScaling)
                            DirCandidates.append( (AngleDelta(LastAngle, NextAngle),  Point) )
                    DirCandidates.sort()
                    if 0 == len(DirCandidates):
                        break
                    NextPoint = DirCandidates[0]
                    if 1 < len(DirCandidates):
                        CandDist = CalculateDistance(CurrentPoint[0][0]/RPMScaling, CurrentPoint[0][1]/TorqueScaling, NextPoint[1][0][0]/RPMScaling, NextPoint[1][0][1]/TorqueScaling)
                        for OtherCandidate in DirCandidates[1:]:
                            OthDist = CalculateDistance(CurrentPoint[0][0]/RPMScaling, CurrentPoint[0][1]/TorqueScaling, OtherCandidate[1][0][0]/RPMScaling, OtherCandidate[1][0][1]/TorqueScaling)
                            if OthDist < CandDist:
                                if CalculateDistance(NextPoint[1][0][0]/RPMScaling, NextPoint[1][0][1]/TorqueScaling, OtherCandidate[1][0][0]/RPMScaling, OtherCandidate[1][0][1]/TorqueScaling) < CandDist:
                                    NextPoint = OtherCandidate
                                    CandDist = OthDist
                        
                                           
                    #DirVector = (CurrentPoint[0][0] - NextPoint[1][0][0], CurrentPoint[0][1] - NextPoint[1][0][1])
                    DirVector = (NextPoint[1][0][0] - CurrentPoint[0][0], NextPoint[1][0][1] - CurrentPoint[0][1])
                    #print(TanVector)
                    LastAngle = VectorToAngle(DirVector[0]/RPMScaling, DirVector[1]/TorqueScaling)
                    #print(LastAngle)
                    CurrentPoint = NextPoint[1]
                    Crossings.remove(CurrentPoint)
                    Topoline.append(CurrentPoint[0]) 
                    if(CurrentPoint[1]):
                        break

                if not AllPointsAboveCurrent:
                    LastAngle = 1.0
                    CurrentPoint = FirstPoint
                    while len(Crossings):           
                        DirCandidates = []
                        for Point in Crossings:
                            if abs(Point[0][0] - CurrentPoint[0][0]) <= MaxRPMDelta and abs(Point[0][1] - CurrentPoint[0][1]) <= MaxTorqueDelta:
                                NextAngle = VectorToAngle( (Point[0][0] - CurrentPoint[0][0])/RPMScaling, (Point[0][1] - CurrentPoint[0][1])/TorqueScaling)
                                DirCandidates.append( (AngleDelta(LastAngle, NextAngle),  Point) )
                        DirCandidates.sort()
                        if 0 == len(DirCandidates):
                            break
                        NextPoint = DirCandidates[0]
                        if 1 < len(DirCandidates):
                            CandDist = CalculateDistance(CurrentPoint[0][0]/RPMScaling, CurrentPoint[0][1]/TorqueScaling, NextPoint[1][0][0]/RPMScaling, NextPoint[1][0][1]/TorqueScaling)
                            for OtherCandidate in DirCandidates[1:]:
                                OthDist = CalculateDistance(CurrentPoint[0][0]/RPMScaling, CurrentPoint[0][1]/TorqueScaling, OtherCandidate[1][0][0]/RPMScaling, OtherCandidate[1][0][1]/TorqueScaling)
                                if OthDist < CandDist:
                                    if CalculateDistance(NextPoint[1][0][0]/RPMScaling, NextPoint[1][0][1]/TorqueScaling, OtherCandidate[1][0][0]/RPMScaling, OtherCandidate[1][0][1]/TorqueScaling) < CandDist:
                                        #print("Changing Point from", NextPoint, "to", OtherCandidate)
                                        NextPoint = OtherCandidate
                                        CandDist = OthDist
                        
                        #DirVector = (CurrentPoint[0][0] - NextPoint[1][0][0], CurrentPoint[0][1] - NextPoint[1][0][1])
                        DirVector = (NextPoint[1][0][0] - CurrentPoint[0][0], NextPoint[1][0][1] - CurrentPoint[0][1])
                        #print(TanVector)
                        LastAngle = VectorToAngle(DirVector[0]/RPMScaling, DirVector[1]/TorqueScaling)
                        #print(LastAngle)
                        CurrentPoint = NextPoint[1]
                        Crossings.remove(CurrentPoint)
                        Topoline.insert(0, CurrentPoint[0]) 
                        if(CurrentPoint[1]):
                            break
                if 1 < len(Topoline):
                    if abs(Topoline[0][0] - Topoline[-1][0]) <= MaxRPMDelta and abs(Topoline[0][1] - Topoline[-1][1]) <= MaxTorqueDelta:
                        Topoline.append(Topoline[0])
                    Topolines.append(Topoline)
                #break
                
            
            for Topoline in Topolines:                     
                OutputPoints = []
                for Point in Topoline:
                    XVal = OriginX + (Point[0] - effmap.MapRPMs[0])/DeltaRangeRPM * RenderWidth
                    YVal = OriginY + (Point[1] - effmap.MapTorques[0])/DeltaRangeTorque * RenderHeight
                    OutputPoints.append((XVal, FlipY(YVal)))
                if 0 == len(OutputPoints):
                    continue
                OutputSVGPolyline(OutputFile,OutputPoints,EfficiencyColor,EfficiencyWidth)
                Topoline.sort(key =itemgetter(1,0))
                TargetString = '{:g}'.format(TargetEff)
                for Point in Topoline:
                    XVal = (Point[0] - effmap.MapRPMs[0])/DeltaRangeRPM * RenderWidth
                    YVal = (Point[1] - effmap.MapTorques[0])/DeltaRangeTorque * RenderHeight - LabelDistance
                    if (YVal > AssumedTextHeight) and (XVal > AssumedTextWidth):
                        MinX = OriginX + XVal - AssumedTextWidth * len(TargetString) / 2
                        MaxX = OriginX + XVal + AssumedTextWidth * len(TargetString) / 2
                        MinY = OriginY + YVal - AssumedTextHeight
                        MaxY = OriginY + YVal + AssumedTextHeight
                        FoundOverlap = False
                        for EffLabel in EffLabels:
                            MnX = max(MinX, EffLabel[3])
                            MxX = min(MaxX, EffLabel[4])
                            MnY = max(MinY, EffLabel[5])
                            MxY = min(MaxY, EffLabel[6])
                            if MnX < MxX and MnY < MxY:
                                FoundOverlap = True
                                break
                        if Point[0] <  effmap.MapRPMs[int(len(effmap.MapRPMs)/3)]:
                            LabelLoc = 'right'
                        elif Point[0] >  effmap.MapRPMs[int((2 * len(effmap.MapRPMs))/3)]:
                            LabelLoc = 'right'
                        else:
                            LabelLoc = 'center'
                        if not FoundOverlap:
                            EffLabels.append((OriginX + XVal, OriginY + YVal, TargetString, MinX, MaxX, MinY, MaxY, LabelLoc))
                            break
            #break
        for Point in set(oppts):
            if effmap.CalculateMaxTorqueCubic(Point[0]) > Point[1]:
                XVal = OriginX + (Point[0] - effmap.MapRPMs[0])/DeltaRangeRPM * RenderWidth
                YVal = OriginY + (Point[1] - effmap.MapTorques[0])/DeltaRangeTorque * RenderHeight
                XLeft = max(XVal - OpPointLength, OriginX)
                XRight = max(XVal + OpPointLength, OriginX)
                YBottom = max(YVal - OpPointLength, OriginY)
                YTop = max(YVal + OpPointLength, OriginY)
                
                if(XLeft != XRight) and (YBottom != YTop) and (YVal > OriginY) and (XVal > OriginX):
                    OutputSVGLine(OutputFile, (XLeft, FlipY(YVal)), (XRight, FlipY(YVal)), OpPointColor, OpPointWidth)
                    OutputSVGLine(OutputFile, (XVal, FlipY(YBottom)), (XVal, FlipY(YTop)), OpPointColor, OpPointWidth)    
        for EffLabel in EffLabels:
            OutputSVGText(OutputFile, EffLabel[0], FlipY(EffLabel[1]), EfficiencyColor, 'bottom', EffLabel[7], EffLabel[2])
        
        
            

        OutputSVGTail(OutputFile)
        
        #print(BicubicInterpolationDiagonalIntersections(effmap.MapCubicEfficiencies[11][1], 475.0))
        
