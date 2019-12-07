#
#   TTP 210 Engine Efficiency Map
#
import csv
import math
from ttputils import *
from efficiencymap import *
from materialproperties import *
from catalyst import *

class EngineEfficiencyMap(EfficiencyMap):
    def __init__(self, filename):
        self.Parameters = {}
        self.Parameters[ "nox" ] = str(1.1)
        self.Parameters[ "co" ] = str(11.0)
        self.Parameters[ "hc" ] = str(1.1)
        self.Parameters[ "pm" ] = str(0.0)
        self.Parameters[ "exheat" ] = str(0.5)
        self.Parameters[ "lhv" ] = str(44427.0)
        self.Parameters[ "cylinders" ] = str(4)
        self.Parameters[ "displacement" ] = str(1.9)
        self.Parameters[ "bore" ] = str(88.0)
        self.Parameters[ "cylinderdrag" ] = str(1)
        self.Parameters[ "vvtrpm" ] = str(0)
        self.Parameters[ "blockmaterial" ] = "steel"
        self.Parameters[ "fueltype" ] = "gasoline"
        EfficiencyMap.__init__(self,filename,True,False,False)

        # Mass is roughly 70kg + 1kg for every 3kW of power
        self.Mass = ConvertWTokW(self.PeakPower) * 0.33333333 + 70.0
        self.NOxRatio = float(self.Parameters[ "nox" ])
        self.CORatio = float(self.Parameters[ "co" ])
        self.HCRatio = float(self.Parameters[ "hc" ])
        self.PMRatio = float(self.Parameters[ "pm" ])
        self.ExhaustHeatRatio = float(self.Parameters[ "exheat" ])
        self.LHVJperg = float(self.Parameters[ "lhv" ])
        self.Cylinders = float(self.Parameters[ "cylinders" ])
        self.Displacement = float(self.Parameters[ "displacement" ])
        self.Bore = float(self.Parameters[ "bore" ])
        self.CylinderDrag = float(self.Parameters[ "cylinderdrag" ])
        self.VVTRPM = float(self.Parameters[ "vvtrpm" ])
        self.BlockMaterial = self.Parameters[ "blockmaterial" ]
        self.FuelType = self.Parameters[ "fueltype" ]
        self.HeatingPower = 0.0
        self.MinConsumption = 10000000000.0
        self.MaxConsumption = -1.0
        self.MinPower = self.MaxPower = RotationalPower(self.MapRPMs[0], self.MapTorques[0])
        for RPMIndex in range(0,len(self.MaxPowerRPMs)):
            self.MaxPower = max(self.MaxPower, RotationalPower(self.MaxPowerRPMs[RPMIndex], self.MaxPowerTorques[RPMIndex]) )
        for RPMIndex in range(0,len(self.MapRPMs)):
            for TorqueIndex in range(0, len(self.MapTorques)):
                if(0 < self.MapEfficiencies[RPMIndex][TorqueIndex]):
                    ConsumptionRate = self.MapEfficiencies[RPMIndex][TorqueIndex] * ConvertJTokWh( RotationalPower(self.MapRPMs[RPMIndex], self.MapTorques[TorqueIndex]))
                    self.MinConsumption = min(self.MinConsumption, ConsumptionRate)
                    self.MaxConsumption = max(self.MaxConsumption, ConsumptionRate)
        VolumePerCylinder = self.Displacement / self.Cylinders
        TopCylinderArea = (math.pi * (self.Bore / 20.0)**2)
        CylinderHeight = ConvertLTocm3(VolumePerCylinder) / TopCylinderArea
        CylinderSurfaceArea = (CylinderHeight * (self.Bore /10.0) * math.pi) + 2.0 * TopCylinderArea
        CylinderWallVolume = MaterialProperties.MaterialVolume(self.BlockMaterial, self.Mass * 0.1 / self.Cylinders)
        TotalTopCylinderArea = (CylinderWallVolume + ConvertLTocm3(VolumePerCylinder)) / CylinderHeight
        OuterCylinderRadius = (TotalTopCylinderArea / math.pi)**0.5
        self.CylinderWallThickness = ((OuterCylinderRadius - (self.Bore / 20.0)) * 0.5) * 0.01
        self.CylinderSurfaceArea = ((CylinderHeight * (OuterCylinderRadius * 2.0) * math.pi) + 2.0 * TotalTopCylinderArea) * self.Cylinders * 4.0 * 1e-6 
        self.CylinderMaterial = MaterialProperties(self.BlockMaterial, self.Mass * 0.1, 25.0, self.CylinderWallThickness)
        self.CoolantMaterial = MaterialProperties('glycol',  (MaterialProperties.MaterialDensities['glycol'] * ConvertLTocm3(VolumePerCylinder) * 4.0) / 1000.0, 25.0, 0.001)
        # Size radiator to 3.5m^2 per L of displacement
        self.RadiatorSurfaceArea = 3.5 * self.Displacement
        self.ThreeWayCat = Catalyst(self.PeakPower / 19000.0, self.FuelType, 4.5)

    def Reset(self):
        self.CylinderMaterial.Reset()
        self.CoolantMaterial.Reset()
        self.ThreeWayCat.Reset()
        
    # Calculate fuel consumption (g/s), HC (g/s), CO (g/s), NOx (g/s), PM (g/s), exhaust power (W)
    def CalculateEfficiencyAndEmissions(self,rpm,torque):
        # Calculate power at motor/engine output
        PowerPoint = RotationalPower(rpm,torque)
        # Calculate the consumption rate of the engine
        ConsumptionRategkWh = self.CalculateEfficiency(rpm, torque)
        # Convert power out W to kW (divide 1000.0) and convert g/h to g/s (divide 3600.0)
        ConsumptionRategs = ConsumptionRategkWh * ConvertJTokWh(PowerPoint)
        # Convert fuel rate into power using fuel LHV
        PowerIn = ConsumptionRategs * self.LHVJperg
        # Implement ratio for NOx based on peak at low consumption
        NOxLookup = 1.0 - (ConsumptionRategs - self.MinConsumption)/(self.MaxConsumption - self.MinConsumption)
        NOxLookup = NOxLookup**16.0
        if 100.0 > self.CylinderMaterial.Temperature:
            NOxLookup = NOxLookup * (self.CylinderMaterial.Temperature / 100.0)
        # Implement ratio for CO based on peak power is peak CO
        COLookup = PowerPoint / self.PeakPower
        # Implement ratio for HC based on dramatic increase above IOL
        MaxTorque = self.CalculateMaxTorque(rpm)
        IdealTorque = self.CalculateIdealTorque(rpm)
        if(torque < IdealTorque):
            HCLookup = torque / IdealTorque * 0.08
        else:
            HCLookup = (((torque - IdealTorque)/(MaxTorque - IdealTorque))**3) * 0.92 + 0.08
        # Implement ratio for PM based on dramatic increase under high torque/high speed
        if(torque < self.PeakTorque * 0.3):
            PMLookup = (torque / self.PeakTorque) * 0.01
        else:
            PMLookup = ((torque - self.PeakTorque * 0.3)/(self.PeakTorque * 0.7)) * 0.99 + 0.01
        MiddleRPM = (self.MapRPMs[0] + self.MapRPMs[-1]) * 0.5
        if(rpm  < MiddleRPM):
            PMLookup *= ((MiddleRPM - rpm) / (MiddleRPM - self.MapRPMs[0])) * 0.01
        else:
            PMLookup *= ((rpm - MiddleRPM)/(self.MapRPMs[-1] - MiddleRPM)) * 0.99 + 0.01
        
        # Multiply emissions ratios calculated by scaling factors (self.XRatio) by fuel consumption rate
        HCRate = HCLookup * self.HCRatio * ConsumptionRategs
        CORate = COLookup * self.CORatio * ConsumptionRategs
        NOxRate = NOxLookup * self.NOxRatio * ConsumptionRategs
        PMRate = PMLookup * self.PMRatio * ConsumptionRategs

        # Roughly 30% efficient, 10% loss in friction, 30% heat into exhaust and 30% heat of block
        WasteHeat = (PowerIn - PowerPoint) * 6.0 / 7.0 
        self.ExhaustHeatRatio = (rpm - self.MapRPMs[0])/(self.MapRPMs[-1] - self.MapRPMs[0]) * 0.25 + 0.25
        self.HeatingPower = WasteHeat * (1.0 - self.ExhaustHeatRatio)
        # Calculate output of the catalyst given input heat, and emissions
        CatOut = self.ThreeWayCat.CalculateOutputs(WasteHeat * self.ExhaustHeatRatio, ConsumptionRategs, HCRate, CORate, NOxRate, PMRate)
        return (ConsumptionRategs, HCRate, CORate, NOxRate, PMRate, WasteHeat * self.ExhaustHeatRatio, CatOut[0], CatOut[1], CatOut[2], CatOut[3])

    # Update the engine and catalyst temperatures
    def UpdateTemperatures(self,time):
        HeatFlowToGlycol = self.CylinderMaterial.HeatFlow(self.CylinderSurfaceArea, self.CoolantMaterial.Temperature)
        # Most thermostats open up at 80C and are wide open at 100C
        if(80.0 > self.CoolantMaterial.Temperature):
            ThermostatRatio = 0.0
        elif(100.0 > self.CoolantMaterial.Temperature):
            ThermostatRatio = ((self.CoolantMaterial.Temperature - 80.0) / 20.0) 
        else:
            ThermostatRatio = 1.0
        HeatFlowToAir = self.CoolantMaterial.HeatFlow(self.RadiatorSurfaceArea * ThermostatRatio, 25.0)
        # Transfer heat to the cylinder walls and from cylinder walls into coolant
        self.CylinderMaterial.UpdateTemperature((self.HeatingPower - HeatFlowToGlycol) * time)
        # Set ambient heat around catalyst to that of coolant temp (just simplification)
        self.ThreeWayCat.AmbientTemperature = self.CoolantMaterial.Temperature
        # Transfer heat from cylinder walls into coolant and from coolant to air
        self.CoolantMaterial.UpdateTemperature((HeatFlowToGlycol - HeatFlowToAir) * time)
        # Transfer heat into/out of catalyst
        self.ThreeWayCat.UpdateTemperatures(time)
    
    # Get the engine, coolant, and catalyst temperatures
    def GetTemperatures(self):
        return (self.CylinderMaterial.Temperature, self.CoolantMaterial.Temperature, self.ThreeWayCat.GetTemperature())
        
