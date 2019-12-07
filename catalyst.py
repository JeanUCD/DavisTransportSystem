#
#   TTP 210 Catalytic Converter 
#
import math
from ttputils import *
from materialproperties import *

class Catalyst:
    
    # Mass in kg, timeconstant in seconds, wall and channel thickness in m
    def __init__(self, mass, fueltype='gasoline', timeconst=2.0, wall=0.001, channel=0.001):
        self.AmbientTemperature = 25.0
        self.MatrixColumns = 100 
        self.MatrixRows = 100 
        self.MatrixWidth = (self.MatrixColumns + 1) * wall + self.MatrixColumns * channel
        self.MatrixHeight = (self.MatrixRows + 1) * wall + self.MatrixRows * channel
        MatrixAreaPerLength = self.MatrixWidth * self.MatrixHeight - self.MatrixColumns * self.MatrixRows * channel
        MatrixLength = (MaterialProperties.MaterialVolume('kanthal',mass) * 1e-6) / MatrixAreaPerLength
        self.MatrixSurfaceArea = self.MatrixColumns * self.MatrixRows * channel * MatrixLength
        self.ExternalSurfaceArea = MatrixLength * (self.MatrixWidth * 2.0 + self.MatrixHeight)
        self.Mass = mass                                                                                                                     
        self.MaxGrams = mass * 5 # 5g per kg
        self.MapTemperatures = (-200.0, 100.0, 150.0, 200.0, 250.0, 300.0, 350.0, 400.0, 450.0, 500.0, 550.0, 600.0)
        self.MapHCs =          (   0.0,   0.0,  0.08,  0.22,  0.40,  0.63,  0.80,  0.90,  0.93,  0.95,  0.96,  0.97)
        self.MapCOs =          (   0.0,  0.10,  0.22,  0.60,  0.80,  0.90,  0.91,  0.93,  0.94,  0.96,  0.97,  0.98)
        self.MapNOxs =         (   0.0,  0.10,  0.24,  0.62,  0.82,  0.92,  0.93,  0.95,  0.96,  0.98,  0.99,  0.995)
        self.MapPMs =          (   0.0,   0.0,  0.08,  0.22,  0.40,  0.63,  0.80,  0.90,  0.93,  0.95,  0.96,  0.97)        
        # Tempeartures in C and Capacities in kJ/kg K
        self.ExhaustTemperatures = (-13.15,  6.85, 26.85, 76.85, 126.85, 176.85, 226.85, 326.85, 526.85, 726.85, 926.85, 1126.85)
        self.ExhaustCapacities =   ( 6.727, 6.802, 6.871, 7.026,  7.161,  7.282,  7.389,  7.579,  7.888,  8.138,  8.349,   8.531)
        self.MatrixMaterialExhaust = MaterialProperties('kanthal',mass,self.AmbientTemperature,wall * 0.5)
        self.MatrixMaterialExternal = MaterialProperties('kanthal',mass,self.AmbientTemperature,(self.MatrixWidth + self.MatrixHeight) * 0.5)
        self.TimeConstant = timeconst
        self.Reset()
        
    def Reset(self):
        self.MatrixMaterialExhaust.Reset()
        self.MatrixMaterialExternal.Reset()
        self.HCAverage = 0.0
        self.COAverage = 0.0
        self.NOxAverage = 0.0
        self.PMAverage = 0.0
        self.HCCurrent = 0.0
        self.COCurrent = 0.0
        self.NOxCurrent = 0.0
        self.PMCurrent = 0.0
        self.HeatPower = 0.0
        self.ExhaustPower = 0.0
        self.CoolingPower = 0.0   
        
    # Inputs heat, fuel, and exhaust flow in. Returns HC, CO, NOx, and PM flow out.
    def CalculateOutputs(self, heatpower, fuel, hc, co, nox, pm):
        self.FuelCurrent = fuel
        self.HCCurrent = hc
        self.COCurrent = co
        self.NOxCurrent = nox
        self.PMCurrent = pm
        
        # Determine exhaust mass total
        TotalInputMass = self.HCAverage + self.COAverage + self.NOxAverage + self.PMAverage                               
        HCExcess = 0.0
        COExcess = 0.0
        NOxExcess = 0.0
        PMExcess = 0.0
        ProcessedRatio = 1.0
        # Clip based on max possible processing
        if(self.MaxGrams < TotalInputMass):
            ProcessedRatio = self.MaxGrams / TotalInputMass
            ExcessRatio = 1.0 - ProcessedRatio
            HCExcess = self.HCAverage * ExcessRatio
            COExcess = self.COAverage * ExcessRatio
            NOxExcess = self.NOxAverage * ExcessRatio
            PMExcess = self.PMAverage * ExcessRatio
        # Determine conversion ratios based on temperature
        HCRatio = Interpolate(self.MatrixMaterialExhaust.Temperature,self.MapTemperatures, self.MapHCs)
        CORatio = Interpolate(self.MatrixMaterialExhaust.Temperature,self.MapTemperatures, self.MapCOs)
        NOxRatio = Interpolate(self.MatrixMaterialExhaust.Temperature,self.MapTemperatures, self.MapNOxs)
        PMRatio = Interpolate(self.MatrixMaterialExhaust.Temperature,self.MapTemperatures, self.MapPMs)
        # Determine exhaust temperature
        ExhaustTemperature = self.CalculateExhaustTemperature(heatpower, fuel) 
        self.HeatPower = heatpower
        # Calculate heat flows
        self.ExhaustPower = self.MatrixMaterialExhaust.HeatFlow(self.MatrixSurfaceArea, ExhaustTemperature)
        self.CoolingPower = self.MatrixMaterialExternal.HeatFlow(self.ExternalSurfaceArea, self.AmbientTemperature)
        # Return exhaust flows
        return (HCExcess + self.HCAverage * (1.0 - HCRatio), COExcess + self.COAverage * (1.0 - CORatio), NOxExcess + self.NOxAverage * (1.0 - NOxRatio), PMExcess + self.PMAverage * (1.0 - PMRatio), self.CoolingPower)
    
    # Calculate exhaust temperature from fuel rate and power
    def CalculateExhaustTemperature(self, heatpower, exhaustrate):
        # Rough calculation of grams to mols for ideal gas
        return ConvertKToC( ((heatpower / 2.0)/(exhaustrate * 0.6)) / 8.3145 )
        
    # Update the heat transfer
    def UpdateTemperatures(self,time):
        # If the heat flow would be faster than that of exhaust, clip it
        if self.ExhaustPower > self.HeatPower:
            # Need to integrate subtime
            self.ExhaustPower = self.HeatPower
            
        # Update the amount in catalyst using a low pass filter
        if(time < self.TimeConstant):
            Ratio = time / self.TimeConstant
            self.HCAverage = (1.0 - Ratio) * self.HCAverage + Ratio * self.HCCurrent 
            self.COAverage = (1.0 - Ratio) * self.COAverage + Ratio * self.COCurrent 
            self.NOxAverage = (1.0 - Ratio) * self.NOxAverage + Ratio * self.NOxCurrent 
            self.PMAverage = (1.0 - Ratio) * self.PMAverage + Ratio * self.PMCurrent 
        else:
            self.HCAverage = self.HCCurrent 
            self.COAverage = self.COCurrent 
            self.NOxAverage = self.NOxCurrent 
            self.PMAverage = self.PMCurrent 
            
        self.MatrixMaterialExhaust.UpdateTemperature((self.ExhaustPower - self.CoolingPower) * time)
        self.MatrixMaterialExternal.UpdateTemperature((self.ExhaustPower - self.CoolingPower) * time) 
    
    def GetTemperature(self):
        return self.MatrixMaterialExhaust.Temperature


