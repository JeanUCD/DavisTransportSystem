#
# TTP 210 
#
import csv
import math
import glob
import os
import locale
from vehicleparameters import *
from busroute import *
from bikepath import *
from simconfig import *
from streetmap import *
from ttputils import *
from powertrain import *

TotalCamupsHours = 9 # 8:00 - 17:00
MinimumCampusHour = 8
ResultsDirectory = 'results/'
DataDirectory = 'data/'

def UpdatePercentage( per):
    if(type(per) == int):
        OutString = str(per) + '%'
        while(len(OutString) < 4):
            OutString = ' ' + OutString
    else:
        OutString = per
    sys.stdout.write('\r'+OutString)
    sys.stdout.flush()

def OutputRoutesAsHTML(filename, streetmap, bikepathmap, incoming, outgoing, distancetravelled, busdepot, busresutls, drivercount, bikercount, studentresult, employeeresult, busdriverinfo, fees, allvehicles, busschedule):
    CO2FuelLookup = {"gasoline":99.18,"biodiesel":83.25,"e85":76.9,"electricity":124.10}
    LHVJpgFuelLookup = {"gasoline":44427.0,"biodiesel":44147.0,"e85":31213.0}
    PricePerKGFuelLookup = {"gasoline":1.18,"biodiesel":1.32,"e85":1.45,"electricity":0.08}
    # Source http://siteresources.worldbank.org/INTEAPASTAE/Resources/GHG-ExecSummary.pdf taken from provincial road
    # CO2/mile of pavement of bike path is 126.574591metric tons = 126,574,591g/mi
    # Source https://ecf.com/files/wp-content/uploads/ECF_CO2_WEB.pdf
    # CO2/km of making a 8year bike is 5g/km = 8.0467g/mi
    # CO2/km of food is 16g/km = 25.74944g/mi
    BikePathConstructiongCO2pmi = 126574591
    BikeConstructiongCO2pmi = 8.0467
    BikeFoodgCO2pmi = 25.74944
    BikePathConstructiongCO2pmi /= 10 * 200 # amortize over 10 years, 200 days/year
    
    DesiredWidth = 600
    BorderWidth = 40
    Scaling = float(DesiredWidth) / streetmap.MaxX
    DesiredHeight = int(math.ceil(streetmap.MaxY * Scaling))
    
    RGBBlack = (0,0,0)
    RGBRed = (255,0,0)
    RGBBlue = (0,0,255)
    RGBGreen = (0,160,0)
    RGBPurple = (255,0,255)
    
    OutputFile = open(ResultsDirectory + 'summary.html', 'w')
    OutputHTMLHead(OutputFile,'Travel Summary') 
    OutputHTMLHeader2(OutputFile,'Travelers:')
    
    OutputHTMLBoldText(OutputFile,'Travel Mode &amp; Distance')
    OutputHTMLTableBegin(OutputFile, 1)
    
    TotalTravel = {'Bike':[0,0], 'Drive':[0,0],'Bus':[0,0],'Total':[0,0]}   
    for CurTime in range(MinimumCampusHour, MinimumCampusHour + TotalCamupsHours + 1):
        if CurTime in incoming:
           PointList = incoming[CurTime]
           TotalTravel['Total'][0] = TotalTravel['Total'][0] + len(PointList)
           for PointData in PointList:
               if 'bike' == PointData[1]:
                   TotalTravel['Bike'][0] = TotalTravel['Bike'][0] + 1
               elif 'drive' == PointData[1]:
                   TotalTravel['Drive'][0] = TotalTravel['Drive'][0] + 1
               else:
                   TotalTravel['Bus'][0] = TotalTravel['Bus'][0] + 1    
               Point = PointData[0]
        if CurTime in outgoing:
           PointList = outgoing[CurTime]
           TotalTravel['Total'][1] = TotalTravel['Total'][1] + len(PointList)
           for PointData in PointList:
               if 'bike' == PointData[1]:
                   TotalTravel['Bike'][1] = TotalTravel['Bike'][1] + 1
               elif 'drive' == PointData[1]:
                   TotalTravel['Drive'][1] = TotalTravel['Drive'][1] + 1
               else:
                   TotalTravel['Bus'][1] = TotalTravel['Bus'][1] + 1
    
    
    
    OutputHTMLTableRow(OutputFile,['','To Campus','From Campus','Distance (mi)','Average (mi)'])
    OutputHTMLTableRow(OutputFile,['Bike',locale.format_string("%d",TotalTravel['Bike'][0], True), locale.format_string("%d",TotalTravel['Bike'][1], True), locale.format_string("%.1f", distancetravelled['Bike'], True), str("%.1f" % ( distancetravelled['Bike']/TotalTravel['Bike'][0])) ])
    if 0 < TotalTravel['Bus'][0]:
        OutputHTMLTableRow(OutputFile,['Bus',locale.format_string("%d",TotalTravel['Bus'][0], True), locale.format_string("%d",TotalTravel['Bus'][1], True), locale.format_string("%.1f", distancetravelled['Bus'], True), str("%.1f" % ( distancetravelled['Bus']/TotalTravel['Bus'][0])) ])
    OutputHTMLTableRow(OutputFile,['Drive',locale.format_string("%d",TotalTravel['Drive'][0], True), locale.format_string("%d",TotalTravel['Drive'][1], True), locale.format_string("%.1f", distancetravelled['Drive'], True), str("%.1f" % ( distancetravelled['Drive']/TotalTravel['Drive'][0])) ])
    OutputHTMLTableRow(OutputFile,['Total',locale.format_string("%d",TotalTravel['Total'][0], True), locale.format_string("%d",TotalTravel['Total'][1], True), locale.format_string("%.1f", distancetravelled['Total'], True), str("%.1f" % ( distancetravelled['Total']/TotalTravel['Total'][0])) ])

    OutputHTMLTableEnd(OutputFile)

    OutputHTMLBoldText(OutputFile,'<BR>Travel Breakdown by Time:<BR>\n')
    for LinkTime in range(MinimumCampusHour, MinimumCampusHour + TotalCamupsHours + 1):
        OutputHTMLAnchor(OutputFile, filename+str(LinkTime)+'.html', ConvertSecondsToTime(LinkTime * 3600) )
        OutputHTMLText(OutputFile, " ")


    BikePassengers = bikercount
    BikeDistance = distancetravelled['Bike']
    BikePassengerDistance = distancetravelled['Bike']
    BikeFuel = 0.0
    BikeElectricity = 0.0
    BikeCO2 = bikepathmap.TotalPathLength() * BikePathConstructiongCO2pmi + (BikeConstructiongCO2pmi + BikeFoodgCO2pmi) * BikePassengerDistance
    BikeHC = 0.0
    BikeCO = 0.0
    BikeNOx = 0.0
    BikePM = 0.0
    BikeFuelKG = 0.0


    BusDistance = 0.0
    BusPassengerDistance = distancetravelled['Bus']
    BusFuel = 0.0
    BusElectricity = 0.0
    BusCO2 = 0.0
    BusHC = 0.0
    BusCO = 0.0
    BusNOx = 0.0
    BusPM = 0.0
    BusFuelKG = {'gasoline':0.0, 'biodiesel':0.0,'e85':0.0,'electricity':0.0}
    for Result in busresutls:
        BusDistance += Result[0]
        BusElectricity += Result[1]
        BusFuel += Result[3]
        BusCO2 += CO2FuelLookup[Result[2]] * LHVJpgFuelLookup[Result[2]] * Result[3]/ 1.0e6 + CO2FuelLookup['electricity'] * Result[1] * 3600.0/1e6
        BusHC += Result[4]
        BusCO += Result[5]
        BusNOx += Result[6]
        BusPM += Result[7]
        BusFuelKG[Result[2]] += Result[3] / 1000.0
        BusFuelKG['electricity'] += Result[1] / 1000.0

    EmployeeDistance = 0.0
    EmployeePassengerDistance = distancetravelled['Employee']  
    EmployeeFuel = 0.0
    EmployeeElectricity = 0.0
    EmployeeCO2 = 0.0
    EmployeeHC = 0.0
    EmployeeCO = 0.0
    EmployeeNOx = 0.0
    EmployeePM = 0.0
    for Result in employeeresult:
        EmployeeDistance += Result[0]
        EmployeeElectricity += Result[1]
        EmployeeFuel += Result[3]
        EmployeeCO2 += CO2FuelLookup[Result[2]] * LHVJpgFuelLookup[Result[2]] * Result[3]/ 1.0e6 + CO2FuelLookup['electricity'] * Result[1] * 3600.0/1e6
        EmployeeHC += Result[4]
        EmployeeCO += Result[5]
        EmployeeNOx += Result[6]
        EmployeePM += Result[7]
        
    EmployeeDistance = (EmployeeDistance * drivercount[1]) / len(employeeresult)
    EmployeeElectricity = (EmployeeElectricity * drivercount[1]) / len(employeeresult)
    EmployeeFuel = (EmployeeFuel * drivercount[1]) / len(employeeresult)
    EmployeeCO2 = (EmployeeCO2 * drivercount[1]) / len(employeeresult)
    EmployeeHC = (EmployeeHC * drivercount[1]) / len(employeeresult)
    EmployeeCO = (EmployeeCO * drivercount[1]) / len(employeeresult)
    EmployeeNOx = (EmployeeNOx * drivercount[1]) / len(employeeresult)
    EmployeePM = (EmployeePM * drivercount[1]) / len(employeeresult)
    
    
    StudentDistance = 0.0
    StudentPassengerDistance = distancetravelled['Student']  
    StudentFuel = 0.0
    StudentElectricity = 0.0
    StudentCO2 = 0.0
    StudentHC = 0.0
    StudentCO = 0.0
    StudentNOx = 0.0
    StudentPM = 0.0
    for Result in studentresult:
        StudentDistance += Result[0]
        StudentElectricity += Result[1]
        StudentFuel += Result[3]
        StudentCO2 += CO2FuelLookup[Result[2]] * LHVJpgFuelLookup[Result[2]] * Result[3]/ 1.0e6 + CO2FuelLookup['electricity'] * Result[1] * 3600.0/1e6
        StudentHC += Result[4]
        StudentCO += Result[5]
        StudentNOx += Result[6]
        StudentPM += Result[7]
        
    StudentDistance = (StudentDistance * drivercount[0]) / len(studentresult)
    StudentElectricity = (StudentElectricity * drivercount[0]) / len(studentresult)
    StudentFuel = (StudentFuel * drivercount[0]) / len(studentresult)
    StudentCO2 = (StudentCO2 * drivercount[0]) / len(studentresult)
    StudentHC = (StudentHC * drivercount[0]) / len(studentresult)
    StudentCO = (StudentCO * drivercount[0]) / len(studentresult)
    StudentNOx = (StudentNOx * drivercount[0]) / len(studentresult)
    StudentPM = (StudentPM * drivercount[0]) / len(studentresult)

    TotalDistance = StudentPassengerDistance + EmployeePassengerDistance + BusDistance + BikeDistance
    TotalPassengerDistance = StudentPassengerDistance + EmployeePassengerDistance + BusPassengerDistance + BikePassengerDistance
    TotalElectricity = StudentElectricity + EmployeeElectricity + BusElectricity + BikeElectricity
    TotalFuel = StudentFuel + EmployeeFuel + BusFuel + BikeFuel
    TotalCO2 = StudentCO2 + EmployeeCO2 + BusCO2 + BikeCO2
    TotalHC = StudentHC + EmployeeHC + BusHC + BikeHC
    TotalCO = StudentCO + EmployeeCO + BusCO + BikeCO
    TotalNOx = StudentNOx + EmployeeNOx + BusNOx + BikeNOx
    TotalPM = StudentPM + EmployeePM + BusPM + BikePM
        
    #DriverCount, AllStudentResults, AllEmployeeResults
    #OutputHTMLHeader2(OutputFile,'Resources:')
    #OutputHTMLTableBegin(OutputFile, 1)
    #OutputHTMLTableRow(OutputFile,['Vehicle Type','Count'])
    #for BusType in busdepot:
    #    OutputHTMLTableRow(OutputFile,[BusType,str(len(busdepot[BusType]))])
    #OutputHTMLTableEnd(OutputFile)
    
   
    OutputHTMLHeader2(OutputFile,'Results:')
    OutputHTMLBoldText(OutputFile,'Fuel Consumption &amp; Emissions')
    OutputHTMLTableBegin(OutputFile, 1)
    Header = ['Mode','Distance','Fuel (kg)','Elec kWh','Total CO<SUB>2</SUB>(kg)','Total HC(kg)','Total CO(kg)','Total NOx(kg)','Total PM(kg)']
    Header.extend(['CO<SUB>2</SUB> g/mi','HC g/mi','CO g/mi','NOx g/mi','PM g/mi'])
    Header.extend(['CO<SUB>2</SUB> g/pmi','HC g/pmi','CO g/pmi','NOx g/pmi','PM g/pmi'])
    OutputHTMLTableRow(OutputFile,Header)
    if 0.0 < BikePassengerDistance:
        RowData = ['Bike', locale.format_string("%.1f", BikeDistance, True), locale.format_string("%.1f" , BikeFuel/1000.0, True), locale.format_string("%.1f", BikeElectricity/1000.0, True), locale.format_string("%.1f", BikeCO2/1000.0, True), locale.format_string("%.1f", BikeHC/1000.0, True), locale.format_string("%.1f", BikeCO/1000.0, True), locale.format_string("%.1f", BikeNOx/1000.0, True), locale.format_string("%.2f", BikePM/1000.0, True)]
        RowData.extend([locale.format_string("%.1f", BikeCO2/BikeDistance, True), locale.format_string("%.1f", BikeHC/BikeDistance, True), locale.format_string("%.1f", BikeCO/BikeDistance, True), locale.format_string("%.1f", BikeNOx/BikeDistance, True), locale.format_string("%.2f", BikePM/BikeDistance, True)])
        RowData.extend([locale.format_string("%.1f", BikeCO2/BikePassengerDistance, True), locale.format_string("%.2f", BikeHC/BikePassengerDistance, True), locale.format_string("%.2f", BikeCO/BikePassengerDistance, True), locale.format_string("%.2f", BikeNOx/BikePassengerDistance, True), locale.format_string("%.3f", BikePM/BikePassengerDistance, True)])
        OutputHTMLTableRow(OutputFile,RowData)
    
    if 0.0 < BusPassengerDistance:
        RowData = ['Bus', locale.format_string("%.1f", BusDistance, True), locale.format_string("%.1f" , BusFuel/1000.0, True), locale.format_string("%.1f", BusElectricity/1000.0, True), locale.format_string("%.1f", BusCO2/1000.0, True), locale.format_string("%.1f", BusHC/1000.0, True), locale.format_string("%.1f", BusCO/1000.0, True), locale.format_string("%.1f", BusNOx/1000.0, True), locale.format_string("%.2f", BusPM/1000.0, True)]
        RowData.extend([locale.format_string("%.1f", BusCO2/BusDistance, True), locale.format_string("%.1f", BusHC/BusDistance, True), locale.format_string("%.1f", BusCO/BusDistance, True), locale.format_string("%.1f", BusNOx/BusDistance, True), locale.format_string("%.2f", BusPM/BusDistance, True)])
        RowData.extend([locale.format_string("%.1f", BusCO2/BusPassengerDistance, True), locale.format_string("%.2f", BusHC/BusPassengerDistance, True), locale.format_string("%.2f", BusCO/BusPassengerDistance, True), locale.format_string("%.2f", BusNOx/BusPassengerDistance, True), locale.format_string("%.3f", BusPM/BusPassengerDistance, True)])
        OutputHTMLTableRow(OutputFile,RowData)
    
    RowData = ['Employee',locale.format_string("%.1f" , EmployeePassengerDistance, True), locale.format_string("%.1f", EmployeeFuel/1000.0, True), locale.format_string("%.1f", EmployeeElectricity/1000.0, True), locale.format_string("%.1f", EmployeeCO2/1000.0, True), locale.format_string("%.1f", EmployeeHC/1000.0, True), locale.format_string("%.1f", EmployeeCO/1000.0, True), locale.format_string("%.1f", EmployeeNOx/1000.0, True), locale.format_string("%.2f", EmployeePM/1000.0, True)]
    RowData.extend([locale.format_string("%.1f", EmployeeCO2/EmployeePassengerDistance, True), locale.format_string("%.1f", EmployeeHC/EmployeePassengerDistance, True), locale.format_string("%.1f", EmployeeCO/EmployeePassengerDistance, True), locale.format_string("%.1f", EmployeeNOx/EmployeePassengerDistance, True), locale.format_string("%.2f", EmployeePM/EmployeePassengerDistance, True)])
    RowData.extend([locale.format_string("%.1f", EmployeeCO2/EmployeePassengerDistance, True), locale.format_string("%.2f", EmployeeHC/EmployeePassengerDistance, True), locale.format_string("%.2f", EmployeeCO/EmployeePassengerDistance, True), locale.format_string("%.2f", EmployeeNOx/EmployeePassengerDistance, True), locale.format_string("%.3f", EmployeePM/EmployeePassengerDistance, True)])
    OutputHTMLTableRow(OutputFile,RowData)
    
    RowData = ['Student',locale.format_string("%.1f", StudentPassengerDistance, True), locale.format_string("%.1f", StudentFuel/1000.0, True), locale.format_string("%.1f", StudentElectricity/1000.0, True), locale.format_string("%.1f", StudentCO2/1000.0, True), locale.format_string("%.1f", StudentHC/1000.0, True), locale.format_string("%.1f", StudentCO/1000.0, True), locale.format_string("%.1f", StudentNOx/1000.0, True), locale.format_string("%.2f", StudentPM/1000.0, True)]
    RowData.extend([locale.format_string("%.1f", StudentCO2/StudentPassengerDistance, True), locale.format_string("%.1f", StudentHC/StudentPassengerDistance, True), locale.format_string("%.1f", StudentCO/StudentPassengerDistance, True), locale.format_string("%.1f", StudentNOx/StudentPassengerDistance, True), locale.format_string("%.2f", StudentPM/StudentPassengerDistance, True)])
    RowData.extend([locale.format_string("%.1f", StudentCO2/StudentPassengerDistance, True), locale.format_string("%.2f", StudentHC/StudentPassengerDistance, True), locale.format_string("%.2f", StudentCO/StudentPassengerDistance, True), locale.format_string("%.2f", StudentNOx/StudentPassengerDistance, True), locale.format_string("%.3f", StudentPM/StudentPassengerDistance, True)])
    OutputHTMLTableRow(OutputFile,RowData)
    
    RowData = ['Total',locale.format_string("%.1f", TotalPassengerDistance, True), locale.format_string("%.1f", TotalFuel/1000.0, True), locale.format_string("%.1f", TotalElectricity/1000.0, True), locale.format_string("%.1f", TotalCO2/1000.0, True), locale.format_string("%.1f", TotalHC/1000.0, True), locale.format_string("%.1f", TotalCO/1000.0, True), locale.format_string("%.1f", TotalNOx/1000.0, True), locale.format_string("%.2f", TotalPM/1000.0, True)]
    RowData.extend([locale.format_string("%.1f", TotalCO2/TotalDistance, True), locale.format_string("%.1f", TotalHC/TotalDistance, True), locale.format_string("%.1f", TotalCO/TotalDistance, True), locale.format_string("%.1f", TotalNOx/TotalDistance, True), locale.format_string("%.2f", TotalPM/TotalDistance, True)])
    RowData.extend([locale.format_string("%.1f", TotalCO2/TotalPassengerDistance, True), locale.format_string("%.2f", TotalHC/TotalPassengerDistance, True), locale.format_string("%.2f", TotalCO/TotalPassengerDistance, True), locale.format_string("%.2f", TotalNOx/TotalPassengerDistance, True), locale.format_string("%.3f", TotalPM/TotalPassengerDistance, True)])
    OutputHTMLTableRow(OutputFile,RowData)
    
    OutputHTMLTableEnd(OutputFile)
    
    OutputHTMLHeader2(OutputFile,'Economics:')
    OutputHTMLBoldText(OutputFile,'Driver Wages')
    OutputHTMLTableBegin(OutputFile, 1)
    Header = ['Drivers','Hours','Wage &#36;/hr','Daily Cost &#36;']
    OutputHTMLTableRow(OutputFile,Header)
    RowData = [busdriverinfo[0] , busdriverinfo[1],locale.format_string("%.2f", busdriverinfo[2], True), locale.format_string("%.2f", busdriverinfo[2] * busdriverinfo[1], True)]
    OutputHTMLTableRow(OutputFile,RowData)
    OutputHTMLTableEnd(OutputFile)
    TotalWages = busdriverinfo[2] * busdriverinfo[1]
    
    OutputHTMLText(OutputFile,'<BR>')
    OutputHTMLBoldText(OutputFile,'Fuel &amp; Maintenance Costs')
    OutputHTMLTableBegin(OutputFile, 1)
    TotalFuelCost = 0.0
    Header = ['Item','Consumed','Cost &#36;/unit','Daily Cost &#36;']
    OutputHTMLTableRow(OutputFile,Header)
    for FuelType in PricePerKGFuelLookup:
        if 0.0 < BusFuelKG[FuelType]:
            if FuelType == 'electricity':
                UnitName = 'kWh'
            else:
                UnitName = 'kg'
            TotalFuelCost = TotalFuelCost + PricePerKGFuelLookup[FuelType] * BusFuelKG[FuelType]
            RowData = [FuelType.capitalize(), locale.format_string("%.1f", BusFuelKG[FuelType], True)+UnitName, locale.format_string("%.2f", PricePerKGFuelLookup[FuelType], True), locale.format_string("%.2f", PricePerKGFuelLookup[FuelType] * BusFuelKG[FuelType], True)]
            OutputHTMLTableRow(OutputFile,RowData)
    # should fix matenance cost to be sim parameter        
    RowData = ['Maintenance',locale.format_string("%.1f", BusDistance, True)+'mi', '0.30',locale.format_string("%.2f", BusDistance * 0.3, True)]
    TotalFuelCost = TotalFuelCost + (BusDistance * 0.3)
    OutputHTMLTableRow(OutputFile,RowData)
    RowData = ['Total','','',locale.format_string("%.2f", TotalFuelCost, True)]
    OutputHTMLTableRow(OutputFile,RowData)
    OutputHTMLTableEnd(OutputFile)
    

    OutputHTMLText(OutputFile,'<BR>')
    OutputHTMLBoldText(OutputFile,'Resource Cost')
    OutputHTMLTableBegin(OutputFile, 1)
    TotalBusPrice = 0.0
    TotalBusOverhead = 0.0
    OutputHTMLTableRow(OutputFile,['Vehicle Type','Count','Price &#36;','5yr Total &#36;','Daily Overhead &#36;'])
    for BusType in busdepot:
        TotalBusPrice = TotalBusPrice + (len(busdepot[BusType]) * float(allvehicles.GetParameter(BusType,'Price')))
        TotalBusOverhead = TotalBusOverhead + (len(busdepot[BusType]) * float(allvehicles.GetParameter(BusType,'Price'))) / 1000.0 
        OutputHTMLTableRow(OutputFile,[BusType,str(len(busdepot[BusType])), locale.format_string("%.2f", float(allvehicles.GetParameter(BusType,'Price')), True),locale.format_string("%.2f", len(busdepot[BusType]) * float(allvehicles.GetParameter(BusType,'Price')), True), locale.format_string("%.2f", (len(busdepot[BusType]) * float(allvehicles.GetParameter(BusType,'Price'))) / 1000.0, True) ])
    RowData = ['Total','','',locale.format_string("%.2f", TotalBusPrice, True),locale.format_string("%.2f", TotalBusOverhead, True)]
    OutputHTMLTableRow(OutputFile,RowData)
    OutputHTMLTableEnd(OutputFile)
    
    # put infrastructure here
    OutputHTMLText(OutputFile,'<BR>')
    OutputHTMLBoldText(OutputFile,'Infrastructure')
    OutputHTMLTableBegin(OutputFile, 1)
    AnnualBikePathPrice = bikepathmap.TotalPathLength() * fees[2]        
    DailyBikePathPRice = AnnualBikePathPrice/ 200.0
    OutputHTMLTableRow(OutputFile,['Path Type','Miles','Annual Price &#36;/mi','Annual Price &#36;', 'Daily Overhead &#36;'])
    OutputHTMLTableRow(OutputFile,['Paved Path', locale.format_string("%.2f", bikepathmap.TotalPathLength(), True), locale.format_string("%.2f", fees[2], True), locale.format_string("%.2f", AnnualBikePathPrice, True), locale.format_string("%.2f", DailyBikePathPRice, True)])

    RowData = ['Total','','',locale.format_string("%.2f", AnnualBikePathPrice, True), locale.format_string("%.2f", DailyBikePathPRice, True)]
    OutputHTMLTableRow(OutputFile,RowData)
    OutputHTMLTableEnd(OutputFile)
    
    OutputHTMLText(OutputFile,'<BR>')
    OutputHTMLBoldText(OutputFile,'Revenue')
    OutputHTMLTableBegin(OutputFile, 1)
    TotalParking = fees[1] * (drivercount[0] + drivercount[1])#TotalTravel['Drive'][0]
    TotalBusRevenue = fees[0] * TotalTravel['Bus'][0]
    OutputHTMLTableRow(OutputFile,['','Count','Price &#36;','Daily Total &#36;'])
    RowData = ['Parking',locale.format_string("%d",drivercount[0] + drivercount[1], True),locale.format_string("%.2f", fees[1], True), locale.format_string("%.2f", TotalParking, True)]
    OutputHTMLTableRow(OutputFile,RowData)
    RowData = ['Bus',locale.format_string("%d",TotalTravel['Bus'][0], True),locale.format_string("%.2f", fees[0], True), locale.format_string("%.2f", TotalBusRevenue, True)]
    OutputHTMLTableRow(OutputFile,RowData)
    RowData = ['Total','','',locale.format_string("%.2f",TotalBusRevenue + TotalParking, True)]
    OutputHTMLTableRow(OutputFile,RowData)
    OutputHTMLTableEnd(OutputFile)


    OutputHTMLText(OutputFile,'<BR>')
    OutputHTMLBoldText(OutputFile,'Totals')
    OutputHTMLTableBegin(OutputFile, 1)
    OutputHTMLTableRow(OutputFile,['Item','Daily Total &#36;'])
    if 0.0 < (TotalBusRevenue + TotalParking):
        RowData = ['Revenue',locale.format_string("%.2f", TotalBusRevenue + TotalParking, True)]
        OutputHTMLTableRow(OutputFile,RowData)
    if 0.0 < TotalWages:
        RowData = ['Wages','('+locale.format_string("%.2f", TotalWages, True)+')']
        OutputHTMLTableRow(OutputFile,RowData)
    if 0.0 < TotalFuelCost:
        RowData = ['Fuel','('+locale.format_string("%.2f", TotalFuelCost, True)+')']
        OutputHTMLTableRow(OutputFile,RowData)
    if 0.0 < TotalBusOverhead:
        RowData = ['Resources','('+locale.format_string("%.2f", TotalBusOverhead, True)+')']
        OutputHTMLTableRow(OutputFile,RowData)
    if 0.0 < DailyBikePathPRice:
        RowData = ['Infrastructure','('+locale.format_string("%.2f", DailyBikePathPRice, True)+')']
        OutputHTMLTableRow(OutputFile,RowData)
    if (TotalBusRevenue + TotalParking) >= (TotalWages + TotalFuelCost + TotalBusOverhead + DailyBikePathPRice):    
        RowData = ['Total',locale.format_string("%.2f", (TotalBusRevenue + TotalParking) - (TotalWages + TotalFuelCost + TotalBusOverhead + DailyBikePathPRice), True)]
    else:
        RowData = ['Total','('+locale.format_string("%.2f", (TotalWages + TotalFuelCost + TotalBusOverhead + DailyBikePathPRice) - (TotalBusRevenue + TotalParking), True)+')']
    OutputHTMLTableRow(OutputFile,RowData)
    OutputHTMLTableEnd(OutputFile)

    OutputHTMLTail(OutputFile)
    OutputFile.close()
    
    for CurTime in range(MinimumCampusHour, MinimumCampusHour + TotalCamupsHours + 1):
        OutputFile = open(ResultsDirectory+filename+str(CurTime)+'.html', 'w')
        OutputHTMLHead(OutputFile,'Travel Plans')     
        
        OutputHTMLIndent(OutputFile,2)
        OutputHTMLHeader1(OutputFile,'Time: '+ ConvertSecondsToTime(CurTime * 3600) )
        
        OutputHTMLIndent(OutputFile,2)
        OutputHTMLAnchor(OutputFile, 'summary.html', 'Summary' )
        OutputHTMLText(OutputFile, '<BR>\n' )
        OutputHTMLIndent(OutputFile,2)
        for LinkTime in range(MinimumCampusHour, MinimumCampusHour + TotalCamupsHours + 1):
            if CurTime != LinkTime:
                OutputHTMLAnchor(OutputFile, filename+str(LinkTime)+'.html', ConvertSecondsToTime(LinkTime * 3600) )
            else:
                OutputHTMLBoldText(OutputFile, ConvertSecondsToTime(LinkTime * 3600) )
            OutputHTMLText(OutputFile, " ")
        OutputHTMLParagrah(OutputFile)
        
        OutputHTMLIndent(OutputFile,2)
        OutputHTMLHeader2(OutputFile,'All Travel' )

        OutputImageFileName = "All"+str(CurTime)+".svg"
        OutputImageFile = open(ResultsDirectory+OutputImageFileName, 'w')
        OutputHTMLIndent(OutputFile,4)
        OutputHTMLImage(OutputFile, OutputImageFileName, DesiredWidth + 2 * BorderWidth, DesiredHeight + 2 * BorderWidth)
        
        OutputSVGDocType(OutputImageFile)
        OutputSVGHead(OutputImageFile, DesiredWidth + 2 * BorderWidth, DesiredHeight + 2 * BorderWidth, True)

        for Edge in streetmap.EdgeList:
           Source = streetmap.PointDB[Edge[0]]
           Source = (BorderWidth + int(Source[0] * Scaling), DesiredHeight + BorderWidth - int(Source[1] * Scaling))
           Dest = streetmap.PointDB[Edge[1]]
           Dest = (BorderWidth + int(Dest[0] * Scaling), DesiredHeight + BorderWidth - int(Dest[1] * Scaling))
           OutputHTMLIndent(OutputImageFile,2)
           OutputSVGLine(OutputImageFile, Source, Dest, RGBBlack, 2)
        TotalTravel = {'Bike':[0,0], 'Drive':[0,0],'Bus':[0,0],'Total':[0,0]}   
        TravelPixels = {}
        GroupedTravelPixels = {}
        DownsampleSize = 7
        if CurTime in incoming:
           PointList = incoming[CurTime]
           TotalTravel['Total'][0] = len(PointList)
           for PointData in PointList:
               if 'bike' == PointData[1]:
                   TotalTravel['Bike'][0] = TotalTravel['Bike'][0] + 1
               elif 'drive' == PointData[1]:
                   TotalTravel['Drive'][0] = TotalTravel['Drive'][0] + 1
               else:
                   TotalTravel['Bus'][0] = TotalTravel['Bus'][0] + 1    
               Point = PointData[0]
               PointTuple = (BorderWidth + int(Point[0] * Scaling), DesiredHeight + BorderWidth - int(Point[1] * Scaling))
               TravelPixels[PointTuple] = RGBRed
               GroupedPointTuple = (int(PointTuple[0]/DownsampleSize), int(PointTuple[1]/DownsampleSize))
               if GroupedPointTuple in GroupedTravelPixels:
                   GroupedTravelPixels[GroupedPointTuple].append((PointTuple, RGBRed))
               else:
                   GroupedTravelPixels[GroupedPointTuple] = [(PointTuple, RGBRed)]

        if CurTime in outgoing:
           PointList = outgoing[CurTime]
           TotalTravel['Total'][1] = len(PointList)
           for PointData in PointList:
               if 'bike' == PointData[1]:
                   TotalTravel['Bike'][1] = TotalTravel['Bike'][1] + 1
               elif 'drive' == PointData[1]:
                   TotalTravel['Drive'][1] = TotalTravel['Drive'][1] + 1
               else:
                   TotalTravel['Bus'][1] = TotalTravel['Bus'][1] + 1
               Point = PointData[0]
               PointTuple = (BorderWidth + int(Point[0] * Scaling), DesiredHeight + BorderWidth - int(Point[1] * Scaling))
               GroupedPointTuple = (int(PointTuple[0]/DownsampleSize), int(PointTuple[1]/DownsampleSize))
               if GroupedPointTuple in GroupedTravelPixels:
                   GroupedTravelPixels[GroupedPointTuple].append((PointTuple, RGBBlue))
               else:
                   GroupedTravelPixels[GroupedPointTuple] = [(PointTuple, RGBBlue)]
               if PointTuple in TravelPixels:
                   if TravelPixels[PointTuple] == RGBRed:
                       TravelPixels[PointTuple] = RGBPurple
               else:
                   TravelPixels[PointTuple] = RGBBlue
                   
        def OutputGroupedTravelPixels(imagefile, groupedpixels):
            for PixelDownsample, PixelDataLocation in sorted(groupedpixels.items()):
                FinalColor = [0, 0, 0]
                Location = [0, 0]
                for PixelData in PixelDataLocation:
                    Location[0] += PixelData[0][0]
                    Location[1] += PixelData[0][1]
                    if PixelData[1] == RGBRed:
                        FinalColor[0] += RGBRed[0]
                        FinalColor[1] += RGBRed[1]
                        FinalColor[2] += RGBRed[2]
                    else:
                        FinalColor[0] += RGBBlue[0]
                        FinalColor[1] += RGBBlue[1]
                        FinalColor[2] += RGBBlue[2]
                
                FinalColor[0] = int(FinalColor[0] / len(PixelDataLocation))
                FinalColor[1] = int(FinalColor[1] / len(PixelDataLocation))
                FinalColor[2] = int(FinalColor[2] / len(PixelDataLocation))
                Location[0] = int(Location[0] / len(PixelDataLocation))
                Location[1] = int(Location[1] / len(PixelDataLocation))
                Diameter = 2
                if len(PixelDataLocation) < 4:
                    Diameter = 0.5
                elif len(PixelDataLocation) < 9:
                    Diameter = 1
                elif len(PixelDataLocation) < 16:
                    Diameter = 1.5
                #Location = (int(PixelDownsample[0] * 3) + 1, int(PixelDownsample[1] * 3) + 1)
                OutputHTMLIndent(imagefile,2)
                OutputSVGCircle(imagefile,Location,Diameter,FinalColor)    
        OutputGroupedTravelPixels(OutputImageFile, GroupedTravelPixels)
        #for PixelLocation in TravelPixels:
        #    OutputHTMLIndent(OutputImageFile,2)  
        #    OutputSVGCircle(OutputImageFile,PixelLocation,1,TravelPixels[PixelLocation])


        PixelLocation = (4, DesiredHeight+BorderWidth+BorderWidth/4)
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGCircle(OutputImageFile,PixelLocation, 1, RGBRed)
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGText(OutputImageFile,8,PixelLocation[1],RGBBlack,'middle','right', "Incoming")
        PixelLocation = (4, DesiredHeight+BorderWidth+(BorderWidth*3/4))
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGCircle(OutputImageFile,PixelLocation, 1, RGBBlue)
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGText(OutputImageFile,8,PixelLocation[1],RGBBlack,'middle','right', "Outgoing")
            
        #OutputHTMLIndent(OutputImageFile,2)
        OutputSVGTail(OutputImageFile)
        OutputImageFile.close()
        
        OutputHTMLIndent(OutputFile,2)
        OutputHTMLHeader2(OutputFile,'Travelers:')
        OutputHTMLIndent(OutputFile,2)
        OutputHTMLTableBegin(OutputFile, 1)
        
        OutputHTMLIndent(OutputFile,2)
        OutputHTMLTableRow(OutputFile,['','To Campus','From Campus'])
        OutputHTMLIndent(OutputFile,2)
        OutputHTMLTableRow(OutputFile,['Bike',locale.format_string("%d",TotalTravel['Bike'][0], True) ,locale.format_string("%d",TotalTravel['Bike'][1], True)])
        OutputHTMLIndent(OutputFile,2)
        OutputHTMLTableRow(OutputFile,['Bus',locale.format_string("%d",TotalTravel['Bus'][0],True) ,locale.format_string("%d",TotalTravel['Bus'][1],True)])
        OutputHTMLIndent(OutputFile,2)
        OutputHTMLTableRow(OutputFile,['Drive',locale.format_string("%d",TotalTravel['Drive'][0],True) ,locale.format_string("%d",TotalTravel['Drive'][1],True)])
        OutputHTMLIndent(OutputFile,2)
        OutputHTMLTableRow(OutputFile,['Total',locale.format_string("%d",TotalTravel['Total'][0],True) ,locale.format_string("%d",TotalTravel['Total'][1],True)])

        OutputHTMLIndent(OutputFile,2)
        OutputHTMLTableEnd(OutputFile)
        
        OutputHTMLIndent(OutputFile,2)
        OutputHTMLHeader2(OutputFile,'Biking' )
        
        OutputImageFileName = "Biking"+str(CurTime)+".svg"
        OutputImageFile = open(ResultsDirectory+OutputImageFileName, 'w')
        OutputHTMLIndent(OutputFile,4)
        OutputHTMLImage(OutputFile, OutputImageFileName, DesiredWidth + 2 * BorderWidth, DesiredHeight + 2 * BorderWidth)
        
        OutputSVGDocType(OutputImageFile)
        OutputSVGHead(OutputImageFile, DesiredWidth + 2 * BorderWidth, DesiredHeight + 2 * BorderWidth, True)

        for Edge in bikepathmap.StreetMap.EdgeList:
           Source = bikepathmap.StreetMap.PointDB[Edge[0]]
           Source = (BorderWidth + int(Source[0] * Scaling), DesiredHeight + BorderWidth - int(Source[1] * Scaling))
           Dest = bikepathmap.StreetMap.PointDB[Edge[1]]
           Dest = (BorderWidth + int(Dest[0] * Scaling), DesiredHeight + BorderWidth - int(Dest[1] * Scaling))
           EdgeColor = RGBBlack
           if Edge in bikepathmap.EndPointsToEdge:
               EdgeColor = RGBGreen
           OutputHTMLIndent(OutputImageFile,2)
           OutputSVGLine(OutputImageFile, Source, Dest, EdgeColor, 2)
           
        TravelPixels = {}
        GroupedTravelPixels = {}
        if CurTime in incoming:
           PointList = incoming[CurTime]
           for PointData in PointList:
               if PointData[1] == 'bike':
                   Point = PointData[0]
                   PointTuple = (BorderWidth + int(Point[0] * Scaling), DesiredHeight + BorderWidth - int(Point[1] * Scaling))
                   TravelPixels[PointTuple] = RGBRed
                   GroupedPointTuple = (int(PointTuple[0]/DownsampleSize), int(PointTuple[1]/DownsampleSize))
                   if GroupedPointTuple in GroupedTravelPixels:
                       GroupedTravelPixels[GroupedPointTuple].append((PointTuple, RGBRed))
                   else:
                       GroupedTravelPixels[GroupedPointTuple] = [(PointTuple, RGBRed)]
        if CurTime in outgoing:
           PointList = outgoing[CurTime]
           for PointData in PointList:
               if PointData[1] == 'bike':
                   Point = PointData[0]
                   PointTuple = (BorderWidth + int(Point[0] * Scaling), DesiredHeight + BorderWidth - int(Point[1] * Scaling))
                   GroupedPointTuple = (int(PointTuple[0]/DownsampleSize), int(PointTuple[1]/DownsampleSize))
                   if GroupedPointTuple in GroupedTravelPixels:
                       GroupedTravelPixels[GroupedPointTuple].append((PointTuple, RGBBlue))
                   else:
                       GroupedTravelPixels[GroupedPointTuple] = [(PointTuple, RGBBlue)]
                   if PointTuple in TravelPixels:
                       if TravelPixels[PointTuple] == RGBRed:
                           TravelPixels[PointTuple] = RGBPurple
                   else:
                       TravelPixels[PointTuple] = RGBBlue
        #for PixelLocation in TravelPixels:
        #    OutputHTMLIndent(OutputImageFile,2)
        #    OutputSVGCircle(OutputImageFile,PixelLocation,1,TravelPixels[PixelLocation])  
        OutputGroupedTravelPixels(OutputImageFile, GroupedTravelPixels)
        
        PixelLocation = (4, DesiredHeight+BorderWidth+BorderWidth/4)
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGCircle(OutputImageFile,PixelLocation, 1, RGBRed)
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGText(OutputImageFile,8,PixelLocation[1],RGBBlack,'middle','right', "Incoming")
        PixelLocation = (4, DesiredHeight+BorderWidth+(BorderWidth*3/4))
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGCircle(OutputImageFile,PixelLocation, 1, RGBBlue)
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGText(OutputImageFile,8,PixelLocation[1],RGBBlack,'middle','right', "Outgoing")
        
        #OutputHTMLIndent(OutputImageFile,2)
        OutputSVGTail(OutputImageFile)
        OutputImageFile.close()
        
        
        ArrivalLoops = busschedule.GetArrivalLoops(CurTime)
        ArrivalsThisHour = []
        for ArrivalLoop in ArrivalLoops:
            BusRouteName = ArrivalLoop[0]
            for LoopIndex in ArrivalLoop[1]:
                ArrivalTime = busschedule.BusRoutes[BusRouteName].RouteTimes[LoopIndex][-1]
                if ((CurTime-1) * 3600 < ArrivalTime) or (MinimumCampusHour == CurTime):
                    if (BusRouteName, LoopIndex) in busschedule.Ridership:
                        if 0 < busschedule.Ridership[(BusRouteName, LoopIndex)][-1]:
                            ArrivalsThisHour.append((BusRouteName, LoopIndex))
        
        DepartureLoops = busschedule.GetDepartureLoops(CurTime)
        DeparturesThisHour = []
        for DepartureLoop in DepartureLoops:
            BusRouteName = DepartureLoop[0]
            for LoopIndex in DepartureLoop[1]:
                DepartureTime = busschedule.BusRoutes[BusRouteName].RouteTimes[LoopIndex][0]
                if ((CurTime+1) * 3600 > DepartureTime) or ((MinimumCampusHour + TotalCamupsHours + 1) == CurTime):
                    if (BusRouteName, LoopIndex) in busschedule.Ridership:
                        if 0 < busschedule.Ridership[(BusRouteName, LoopIndex)][0]:
                            DeparturesThisHour.append((BusRouteName, LoopIndex))
        BusPathEdges = {}
        AllBusLoops = list(ArrivalsThisHour)
        AllBusLoops.extend( list(DeparturesThisHour) )
        AllBusStops = {}
        for BusLoop in AllBusLoops:
            FullPath = busschedule.BusRoutes[BusLoop[0]].CalculateFullPath()
            if 0 != len(FullPath):
                LastNode = FullPath[0]
                for CurNode in FullPath[1:]:
                    if LastNode < CurNode:
                        BusPathEdges[(LastNode,CurNode)] = True
                    else:
                        BusPathEdges[(CurNode,LastNode)] = True
                    LastNode = CurNode
                for CurStop in busschedule.BusRoutes[BusLoop[0]].RoutePath:
                    AllBusStops[CurStop] = True
                          
        OutputHTMLIndent(OutputFile,2)
        OutputHTMLHeader2(OutputFile,'Bus' )
        
        OutputImageFileName = "Bus"+str(CurTime)+".svg"
        OutputImageFile = open(ResultsDirectory+OutputImageFileName, 'w')
        OutputHTMLIndent(OutputFile,4)
        OutputHTMLImage(OutputFile, OutputImageFileName, DesiredWidth + 2 * BorderWidth, DesiredHeight + 2 * BorderWidth)
        
        OutputSVGDocType(OutputImageFile)
        OutputSVGHead(OutputImageFile, DesiredWidth + 2 * BorderWidth, DesiredHeight + 2 * BorderWidth, True)

        for Edge in streetmap.EdgeList:
           Source = streetmap.PointDB[Edge[0]]
           Source = (BorderWidth + int(Source[0] * Scaling), DesiredHeight + BorderWidth - int(Source[1] * Scaling))
           Dest = streetmap.PointDB[Edge[1]]
           Dest = (BorderWidth + int(Dest[0] * Scaling), DesiredHeight + BorderWidth - int(Dest[1] * Scaling))
           OutputHTMLIndent(OutputImageFile,2)
           if Edge in BusPathEdges:
               OutputSVGLine(OutputImageFile, Source, Dest, RGBGreen, 2)
           else:
               OutputSVGLine(OutputImageFile, Source, Dest, RGBBlack, 2)
           
        for CurBusStop in AllBusStops:
            Center = streetmap.PointDB[CurBusStop]
            Center = (BorderWidth + int(Center[0] * Scaling), DesiredHeight + BorderWidth - int(Center[1] * Scaling))

            OutputHTMLIndent(OutputImageFile,2)
            OutputSVGCircle(OutputImageFile,Center,5,RGBGreen)
           
        TravelPixels = {}
        GroupedTravelPixels = {}
        if CurTime in incoming:
           PointList = incoming[CurTime]
           for PointData in PointList:
               if (PointData[1] != 'bike') and (PointData[1] != 'drive'):
                   Point = PointData[0]
                   PointTuple = (BorderWidth + int(Point[0] * Scaling), DesiredHeight + BorderWidth - int(Point[1] * Scaling))
                   TravelPixels[PointTuple] = RGBRed
                   GroupedPointTuple = (int(PointTuple[0]/DownsampleSize), int(PointTuple[1]/DownsampleSize))
                   if GroupedPointTuple in GroupedTravelPixels:
                       GroupedTravelPixels[GroupedPointTuple].append((PointTuple, RGBRed))
                   else:
                       GroupedTravelPixels[GroupedPointTuple] = [(PointTuple, RGBRed)]
        if CurTime in outgoing:
           PointList = outgoing[CurTime]
           for PointData in PointList:
               if (PointData[1] != 'bike') and (PointData[1] != 'drive'):
                   Point = PointData[0]
                   PointTuple = (BorderWidth + int(Point[0] * Scaling), DesiredHeight + BorderWidth - int(Point[1] * Scaling))
                   GroupedPointTuple = (int(PointTuple[0]/DownsampleSize), int(PointTuple[1]/DownsampleSize))
                   if GroupedPointTuple in GroupedTravelPixels:
                       GroupedTravelPixels[GroupedPointTuple].append((PointTuple, RGBRed))
                   else:
                       GroupedTravelPixels[GroupedPointTuple] = [(PointTuple, RGBRed)]
                   if PointTuple in TravelPixels:
                       if TravelPixels[PointTuple] == RGBRed:
                           TravelPixels[PointTuple] = RGBPurple
                   else:
                       TravelPixels[PointTuple] = RGBBlue
        #for PixelLocation in TravelPixels:
        #    OutputHTMLIndent(OutputImageFile,2)
        #    OutputSVGCircle(OutputImageFile,PixelLocation,1,TravelPixels[PixelLocation])
        OutputGroupedTravelPixels(OutputImageFile, GroupedTravelPixels)
            
        PixelLocation = (2, DesiredHeight+BorderWidth-(BorderWidth*3/4))
        DestLocation = (8,PixelLocation[1])
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGLine(OutputImageFile, PixelLocation, DestLocation, RGBGreen, 2)
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGText(OutputImageFile,10,PixelLocation[1],RGBBlack,'middle','right', "Bus Route")
        PixelLocation = (5, DesiredHeight+BorderWidth-BorderWidth/4)
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGCircle(OutputImageFile,PixelLocation, 5, RGBGreen)
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGText(OutputImageFile,10,PixelLocation[1],RGBBlack,'middle','right', "Bus Stop")
        PixelLocation = (5, DesiredHeight+BorderWidth+BorderWidth/4)
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGCircle(OutputImageFile,PixelLocation, 1, RGBRed)
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGText(OutputImageFile,10,PixelLocation[1],RGBBlack,'middle','right', "Incoming")
        PixelLocation = (5, DesiredHeight+BorderWidth+(BorderWidth*3/4))
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGCircle(OutputImageFile,PixelLocation, 1, RGBBlue)
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGText(OutputImageFile,10,PixelLocation[1],RGBBlack,'middle','right', "Outgoing")
        
        #OutputHTMLIndent(OutputImageFile,2)
        OutputSVGTail(OutputImageFile)
        OutputImageFile.close()
        
        
        if 0 < len(ArrivalsThisHour):
            
            OutputHTMLText(OutputFile,"<BR>\n")
            OutputHTMLBoldText(OutputFile,"Bus Arrival Statistics")
            ArrivalsThisHour.sort()
            LastRouteName = ''
            for ArrivalThisHour in ArrivalsThisHour:
                if not ArrivalThisHour[0] == LastRouteName:
                    if 0 < len(LastRouteName):
                        OutputHTMLTableEnd(OutputFile)    
                        OutputHTMLText(OutputFile,'<BR>\n')
                    OutputHTMLTableBegin(OutputFile, 1)
                    
                    Header = [ArrivalThisHour[0], 'Buses', 'Campus']
                    for StopName in busschedule.BusRoutes[ArrivalThisHour[0]].RoutePath:
                        Header.append(StopName)
                    Header.append('Campus')
                    OutputHTMLTableRow(OutputFile, Header)
                    LastRouteName = ArrivalThisHour[0]
                if (ArrivalThisHour[0], ArrivalThisHour[1]) in busschedule.Ridership:
                    RiderShipInfo = busschedule.Ridership[ (ArrivalThisHour[0], ArrivalThisHour[1]) ]
                    BusesNeeded = int(max(1,(max(RiderShipInfo) + busschedule.LineOccupancy[ArrivalThisHour[0]] - 1) / busschedule.LineOccupancy[ArrivalThisHour[0]]))
                    Row = ['Loop '+str(ArrivalThisHour[1]+1) + ' (' + ConvertSecondsToTime(busschedule.BusRoutes[ArrivalThisHour[0]].RouteStartTimes[ArrivalThisHour[1]]) + ')', locale.format_string("%d",BusesNeeded, True) ]
                    for Capacity in RiderShipInfo:
                        Row.append(Capacity)
                else:
                    Row = ['Loop '+str(ArrivalThisHour[1]+1) + ' (' + ConvertSecondsToTime(busschedule.BusRoutes[ArrivalThisHour[0]].RouteStartTimes[ArrivalThisHour[1]]) + ')', '1', '0' ]
                    for StopName in busschedule.BusRoutes[ArrivalThisHour[0]].RoutePath:
                        Row.append('0')
                    Row.append('0')
                OutputHTMLTableRow(OutputFile, Row)    
            OutputHTMLTableEnd(OutputFile)   
        
        if 0 < len(DeparturesThisHour):
            OutputHTMLText(OutputFile,"<BR>\n")
            OutputHTMLBoldText(OutputFile,"Bus Departure Statistics")
            DeparturesThisHour.sort()
            LastRouteName = ''
            for DepartureThisHour in DeparturesThisHour:
                if not DepartureThisHour[0] == LastRouteName:
                    if 0 < len(LastRouteName):
                        OutputHTMLTableEnd(OutputFile)    
                        OutputHTMLText(OutputFile,'<BR>\n')
                    OutputHTMLTableBegin(OutputFile, 1)
                    
                    Header = [DepartureThisHour[0], 'Buses', 'Campus']
                    for StopName in busschedule.BusRoutes[DepartureThisHour[0]].RoutePath:
                        Header.append(StopName)
                    Header.append('Campus')
                    OutputHTMLTableRow(OutputFile, Header)
                    LastRouteName = DepartureThisHour[0]
                if (DepartureThisHour[0], DepartureThisHour[1]) in busschedule.Ridership:
                    RiderShipInfo = busschedule.Ridership[ (DepartureThisHour[0], DepartureThisHour[1]) ]
                    BusesNeeded = int(max(1,(max(RiderShipInfo) + busschedule.LineOccupancy[DepartureThisHour[0]] - 1) / busschedule.LineOccupancy[DepartureThisHour[0]]))
                    Row = ['Loop '+str(DepartureThisHour[1]+1) + ' (' + ConvertSecondsToTime(busschedule.BusRoutes[DepartureThisHour[0]].RouteStartTimes[DepartureThisHour[1]]) + ')', locale.format_string("%d",BusesNeeded, True) ]
                    for Capacity in RiderShipInfo:
                        Row.append(Capacity)
                else:
                    Row = ['Loop '+str(DepartureThisHour[1]+1) + ' (' + ConvertSecondsToTime(busschedule.BusRoutes[DepartureThisHour[0]].RouteStartTimes[DepartureThisHour[1]]) + ')', '1', '0' ]
                    for StopName in busschedule.BusRoutes[DepartureThisHour[0]].RoutePath:
                        Row.append('0')
                    Row.append('0')
                OutputHTMLTableRow(OutputFile, Row)    
            OutputHTMLTableEnd(OutputFile)   
        
        OutputHTMLIndent(OutputFile,2)
        OutputHTMLHeader2(OutputFile,'Driving' )
        
        OutputImageFileName = "Driving"+str(CurTime)+".svg"
        OutputImageFile = open(ResultsDirectory+OutputImageFileName, 'w')
        OutputHTMLIndent(OutputFile,4)
        OutputHTMLImage(OutputFile, OutputImageFileName, DesiredWidth + 2 * BorderWidth, DesiredHeight + 2 * BorderWidth)
        
        OutputSVGDocType(OutputImageFile)
        OutputSVGHead(OutputImageFile, DesiredWidth + 2 * BorderWidth, DesiredHeight + 2 * BorderWidth, True)
        
        for Edge in streetmap.EdgeList:
           Source = streetmap.PointDB[Edge[0]]
           Source = (BorderWidth + int(Source[0] * Scaling), DesiredHeight + BorderWidth - int(Source[1] * Scaling))
           Dest = streetmap.PointDB[Edge[1]]
           Dest = (BorderWidth + int(Dest[0] * Scaling), DesiredHeight + BorderWidth - int(Dest[1] * Scaling))
           OutputHTMLIndent(OutputImageFile,2)
           OutputSVGLine(OutputImageFile, Source, Dest, RGBBlack, 2)
           
        TravelPixels = {}
        GroupedTravelPixels = {}
        if CurTime in incoming:
           PointList = incoming[CurTime]
           for PointData in PointList:
               if PointData[1] == 'drive':
                   Point = PointData[0]
                   PointTuple = (BorderWidth + int(Point[0] * Scaling), DesiredHeight + BorderWidth - int(Point[1] * Scaling))
                   TravelPixels[PointTuple] = RGBRed
                   GroupedPointTuple = (int(PointTuple[0]/DownsampleSize), int(PointTuple[1]/DownsampleSize))
                   if GroupedPointTuple in GroupedTravelPixels:
                       GroupedTravelPixels[GroupedPointTuple].append((PointTuple, RGBRed))
                   else:
                       GroupedTravelPixels[GroupedPointTuple] = [(PointTuple, RGBRed)]
        if CurTime in outgoing:
           PointList = outgoing[CurTime]
           for PointData in PointList:
               if PointData[1] == 'drive':
                   Point = PointData[0]
                   PointTuple = (BorderWidth + int(Point[0] * Scaling), DesiredHeight + BorderWidth - int(Point[1] * Scaling))
                   GroupedPointTuple = (int(PointTuple[0]/DownsampleSize), int(PointTuple[1]/DownsampleSize))
                   if GroupedPointTuple in GroupedTravelPixels:
                       GroupedTravelPixels[GroupedPointTuple].append((PointTuple, RGBBlue))
                   else:
                       GroupedTravelPixels[GroupedPointTuple] = [(PointTuple, RGBBlue)]
                   if PointTuple in TravelPixels:
                       if TravelPixels[PointTuple] == RGBRed:
                           TravelPixels[PointTuple] = RGBPurple
                   else:
                       TravelPixels[PointTuple] = RGBBlue
        OutputGroupedTravelPixels(OutputImageFile, GroupedTravelPixels)
        #for PixelLocation in TravelPixels:
        #    OutputHTMLIndent(OutputImageFile,2)
        #    OutputSVGCircle(OutputImageFile,PixelLocation,1,TravelPixels[PixelLocation])
            
        PixelLocation = (4, DesiredHeight+BorderWidth+BorderWidth/4)
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGCircle(OutputImageFile,PixelLocation, 1, RGBRed)
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGText(OutputImageFile,8,PixelLocation[1],RGBBlack,'middle','right', "Incoming")
        PixelLocation = (4, DesiredHeight+BorderWidth+(BorderWidth*3/4))
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGCircle(OutputImageFile,PixelLocation, 1, RGBBlue)
        OutputHTMLIndent(OutputImageFile,2)
        OutputSVGText(OutputImageFile,8,PixelLocation[1],RGBBlack,'middle','right', "Outgoing")
        
        #OutputHTMLIndent(OutputImageFile,2)
        OutputSVGTail(OutputImageFile)
        OutputImageFile.close()
        
        OutputHTMLTail(OutputFile)
        OutputFile.close()
        sys.stdout.write(".")
        sys.stdout.flush()
    




