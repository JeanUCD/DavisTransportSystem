#
# TTP 210 
#
import csv
from ttputils import *

class SimulationConfiguration:
    def __init__(self, filename=''):
        self.ConfigDB = {}
        
        self.ConfigDB['Bus Station'] = 'P9'
        self.ConfigDB['Max Bus Per Loop'] = '2'
        self.ConfigDB['Student Count'] = '30000'
        self.ConfigDB['Student Hours'] = '3'
        self.ConfigDB['Student Ratio'] = '10'
        self.ConfigDB['Employee Count'] = '30000'
        self.ConfigDB['Employee Ratio'] = '100'
        self.ConfigDB['Outer Perimeter'] = '0.1'
        self.ConfigDB['Bus Cost'] = '0.0'
        self.ConfigDB['Parking'] = '0.0'
        self.ConfigDB['Mileage'] = '0.56'
        self.ConfigDB['Minimum Wage'] = '8.0'
        self.ConfigDB['Employee Wage'] = '30.0'
        self.ConfigDB['Bike Path Cost'] = '10000.0'
        if(len(filename)):
            self.Load(filename)
        
    def Load(self, filename):
        self.ConfigDB = {}
        with open(filename, 'rU') as ConfigFile:
            ConfigFileReader = csv.reader(ConfigFile, delimiter=',')
            for Row in ConfigFileReader:
                self.ConfigDB[Row[0]] = Row[1]
                
    def Save(self, filename):
        OutputFile = open(filename, 'w', newline='')
        ConfigFileWriter = csv.writer(OutputFile, quoting=csv.QUOTE_ALL)
        for Item in self.ConfigDB:
            TempList = [Item, self.ConfigDB[Item]]
            ConfigFileWriter.writerow(TempList)       

    def BusStation(self):
        return self.ConfigDB['Bus Station']

    def MaxBusPerLoop(self):
        return int(self.ConfigDB['Max Bus Per Loop'])
        
    def StudentCount(self):
        return int(self.ConfigDB['Student Count'])
            
    def StudentHours(self):
        return int(self.ConfigDB['Student Hours'])
        
    def StudentRatio(self):
        return float(self.ConfigDB['Student Ratio'])
        
    def EmployeeCount(self):
        return int(self.ConfigDB['Employee Count'])
        
    def EmployeeRatio(self):
        return float(self.ConfigDB['Employee Ratio'])
        
    def OuterPerimeter(self):
        return float(self.ConfigDB['Outer Perimeter'])

    def BusCost(self):
        return float(self.ConfigDB['Bus Cost'])
        
    def Parking(self):
        return float(self.ConfigDB['Parking'])
        
    def Mileage(self):
        return float(self.ConfigDB['Mileage'])
        
    def MinimumWage(self):
        return float(self.ConfigDB['Minimum Wage'])
        
    def EmployeeWage(self):
        return float(self.ConfigDB['Employee Wage'])

    def BikePathCost(self):
        return float(self.ConfigDB['Bike Path Cost'])