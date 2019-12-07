#
# TTP 210 
#
import csv
from ttputils import *

class VehicleParameters:
    def __init__(self, filename):
        self.Load(filename)

    def Load(self, filename):
        self.VehicleData = {}
        with open(filename, 'rU') as ParameterFile:
            ParameterFileReader = csv.reader(ParameterFile, delimiter=',')
            Header = next(ParameterFileReader)
            for Row in ParameterFileReader:
                NewVehicle = {}
                for Index in range(1,len(Row)):
                    if 0 != len(Row[Index]):
                        NewVehicle[Header[Index]] = Row[Index]
                self.VehicleData[ Row[0] ] = NewVehicle
                

    def GetParameter(self, vehicle, param):
        if vehicle in self.VehicleData:
            if param in self.VehicleData[vehicle]:
                return self.VehicleData[vehicle][param]
        return None

    def GetVehicleNames(self):
        ReturnNames = []
        for Vehicle in self.VehicleData:
            ReturnNames.append(Vehicle)
        return ReturnNames