class PersonSchedule:
    def __init__(self, hours):

        LastHour = 8
        self.CampusSchedule = []
        if hours < TotalCamupsHours:
            for Index in range(0,hours):
                SkipAmount = random.randint(0,TotalCamupsHours-1-Index)
                while LastHour in self.CampusSchedule:
                    LastHour = MinimumCampusHour + ((LastHour + 1 - MinimumCampusHour) % TotalCamupsHours)
                while 0 < SkipAmount:
                    LastHour = MinimumCampusHour + ((LastHour + 1 - MinimumCampusHour) % TotalCamupsHours)
                    while LastHour in self.CampusSchedule:
                        LastHour = MinimumCampusHour + ((LastHour + 1 - MinimumCampusHour) % TotalCamupsHours)
                    SkipAmount = SkipAmount - 1
                self.CampusSchedule.append(LastHour) 
            self.CampusSchedule.sort()
        else:
            for Index in range(0,TotalCamupsHours):
                self.CampusSchedule.append(MinimumCampusHour + Index)
        
    def CalculateTravelPlans(self):
        OnCampus = False
        TravelTimes = []
        EndTime = 8
        for CurTime in self.CampusSchedule:
            if not OnCampus:
                TravelTimes.append(CurTime)
                OnCampus = True
            elif EndTime + 3 <= CurTime:
                TravelTimes.append(EndTime)
                TravelTimes.append(CurTime)
            EndTime = CurTime + 1
        TravelTimes.append(EndTime)
        
        return TravelTimes

