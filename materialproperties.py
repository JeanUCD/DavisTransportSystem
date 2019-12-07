#
#   TTP 210 Material Property Functions
#
import math
from ttputils import *

class MaterialProperties:
    # Tempeartures in C and Capacities in kJ/kg K
    MaterialHeatCapacityTemperatures = {'kanthal':(20.0, 200.0, 400.0, 600.0, 800.0, 1000.0, 1200.0, 1400.0),
                                        'aluminum':(0.0, 20.0, 100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0),
                                        'iron':(0.0, 20.0, 100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0,750.0),
                                        'steel':(0.0, 20.0, 100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0),
                                        'glycol':(0.0,100.0)} 
    MaterialHeatCapacities =    {'kanthal':(0.46,  0.56,  0.63,  0.75,  0.71,   0.72,  0.74,    0.80),
                                 'aluminum':(0.881310422, 0.891303548, 0.931276054, 0.981241686, 1.031207318, 1.08117295, 1.131138582, 1.181104214, 1.231069846),
                                 'iron':(0.436603995, 0.446065436, 0.483911199, 0.531218403, 0.578525606, 0.62583281, 0.673140014, 0.720447218, 0.767754422, 0.791408024),
                                 'steel':(0.425, 0.43980176, 0.48762, 0.52976, 0.56474, 0.60588, 0.6665, 0.75992, 1.008157895, 0.80326087),
                                 'glycol':(2.38,2.38)}

    # Tempeartures in C and Conductivites in W/m K
    MaterialHeatConductivityTemperatures = {'kanthal':(50.0, 600.0, 800.0, 1000.0, 1200.0, 1400.0),
                                            'aluminum':(0, 26.85, 76.85, 126.85, 226.85, 326.85, 426.85),
                                            'iron':(0.0, 26.85, 76.85, 126.85, 226.85, 326.85, 426.85, 526.85, 626.85, 726.85, 826.85),
                                            'steel':(0.0, 20.0, 100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0),
                                            'glycol':(0.0,100.0)} 
    MaterialHeatConductivities = {'kanthal':(11.0, 20.0, 22.0, 26.0, 27.0, 35.0),
                                  'aluminum':(236.0, 237.0, 240.0, 240.0, 237.0, 232.0, 226.0),
                                  'iron':(83.5, 80.3, 74.4, 69.4, 61.3, 54.7, 48.7, 43.3, 38, 32.6, 29.7),
                                  'steel':(54.0, 53.334, 50.67, 47.34, 44.01, 40.68, 37.35, 34.02, 30.69, 27.36),
                                  'glycol':(0.25,0.25)}

    # g/cm^3
    MaterialDensities = {'kanthal':7.10, 'aluminum':2.7, 'iron':7.874, 'steel':8.05, 'glycol':1.11}
    
    @staticmethod
    def MaterialVolume(material, mass):
        return (mass * 1000.0) / MaterialProperties.MaterialDensities[ material ] 
    
    # material - name, mass in kg, temperature in C
    def __init__(self,material,mass,inittemp,thickness=-1):
        self.HeatCapacityTemperatures = MaterialProperties.MaterialHeatCapacityTemperatures[material]
        self.HeatCapacities = MaterialProperties.MaterialHeatCapacities[material]
        self.HeatConductivityTemperatures = MaterialProperties.MaterialHeatConductivityTemperatures[material]
        self.HeatConductivities = MaterialProperties.MaterialHeatConductivities[material]
        self.Density = MaterialProperties.MaterialDensities[material]
        self.Mass = mass
        self.InitialTemperature = inittemp
        self.Temperature = inittemp
        if(0.0 < thickness):
            self.Thickness = thickness
        else:
            # Volume in cm^3
            Volume = (mass * 1000.0) / self.Density
            # Thickness in meters
            self.Thickness = ConvertVolumeToRadius(Volume) / 100.0
            
    def Reset(self):
        self.Temperature = self.InitialTemperature
        
    # Determine instantaneous heat flow out W, area in m^2, othertemp in C
    def HeatFlow(self,area,othertemp):
        HeatConductance = Interpolate(self.Temperature,self.HeatConductivityTemperatures, self.HeatConductivities) / self.Thickness
        return (self.Temperature - othertemp) * HeatConductance * area
        
    # Update temperature by adding heat in J
    def UpdateTemperature(self,heat):
        CurrentHeatCapacity = Interpolate(self.Temperature,self.HeatCapacityTemperatures, self.HeatCapacities)
        CurrentEnergykJ = self.Mass * ConvertCToK(self.Temperature) * CurrentHeatCapacity
        CurrentEnergykJ += heat / 1000.0
        self.Temperature = ConvertKToC(CurrentEnergykJ / (self.Mass * CurrentHeatCapacity))
        
        

