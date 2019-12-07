#
#   TTP 210 Battery Model
#
from ttputils import *
        
class Battery:
    def __init__(self,maxpower,maxenergy,initialenergy):
        MinPowerDensity = 175.0             # W/kg
        MaxPowerDensity = 238.0             # W/kg
        MinEnergyDensity = 70.0             # Wh/kg
        MaxEnergyDensity = 185.5            # Wh/kg
        
        self.EnergyCapacity = maxenergy     # Wh Total capacity
        self.CurrentEnergy = initialenergy  # Wh Initial capacity
        self.PeakPower = maxpower           # W for 20% SOC
        self.MapSOC = (0.00,  0.05,  0.10,  0.20,  0.50,  0.90,  0.94,  0.96,  1.00)
        self.MapVOC = (0.00, 300.0, 330.0, 340.0, 345.0, 360.0, 380.0, 400.0, 400.0)
        IntRRatio = (1.234567901, 1.234567901, 1.114197531, 1, 0.918402778, 1, 1.114197531, 1.234567901, 1.234567901)
        Rfor20SOC = Interpolate(0.2, self.MapSOC, self.MapVOC)**2 /(4 * self.PeakPower)
        self.MapIntR = tuple([x*Rfor20SOC for x in IntRRatio])
        # Figure out chemistry blend Power density vs Energy density for Li-ion
        DeltaPowerDensity = MaxPowerDensity - MinPowerDensity
        DeltaEnergyDensity = MaxEnergyDensity - MinEnergyDensity
        ChemistryBlend = (self.EnergyCapacity * MaxPowerDensity - self.PeakPower * MinEnergyDensity) / (self.PeakPower * DeltaEnergyDensity + self.EnergyCapacity * DeltaPowerDensity)
        if(ChemistryBlend < 0.0):
            # Blend for power
            self.Mass = self.PeakPower / MaxPowerDensity
        elif(ChemistryBlend > 1.0):
            # Blend for energy
            self.Mass = self.EnergyCapacity / MaxEnergyDensity
        else:
            # Mixed blend
            self.Mass = self.EnergyCapacity / (ChemistryBlend * DeltaEnergyDensity + MinEnergyDensity)
        
    def Reset(self, initialenergy):
        self.CurrentEnergy = initialenergy
        
    def UpdatePackLoad(self, power, time):
        CurrentSOC = self.SOC()
        VOC = Interpolate(CurrentSOC, self.MapSOC, self.MapVOC)
        IntR = Interpolate(CurrentSOC, self.MapSOC, self.MapIntR)
        Currents = QuadraticEquation(IntR, -VOC, power)
        Current = 0.0
        if(0 == len(Currents)):
            print("ERROR: Battery pack unable to supply power!")
            self.CurrentEnergy -= PowerTimeToWh(power, time)
        else:
            Current = min(Currents)
            self.CurrentEnergy -= PowerTimeToWh(Current * VOC, time)
        if(0.0 > self.CurrentEnergy):
            self.CurrentEnergy = 0.0
        if(self.EnergyCapacity < self.CurrentEnergy):
            self.CurrentEnergy = self.EnergyCapacity
        V = VOC - IntR * Current
        return (self.CurrentEnergy / self.EnergyCapacity, V, Current)
        
    def SOC(self):
        return self.CurrentEnergy / self.EnergyCapacity
        
    def OpenCircuitVoltage(self):
        return Interpolate(self.SOC(), self.MapSOC, self.MapVOC)