class ZoneMap:
    def __init__(self):
        self.AllZones = []
        
    def Load(self, filename):
        with open(filename, 'rU') as ZoneFile:
            ZoneFileReader = csv.reader(ZoneFile, delimiter=',')
            self.AllZones = []
            for Row in ZoneFileReader:
                RowData = []
                for Col in Row:
                    RowData.append(float(Col))
                RowData[2] += RowData[0]
                RowData[3] += RowData[1]
                RowData[5] += RowData[4]
                self.AllZones.append(RowData)
        
    def ValidTypeForZone(self, x, y, prob, isstudent):
        for Zone in self.AllZones:
            if Zone[0] <= x and Zone[1] <= y and Zone[2] >= x and Zone[3] >= y:
                if isstudent:
                    return prob < Zone[4]
                else:
                    return Zone[4] <= prob and prob < Zone[5]
        if isstudent:
            return prob < 0.5
        else:
            return 0.5 <= prob

class RandomHomeLocation:
    def __init__(self, streetmap, bikepathmap, outperimeter, zonemap, isstudent):
        while True:
            self.XPosition = (random.random() * 1.05 - 0.025) * streetmap.MaxX
            self.YPosition = (random.random() * 1.05 - 0.025) * streetmap.MaxY
            if not zonemap.ValidTypeForZone(self.XPosition, self.YPosition, random.random(), isstudent):
                continue
            self.NearestStreetInfo = streetmap.FindNearestEdgeAndDistance(self.XPosition, self.YPosition)
            self.NearestBikePathInfo = bikepathmap.FindNearestEdgeLocationInArea(self.XPosition, self.YPosition, -1)
            if streetmap.InsidePerimeter(self.XPosition, self.YPosition):
                break
            if self.NearestStreetInfo[1] < outperimeter:
                break
                
                
