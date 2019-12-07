#
#   TTP 210 Transmission Model
#
from ttputils import *

#
#22.6796 kg 
#0.000164235 kg/W peak power
#0.167276145 kg/N-m peak torque
#0.453592 kg/gear
# Multiplier 1 auto, 0.9 manual, 
            
class Transmission:
    def __init__(self,eff,ratios):
        self.Efficiency = eff
        if(2 == len(ratios)):
            if((0.0 > ratios[0]) and (0.0 > ratios[1])):
                self.Ratios = (-ratios[0],-ratios[1])
                self.IsCVT = True
            else:
                self.Ratios = ratios
                self.IsCVT = False
        else:
            self.Ratios = ratios
            self.IsCVT = False
            
    # Helper Functions
    def Reset(self):
        self.LossEnergy = 0.0
    
    def MinimumGear(self):
        if(self.IsCVT):
            return 0
        else:
            return 1

    def MaximumGear(self):
        if(self.IsCVT):
            return 1
        else:
            return len(self.Ratios) - 1
    
    def FindClosestGear(self, inrpm, outrpm):
        if(self.IsCVT):
            if(0.0 < outrpm):
                Ratio = inrpm / outrpm
                if(self.Ratios[1] > Ratio):
                    return 1
                elif(self.Ratios[0] < Ratio):
                    return 0
                else:
                    return (Ratio - self.Ratios[0])/(self.Ratios[1] - self.Ratios[0])
            else:
                return 0
                    
        else:
            BestGear = 1
            BestError = abs(inrpm - self.Ratios[1] * outrpm)
            for Index in range(1, len(self.Ratios)):
                Error = abs(inrpm - self.Ratios[Index] * outrpm)
                if(BestError > Error):
                    BestError = Error
                    BestGear = Index
            return BestGear

    # Returns tuple with Power, RPM, Torque
    def CalculateInputs(self,outpower,outrpm,gear):
        if(0.0 <= outpower):
            InputPower = outpower / self.Efficiency
        else:
            InputPower = outpower * self.Efficiency
        if(self.IsCVT):
            InputRPM = outrpm * (self.Ratios[0] + (self.Ratios[1] - self.Ratios[0])*gear)
        else:
            InputRPM = outrpm * self.Ratios[gear]
        if(0.0 < InputRPM):
            InputTorque = RotationalTorque(InputPower, InputRPM)
        else:
            InputTorque = 0.0
        return (InputPower, InputRPM, InputTorque)
        
    # Updates the loss energy
    def UpdateLoad(self,outpower,gear,time):
        if(0.0 <= outpower):
            self.LossEnergy += ((outpower / self.Efficiency) - outpower) * time
        else:
            # Using eff -1 instead of 1 - eff because output is negative
            self.LossEnergy += ((self.Efficiency - 1.0) * outpower) * time