class PersonScheduleHome:
    def __init__(self, hours, anchor, streetmap, bikepathmap, outperimeter, zonemap, isstudent):
        self.Schedule = PersonSchedule(hours)
        self.RouteAnchor = anchor
        self.Home = RandomHomeLocation(streetmap, bikepathmap, outperimeter, zonemap, isstudent)
        self.StreetMap = streetmap
        self.BikePathMap = bikepathmap
        self.BikeProbability = random.random()
        self.BusProbability = random.random()
        self.TravelTimes = []
        self.TravelMethod = 'drive'
        self.TravelOptions = []
        self.TravelDistance = 0.0
        self.IsStudent = isstudent
        
    def CalculateTravelPlans(self, busschedule, costbus, parking, mileage, wage, maxbus):
        TravelTimes = self.Schedule.CalculateTravelPlans()
        self.TravelTimes = TravelTimes
        TravelPlans = self.Schedule.CalculateTravelPlans()
        
        # Calculate Driving distance
        BikePosition1 = self.Home.NearestBikePathInfo[0]
        BikePosition2 = self.Home.NearestBikePathInfo[1]
        DistanceRatio = self.Home.NearestBikePathInfo[2]
        NearestIsBikePath = (BikePosition1, BikePosition2) in self.BikePathMap.EndPointsToEdge
        PathLength = CalculateDistancePoint(self.BikePathMap.StreetMap.PointDB[BikePosition1], self.BikePathMap.StreetMap.PointDB[BikePosition2])
        DistanceToPath = SegmentPointCalculateDistance(self.BikePathMap.StreetMap.PointDB[BikePosition1], self.BikePathMap.StreetMap.PointDB[BikePosition2], self.HomeLocation())
        DistanceToStop1 = DistanceToPath + DistanceRatio * PathLength
        if BikePosition1 != self.RouteAnchor:
            BikeDistance1 = DistanceToStop1 + self.BikePathMap.StreetMap.ShortestPathDistanceDB[ (BikePosition1, self.RouteAnchor) ]
        else:
            BikeDistance1 = DistanceToStop1
        DistanceToStop2 = DistanceToPath + (1.0 - DistanceRatio) * PathLength
        if BikePosition2 != self.RouteAnchor:        
            BikeDistance2 = DistanceToStop2 + self.BikePathMap.StreetMap.ShortestPathDistanceDB[ (BikePosition2, self.RouteAnchor) ]
        else:
            BikeDistance2 = DistanceToStop2
        if BikeDistance1 < BikeDistance2:
            BikePosition = BikePosition1
            BikeDistance = BikeDistance1
            BikeDistanceToStop = DistanceToStop1
        else:
            BikePosition = BikePosition2
            BikeDistance = BikeDistance2
            BikeDistanceToStop = DistanceToStop2
        
        if BikePosition != self.RouteAnchor:
            BikeTime = self.BikePathMap.StreetMap.FastestPathDurationDB[ (BikePosition,self.RouteAnchor) ] + self.BikePathMap.StreetMap.FastestPathDurationDB[ (self.RouteAnchor, BikePosition) ]
        else:
            BikeTime = 0.0
        BikeTime += (2 * BikeDistanceToStop / self.BikePathMap.SpeedLimit) * 3600.0
        BikeTime *= len(TravelTimes)
        #BikeTime *= 2.0 #math.log(3.0 + math.log(BikeTime))
        if not NearestIsBikePath:
            BikeTime *= math.log(BikeTime)
        
        # Calculate Driving distance
        DrivePosition1 = self.Home.NearestStreetInfo[0][0]
        DrivePosition2 = self.Home.NearestStreetInfo[0][1]
        DistanceToStop1 = CalculateDistancePoint( self.HomeLocation(), self.StreetMap.PointDB[DrivePosition1] )
        if DrivePosition1 != self.RouteAnchor:
            DriveDistance1 = DistanceToStop1 + self.StreetMap.ShortestPathDistanceDB[ (DrivePosition1, self.RouteAnchor) ]
        else:
            DriveDistance1 = DistanceToStop1
        DistanceToStop2 = CalculateDistancePoint( self.HomeLocation(), self.StreetMap.PointDB[DrivePosition2] )
        if DrivePosition2 != self.RouteAnchor:        
            DriveDistance2 = DistanceToStop2 + self.StreetMap.ShortestPathDistanceDB[ (DrivePosition2, self.RouteAnchor) ]
        else:
            DriveDistance2 = DistanceToStop2
        if DriveDistance1 < DriveDistance2:
            DrivePosition = DrivePosition1
            DriveDistance = DriveDistance1
            DriveDistanceToStop = DistanceToStop1
        else:
            DrivePosition = DrivePosition2
            DriveDistance = DriveDistance2
            DriveDistanceToStop = DistanceToStop2
            
        if DrivePosition != self.RouteAnchor:
            DriveTime = self.StreetMap.FastestPathDurationDB[ (DrivePosition,self.RouteAnchor) ] + self.StreetMap.FastestPathDurationDB[ (self.RouteAnchor, DrivePosition) ]
            FastestPathDistance = self.StreetMap.FastestPathDistanceDB[ (DrivePosition,self.RouteAnchor) ] + self.StreetMap.FastestPathDistanceDB[ (self.RouteAnchor, DrivePosition) ]
        else:
            DriveTime = 0.0
            FastestPathDistance = 0.0
        FastestPathDistance += 2 * DriveDistanceToStop
        DriveTime += (2 * DriveDistanceToStop / self.StreetMap.SpeedDB[ self.Home.NearestStreetInfo[0] ]) * 3600.0
        DriveTime += 600.0 # add walk time
        DriveTime *= len(TravelTimes)
        DriveTime += ((parking + FastestPathDistance * mileage * len(TravelPlans)) / wage) * 3600.0
            
        self.TravelDistance = DriveDistance
        self.TravelOptions = []
        if 0.25 > BikeDistance:
            self.TravelMethod = 'bike'
            return (TravelTimes,'bike', self.TravelDistance)
        #elif (0.25 / BikeDistance) > self.BikePobability:
        #    self.TravelMethod = 'bike'
        #    return (TravelTimes,'bike', self.TravelDistance)
        
        BusPossible = True
        BusTravelTime = (costbus / wage) * len(TravelPlans) * 3600.0
        BusTravelTime += 600.0 * len(TravelPlans) # add in walk time
        for Index in range(0, len(TravelPlans), 2):
            BusOptionsTo = busschedule.RouteOptionsToStation(self.HomeLocation(), TravelPlans[Index] )
            if 0 == len(BusOptionsTo):
                self.TravelOptions = []
                #self.TravelMethod = 'drive'
                #return (TravelTimes,'drive', self.TravelDistance)
                BusPossible = False 
                break
            BusOptionsFrom = busschedule.RouteOptionsFromStation(self.HomeLocation(), TravelPlans[Index+1] )
            if 0 == len(BusOptionsFrom):
                self.TravelOptions = []
                #self.TravelMethod = 'drive'
                #return (TravelTimes,'drive', self.TravelDistance)
                BusPossible = False 
                break
                
            self.TravelOptions.append(BusOptionsTo)
            self.TravelOptions.append(BusOptionsFrom)
            BestToTime = -1
            for ToPath in BusOptionsTo:
                CurTime = TravelPlans[Index] * 3600 - ToPath[0] + ToPath[1][0] * 3600.0
                if (0 > BestToTime) or (CurTime < BestToTime):
                    BestToTime = CurTime
            BestFromTime = -1
            for FromPath in BusOptionsFrom:
                CurTime = FromPath[0] - TravelPlans[Index+1] * 3600 + FromPath[1][0] * 3600.0
                if (0 > BestFromTime) or (CurTime < BestFromTime):
                    BestFromTime = CurTime
            BusTravelTime = BusTravelTime + BestToTime + BestFromTime
        
        if BusPossible:
            TotalTime = BikeTime + (DriveTime + BusTravelTime) * 0.5
            if (BikeTime / TotalTime) < self.BikeProbability:
                # as bike time increases probability drops
                self.TravelOptions = []
                self.TravelMethod = 'bike'
                return (TravelTimes,'bike', self.TravelDistance)
            TotalTime = DriveTime + BusTravelTime
            if (BusTravelTime / TotalTime) > self.BusProbability:
                # As bus time drops probability of driving drops
                self.TravelOptions = []
                self.TravelMethod = 'drive'
                return (TravelTimes,'drive',self.TravelDistance) 
        else:
            TotalTime = BikeTime + DriveTime
            if (BikeTime / TotalTime) < self.BikeProbability:
                # as bike time increases probability drops
                self.TravelOptions = []
                self.TravelMethod = 'bike'
                return (TravelTimes,'bike', self.TravelDistance)
            else:
                self.TravelOptions = []
                self.TravelMethod = 'drive'
                return (TravelTimes,'drive', self.TravelDistance)
                
        BusOptionsToTake = []
        for Index in range(0, len(TravelPlans), 2):
            FoundOption = False
            BestToOption = None
            PossibleToOption = None
            for CurrentOption in self.TravelOptions[Index]:
                BussesNeeded = busschedule.BusNeededForRiderToStation(CurrentOption[2],CurrentOption[1][1],CurrentOption[0])
                if(BussesNeeded[0] <= maxbus):
                    FoundOption = True
                    if not PossibleToOption:
                        PossibleToOption = CurrentOption
                    if(BussesNeeded[0] == BussesNeeded[1]):
                        BestToOption = CurrentOption
                        break
            if not FoundOption:
                self.TravelOptions = []
                self.TravelMethod = 'drive'
                return (TravelTimes,'drive',self.TravelDistance) 
            if BestToOption:
                BusOptionsToTake.append(BestToOption)
            else:
                BusOptionsToTake.append(PossibleToOption)
            FoundOption = False
            BestFromOption = None
            PossibleFromOption = None
            for CurrentOption in self.TravelOptions[Index+1]:
                BussesNeeded = busschedule.BusNeededForRiderFromStation(CurrentOption[2],CurrentOption[1][1],CurrentOption[0])
                if(BussesNeeded[0] <= maxbus):
                    FoundOption = True
                    if not PossibleFromOption:
                        PossibleFromOption = CurrentOption
                    if(BussesNeeded[0] == BussesNeeded[1]):
                        BestFromOption = CurrentOption
                        break
            if not FoundOption:
                self.TravelOptions = []
                self.TravelMethod = 'drive'
                return (TravelTimes,'drive',self.TravelDistance) 
            if BestFromOption:
                BusOptionsToTake.append(BestFromOption)
            else:
                BusOptionsToTake.append(PossibleFromOption)
        for Index in range(0, len(TravelPlans), 2):
            CurrentOption = BusOptionsToTake[Index]
            busschedule.AddRiderToStation(CurrentOption[2],CurrentOption[1][1],CurrentOption[0])
            CurrentOption = BusOptionsToTake[Index+1]
            busschedule.AddRiderFromStation(CurrentOption[2],CurrentOption[1][1],CurrentOption[0])
            
        self.TravelMethod = 'bus'
        return (TravelTimes,'bus',self.TravelDistance, self.TravelOptions)

        
    def GetTravelPlans(self):
        if self.TravelMethod == 'bus':
            return (self.TravelTimes,'bus',self.TravelDistance, self.TravelOptions)
        return (self.TravelTimes, self.TravelMethod, self.TravelDistance)
        
    def HomeLocation(self):
        return (self.Home.XPosition, self.Home.YPosition)
   
def SimulateVehicleOnTraces(vehtype, allvehicles, trace):
    CO2FuelLookup = {"gasoline":99.18,"biodiesel":83.25,"e85":76.9,"electricity":124.10}

    # Initialize Powertrain
    VehicleEngine = None
    if allvehicles.GetParameter(vehtype,'Engine'):
        VehicleEngine = EngineEfficiencyMap(DataDirectory+allvehicles.GetParameter(vehtype,'Engine'))
 
    VehicleMotor = None
    if allvehicles.GetParameter(vehtype,'Motor'):
        VehicleMotor = EfficiencyMap(DataDirectory+allvehicles.GetParameter(vehtype,'Motor'))
      
    TractionBattery = None
    if allvehicles.GetParameter(vehtype,'BatteryPower'):
        if allvehicles.GetParameter(vehtype,'BatteryCapacity'):
            Capacity = float(allvehicles.GetParameter(vehtype,'BatteryCapacity'))
            TractionBattery = Battery(float(allvehicles.GetParameter(vehtype,'BatteryPower')),Capacity,0.60 * Capacity)

    TransEff = float(allvehicles.GetParameter(vehtype,'Efficiency'))
    Gears = int(allvehicles.GetParameter(vehtype,'Gears'))
    GearRatios = []        
    for Index in range(0,Gears):
        GearRatios.append(float(allvehicles.GetParameter(vehtype,'R' + str(Index+1))))
    if (2 != Gears) or (0 < min(GearRatios)):
        TempList = [10000.0]
        TempList.extend(GearRatios)
        GearRatios = TempList
    VehicleTransmission = Transmission(TransEff, tuple(GearRatios))
    VehicleGlider = VehicleLoad()
    VehicleGlider.Mass = float(allvehicles.GetParameter(vehtype,'Mass'))
    VehicleGlider.Area = float(allvehicles.GetParameter(vehtype,'Area'))
    VehicleGlider.CD = float(allvehicles.GetParameter(vehtype,'CD'))
    VehicleGlider.CRR = float(allvehicles.GetParameter(vehtype,'CRR'))
    VehicleGlider.TireRadius = float(allvehicles.GetParameter(vehtype,'Tire'))
    VehicleGlider.DifferentialRatio = float(allvehicles.GetParameter(vehtype,'Differential'))
    VehicleGlider.DifferentialEfficiency = 0.99    # efficiency of differential
    VehiclePowertrain = Powertrain(VehicleEngine, VehicleMotor, TractionBattery, VehicleTransmission, VehicleGlider)
    BaseMass = VehicleGlider.Mass
    Distance = 0.0
    ElectricityWh = 0.0
    FuelGrams = 0.0
    HCGrams = 0.0
    COGrams = 0.0
    NOxGrams = 0.0
    PMGrams = 0.
    TimeStep = 0
    OutputFile = open(ResultsDirectory+vehtype + "cold.csv", 'w', newline='')
    # Create a CSV writer from 
    OutputWriter = csv.writer(OutputFile, quoting=csv.QUOTE_ALL)
    OutputWriter.writerow(['Time','ICE','Coolant','Cat',"HC'","CO'","NOx'","HC","CO","NOx",])
    ColdTrace = trace[0]
    for Segment in ColdTrace:
        PassengerMass = Segment[0] * 80.0
        VehicleGlider.Mass = BaseMass + PassengerMass
        for Speed in Segment[1]:
            # Get time and speed
            TimestepData = VehiclePowertrain.CalculateTimestep(Speed, float(TimeStep))
            # Distance and electrical energy are cumulative
            Distance = TimestepData[2]
            ElectricityWh = TimestepData[6]
            # Grams are per timestep
            FuelGrams += TimestepData[10]
            HCGrams += TimestepData[18]
            COGrams += TimestepData[19]
            NOxGrams += TimestepData[20]
            PMGrams  += TimestepData[21]
            OutputWriter.writerow([TimeStep,TimestepData[16],TimestepData[17],TimestepData[-1],TimestepData[11], TimestepData[12], TimestepData[13], TimestepData[18], TimestepData[19], TimestepData[20]])
            TimeStep += 1

    ColdOverview = [Distance, ElectricityWh, VehiclePowertrain.FuelType(), FuelGrams, HCGrams, COGrams, NOxGrams, PMGrams]
    Distance = 0.0
    ElectricityWh = 0.0
    FuelGrams = 0.0
    HCGrams = 0.0
    COGrams = 0.0
    NOxGrams = 0.0
    PMGrams = 0.
    TimeStep = 0
    VehiclePowertrain.Reset(False)
    HotTrace = trace[1]
    for Segment in HotTrace:
        PassengerMass = Segment[0] * 80.0
        VehicleGlider.Mass = BaseMass + PassengerMass
        for Speed in Segment[1]:
            # Get time and speed
            TimestepData = VehiclePowertrain.CalculateTimestep(Speed, float(TimeStep))
            # Distance and electrical energy are cumulative
            Distance = TimestepData[2]
            ElectricityWh = TimestepData[6]
            # Grams are per timestep
            FuelGrams += TimestepData[10]
            HCGrams += TimestepData[18]
            COGrams += TimestepData[19]
            NOxGrams += TimestepData[20]
            PMGrams  += TimestepData[21]
            TimeStep += 1
    HotOverview = [Distance, ElectricityWh, VehiclePowertrain.FuelType(), FuelGrams, HCGrams, COGrams, NOxGrams, PMGrams]
    return (ColdOverview, HotOverview)

def main():
    #locale.setlocale(locale.LC_NUMERIC, 'en_US')
    SimConfig = SimulationConfiguration()
    if len(glob.glob(DataDirectory+"config.csv")):
        sys.stdout.write("Loading Configuration File : ")
        SimConfig.Load(DataDirectory+"config.csv")
        sys.stdout.write("Done\n")
        
    if SimConfig.Parking() > SimConfig.EmployeeWage() * 4:
        sys.stdout.write("Error                      : Parking is greater than 50% employee daily wage!")
        return
       
    sys.stdout.write("Loading Street Map         : ")
    CityStreetMap = StreetMap(DataDirectory+'streetmap.csv')
    sys.stdout.write("Done\n")
    CityBikePathMap = BikePaths(CityStreetMap)
    if len(glob.glob(DataDirectory+"bikepath.csv")):
        sys.stdout.write("Loading Bike Path File     : ")
        CityBikePathMap.Load(DataDirectory+"bikepath.csv")
        sys.stdout.write("Done\n")
    CityBusStops = BusStops(CityStreetMap)       
    if len(glob.glob(DataDirectory+"busstops.csv")):
        sys.stdout.write("Loading Bus Stops          : ")
        CityBusStops.Load(DataDirectory+"busstops.csv")
        sys.stdout.write("Done\n")
    CityBusRoutes = {}
    sys.stdout.write("Loading Bus Routes         : ")
    for RouteFile in glob.glob(DataDirectory+"route*.csv"):
        NewBusRoute = BusRoute(CityStreetMap, SimConfig.BusStation())
        if NewBusRoute.Load(RouteFile):
            sys.stdout.write(".")
            sys.stdout.flush()
            CityBusRoutes[NewBusRoute.RouteName] = NewBusRoute
    sys.stdout.write(" Done\n")
    CityZoneMap = ZoneMap()
    if len(glob.glob(DataDirectory+"zones.csv")):
        sys.stdout.write("Loading Zone Map           : ")
        CityZoneMap.Load(DataDirectory+"zones.csv")
        sys.stdout.write("Done\n")
    AllVehicles = VehicleParameters(DataDirectory+"vehicleparameters.csv")
    CityBusSchedule = BusSchedule(CityBusStops, CityBusRoutes, 0.5, MinimumCampusHour, MinimumCampusHour + TotalCamupsHours, AllVehicles)
    
    Done = False
    CityStreetMap.UpdatePerimeter()
    sys.stdout.write("Calculating Shortest Routes: ")
    def UpdateFunction():
        sys.stdout.write(".")
        sys.stdout.flush()
    CityStreetMap.CalculateAllBestPathsToDestination(SimConfig.BusStation(),UpdateFunction)
    sys.stdout.write(" Done\n")
    
    sys.stdout.write("Calculating Shortest Paths : ")
    CityBikePathMap.StreetMap.CalculateAllBestPathsToDestination(SimConfig.BusStation(),UpdateFunction)
    sys.stdout.write(" Done\n")
    
    random.seed(123456)
    
    AllIncomingTravelPlans = {}
    AllOutgoingTravelPlans = {}
    AllPeople = []
    AllStudentResults = []
    StudentLocations = []
    AllEmployeeResults = []
    EmployeeLocations = []
    DistanceTravelled = {'Bike':0.0,'Bus':0.0,'Drive':0.0,'Total':0.0,'Student':0.0,'Employee':0.0}
    DriverCount = [0,0]
    BikerCount = 0
    StudentSampleRatio = 1.0 / float(SimConfig.StudentRatio())
    StudentSamples = SimConfig.StudentCount() 
    EmployeeSampleRatio = 1.0 / float(SimConfig.EmployeeRatio())
    EmployeeSamples = SimConfig.EmployeeCount() 
    TotalSamples = StudentSamples + EmployeeSamples
    OnePercent = TotalSamples / 100
    StudentsLeft = StudentSamples
    EmployeesLeft = EmployeeSamples
    
    
    sys.stdout.write("Generating People          : ")
    for PersonIndex in range(0, TotalSamples):    
        if (float(StudentsLeft) / float(StudentsLeft + EmployeesLeft)) > random.random():
            StudentsLeft = StudentsLeft - 1
            NewPersonInfo = PersonScheduleHome(SimConfig.StudentHours(), SimConfig.BusStation(), CityStreetMap, CityBikePathMap, SimConfig.OuterPerimeter(), CityZoneMap, True)
        else:
            EmployeesLeft = EmployeesLeft - 1
            NewPersonInfo = PersonScheduleHome(TotalCamupsHours, SimConfig.BusStation(), CityStreetMap, CityBikePathMap, SimConfig.OuterPerimeter(), CityZoneMap, False)
        AllPeople.append(NewPersonInfo)
        if (OnePercent - 1) == (PersonIndex % OnePercent):
            #UpdatePercentage(int(PersonIndex * 100 / TotalSamples))
            sys.stdout.write(".")
            sys.stdout.flush()
    
    PersonIndex = 0
    sys.stdout.write(" Done\n")
    sys.stdout.write("Generating Travel Plans    : ")
    for NewPersonInfo in AllPeople:    
        if NewPersonInfo.IsStudent:
            NewTravelPlans = NewPersonInfo.CalculateTravelPlans(CityBusSchedule, SimConfig.BusCost(), SimConfig.Parking(), SimConfig.Mileage(), SimConfig.MinimumWage(), SimConfig.MaxBusPerLoop())
            if StudentSampleRatio > random.random():
                StudentLocations.append( NewPersonInfo.Home.NearestStreetInfo[0] )
            if 'drive' == NewTravelPlans[1]:
                DriverCount[0] = DriverCount[0] + 1
                DistanceTravelled['Student'] = DistanceTravelled['Student'] + NewTravelPlans[2] * len(NewTravelPlans[0])
        else:
            NewTravelPlans = NewPersonInfo.CalculateTravelPlans(CityBusSchedule, SimConfig.BusCost(), SimConfig.Parking(), SimConfig.Mileage(), SimConfig.EmployeeWage(), SimConfig.MaxBusPerLoop())
            if EmployeeSampleRatio > random.random():
                EmployeeLocations.append( NewPersonInfo.Home.NearestStreetInfo[0] )
            if 'drive' == NewTravelPlans[1]:
                DriverCount[1] = DriverCount[1] + 1
                DistanceTravelled['Employee'] = DistanceTravelled['Employee'] + NewTravelPlans[2] * len(NewTravelPlans[0])
        CurDistance = NewTravelPlans[2] * len(NewTravelPlans[0])
        DistanceTravelled['Total'] = DistanceTravelled['Total'] + CurDistance
        if 'bike' == NewTravelPlans[1]:
            DistanceTravelled['Bike'] = DistanceTravelled['Bike'] + CurDistance
            BikerCount += 1
        elif 'drive' == NewTravelPlans[1]:
            DistanceTravelled['Drive'] = DistanceTravelled['Drive'] + CurDistance
        else:
            DistanceTravelled['Bus'] = DistanceTravelled['Bus'] + CurDistance
        if (OnePercent - 1) == (PersonIndex % OnePercent):
            sys.stdout.write(".")
            sys.stdout.flush()
        PersonIndex = PersonIndex + 1
    
    sys.stdout.write(" Done\n")
    sys.stdout.write("Generating Travel Maps     : ")
    PersonIndex = 0
    for CurPersonInfo in AllPeople:
        NewTravelPlans = CurPersonInfo.GetTravelPlans()
        NewTravelTimes = NewTravelPlans[0]
        for Index in range(0,len(NewTravelTimes),2): 
            if not NewTravelTimes[Index] in AllIncomingTravelPlans:
                AllIncomingTravelPlans[NewTravelTimes[Index]] = [ (CurPersonInfo.HomeLocation(), NewTravelPlans[1])]
            else:
                AllIncomingTravelPlans[NewTravelTimes[Index]].append( (CurPersonInfo.HomeLocation(), NewTravelPlans[1]))
                
            if not NewTravelTimes[Index+1] in AllOutgoingTravelPlans:
                AllOutgoingTravelPlans[NewTravelTimes[Index+1]] = [ (CurPersonInfo.HomeLocation(), NewTravelPlans[1])]
            else:
                AllOutgoingTravelPlans[NewTravelTimes[Index+1]].append( (CurPersonInfo.HomeLocation(), NewTravelPlans[1])) 
        if (OnePercent - 1) == (PersonIndex % OnePercent):
            sys.stdout.write(".")
            sys.stdout.flush()
        PersonIndex = PersonIndex+ 1
    sys.stdout.write(" Done\n")
    BusEvents = []
    BusDepot = {}
    RouteResults = {}
    BusLeaveTimes = []
    BusDriversAtDepot = [] 
    BusDriverSeconds = 0.0
    sys.stdout.write("Generating Traces          : ")
    for BusRouteName in CityBusRoutes:
        RouteTraceInfo = CityBusSchedule.GenerateDriveTrace(BusRouteName)
        RouteResults[BusRouteName] = SimulateVehicleOnTraces(CityBusRoutes[BusRouteName].BusType, AllVehicles, RouteTraceInfo)
        LoopIndex = 0
        for RouteStopTimes in CityBusRoutes[BusRouteName].RouteTimes:
            for BusIndex in range(0, RouteTraceInfo[2][LoopIndex]):
                BusEvents.append((RouteStopTimes[0],BusRouteName,CityBusRoutes[BusRouteName].BusType,'Start'))
                BusEvents.append((RouteStopTimes[-1],BusRouteName,CityBusRoutes[BusRouteName].BusType,'End'))
                BusLeaveTimes.append((RouteStopTimes[0],RouteStopTimes[-1]))
                BusLeaveTimes.append((RouteStopTimes[-1], RouteStopTimes[0],))
                BusDriverSeconds = BusDriverSeconds + RouteStopTimes[-1] - RouteStopTimes[0]
        sys.stdout.write(".")
        sys.stdout.flush()
    
    BusLeaveTimes.sort()
    for CurTime in BusLeaveTimes:
        if CurTime[0] < CurTime[1]:
            if 0 < len(BusDriversAtDepot):
                BusDriversAtDepot.pop()
        else:
            BusDriversAtDepot.append(CurTime[0])
    BusDriversAtDepot = len(BusDriversAtDepot)
    BusDriverHours = int(BusDriversAtDepot + (int(BusDriverSeconds) + 3599) / 3600)
    BusDriverInfo = (BusDriversAtDepot, BusDriverHours, SimConfig.MinimumWage() * 1.5)
    for Location in StudentLocations:
        if(SimConfig.BusStation() != Location[0]):
            TraceInfo = ([(1, CityStreetMap.GenerateSpeedTrace( CityStreetMap.FindFastestPath(Location[0],SimConfig.BusStation()), 6.0, 5.0))], [] )
            NewStudentResults = SimulateVehicleOnTraces('Student' , AllVehicles, TraceInfo)
            AllStudentResults.append( NewStudentResults[0])       
        if(SimConfig.BusStation() != Location[1]):
            TraceInfo = ([(1, CityStreetMap.GenerateSpeedTrace( CityStreetMap.FindFastestPath(Location[1],SimConfig.BusStation()), 6.0, 5.0))], [] )
            NewStudentResults = SimulateVehicleOnTraces('Student' , AllVehicles, TraceInfo)
            AllStudentResults.append( NewStudentResults[0])
        sys.stdout.write(".")
        sys.stdout.flush()
    
    for Location in EmployeeLocations:
        if(SimConfig.BusStation() != Location[0]):
            TraceInfo = ([(1, CityStreetMap.GenerateSpeedTrace( CityStreetMap.FindFastestPath(Location[0],SimConfig.BusStation()), 4.0, 5.0))], [] )
            NewEmployeeResults = SimulateVehicleOnTraces('Employee' , AllVehicles, TraceInfo)
            AllEmployeeResults.append( NewEmployeeResults[0])       
        if(SimConfig.BusStation() != Location[1]):
            TraceInfo = ([(1, CityStreetMap.GenerateSpeedTrace( CityStreetMap.FindFastestPath(Location[1],SimConfig.BusStation()), 4.0, 5.0))], [] )
            NewEmployeeResults = SimulateVehicleOnTraces('Employee' , AllVehicles, TraceInfo)
            AllEmployeeResults.append( NewEmployeeResults[0])
        sys.stdout.write(".")
        sys.stdout.flush()
    
        
        
    sys.stdout.write(" Done\n")
    BusEvents.sort()
    TotalBusResults = []
    for Event in BusEvents:
        if 'End' == Event[3]:
            if Event[2] in BusDepot:
                BusDepot[Event[2]].append(Event[0])
            else:
                BusDepot[Event[2]] = [Event[0]]
        else:
            if not Event[2] in BusDepot:
                TotalBusResults.append(RouteResults[Event[1]][0])
            elif 0 == len(BusDepot[Event[2]]):
                TotalBusResults.append(RouteResults[Event[1]][0])
            else:
                if (Event[0] - BusDepot[Event[2]][-1]) > 1800.0:
                    TotalBusResults.append(RouteResults[Event[1]][0])
                else:
                    TotalBusResults.append(RouteResults[Event[1]][1])
                BusDepot[Event[2]].pop()
                
    Fees = (SimConfig.BusCost(), SimConfig.Parking(), SimConfig.BikePathCost())
    sys.stdout.write("Outputting Data Files      : ")
    OutputRoutesAsHTML("travel", CityStreetMap, CityBikePathMap, AllIncomingTravelPlans, AllOutgoingTravelPlans, DistanceTravelled, BusDepot, TotalBusResults, DriverCount, BikerCount, AllStudentResults, AllEmployeeResults, BusDriverInfo, Fees, AllVehicles, CityBusSchedule)
    sys.stdout.write(" Done\n")

if __name__ == '__main__':
    main()