#
#   TTP 210 Efficiency Map
#
import csv
from ttputils import *


class EfficiencyMap:
    def __init__(self, filename, normalized=False, peakpower=True, negativepower=True):
        self.NormalizedConsumption = normalized
        self.PeakPowerListed = peakpower
        self.NegativeTorqueAllowed = negativepower
        if not hasattr(self, 'Parameters'):
            self.Parameters = {}
        self.MaxPowerRPMs = []
        self.MaxPowerTorques = []
        self.MaxPowerEfficiency = []
        self.MapTorques = []
        self.MapRPMs = []
        self.MapEfficiencies = []
        self.MapCubicEfficiencies = []
        self.MapCubicEfficienciesTranspose = []
        self.IdealTorques = []
        self.IdealCubicTorques = []
        self.IdealCubicTorqueRPMs = []
        self.PeakPower = 0.0   
        self.Mass = 0.0
        self.StabilizationSamples = 1
        self.CalculateLinear = False
        self.Load(filename)
        
    def Reset(self):
        pass
        
    def ScaleMap(self, scaling):
        for Index in range(0,len(self.MaxPowerTorques)):
            self.MaxPowerTorques[Index] = self.MaxPowerTorques[Index] * scaling
            if not self.NormalizedConsumption:
                self.MaxPowerEfficiency[Index] = self.MaxPowerEfficiency[Index] * scaling
        for TorqueIndex in range(0,len(self.MapTorques)):
            self.MapTorques[TorqueIndex] = self.MapTorques[TorqueIndex] * scaling
            if not self.NormalizedConsumption:
                for RPMIndex in range(0,len(self.MapRPMs)):
                    if(0.0 <= self.MapEfficiencies[RPMIndex][TorqueIndex]):
                        self.MapEfficiencies[RPMIndex][TorqueIndex] = self.MapEfficiencies[RPMIndex][TorqueIndex] * scaling
                
    def Load(self, filename):
        LoadingData = False
        #print ("Opening engine data \"%s\"" %filename)

        # Open the engine data file
        with open(filename, 'rU') as DataFile:
            DataReader = csv.reader(DataFile, delimiter=',')
            # For each row in the CSV File
            for Row in DataReader:
                # If the row is not empty
                if(len(Row)):
                    # If the first element is not empty
                    if(len(Row[0])):
                        # If the row is a comment
                        if('#' != Row[0][0]):
                            # Load additional parameters
                            if(not IsFloat(Row[0])):
                                # Place parameter in dictionary 
                                self.Parameters[ Row[0].lower() ] = Row[1]
                            elif(LoadingData):
                                CurrentRPM = float(Row[0])
                                CurrentConsumption = float(Row[1])
                                self.MapRPMs.append(CurrentRPM)
                                TempEfficiencyMapRow = []
                                MinEfficiency = CurrentConsumption
                                MaxEfficiency = RotationalPower(CurrentRPM, self.MapTorques[0]) / CurrentConsumption
                                MinEfficiencyTorque = self.MapTorques[0]
                                MaxEfficiencyTorque = self.MapTorques[0]
                                CurrentIndex = 0
                                for Element in Row[1:]:
                                    CurrentConsumption = float(Element)
                                    TempEfficiencyMapRow.append(CurrentConsumption)
                                    if((MinEfficiency > CurrentConsumption)and(0.0 <= CurrentConsumption)):
                                        MinEfficiency = CurrentConsumption
                                        MinEfficiencyTorque = self.MapTorques[CurrentIndex]
                                    if(MaxEfficiency < (RotationalPower(CurrentRPM, self.MapTorques[CurrentIndex]) / CurrentConsumption)):
                                        MaxEfficiency = RotationalPower(CurrentRPM, self.MapTorques[CurrentIndex]) / CurrentConsumption
                                        MaxEfficiencyTorque = self.MapTorques[CurrentIndex]
                                    CurrentIndex += 1                                        
                                self.MapEfficiencies.append(TempEfficiencyMapRow)
                                if(self.NormalizedConsumption):
                                    self.IdealTorques.append(MinEfficiencyTorque)
                                else:
                                    self.IdealTorques.append(MaxEfficiencyTorque)
                            else:              
                                self.MaxPowerRPMs.append(float(Row[0]))
                                self.MaxPowerTorques.append(float(Row[1]))
                                self.MaxPowerEfficiency.append(float(Row[2]))
                                    
                    else:
                        # Found header for consumption map
                        for Element in Row[1:]:
                            self.MapTorques.append(float(Element))
                        LoadingData = True
        # Find Peak power 
        for Index in range(0,len(self.MaxPowerRPMs)):   
            # For each calculate the power at the max torque point
            PowerPoint = RotationalPower(self.MaxPowerRPMs[Index],self.MaxPowerTorques[Index])
            # If the peak power isn't just in the map, find max of torque * rpm
            if((0 < Index)and(not self.PeakPowerListed)):
                # If the power is increasing
                if(PowerPoint < RotationalPower(self.MaxPowerRPMs[Index-1],self.MaxPowerTorques[Index-1])):
                    # Find the line Y = MX + B parameters
                    LineData = LineCalculateMB(self.MaxPowerRPMs[Index-1],self.MaxPowerTorques[Index-1],self.MaxPowerRPMs[Index],self.MaxPowerTorques[Index])
                    if(0 != LineData[0]):
                        RPMPoint = LineData[1] / (LineData[0] * 2.0)
                        RPMRatio = (RPMPoint - self.MaxPowerRPMs[Index-1]) / (self.MaxPowerRPMs[Index] - self.MaxPowerRPMs[Index-1])
                        TorquePoint = RPMRatio * (self.MaxPowerTorques[Index] - self.MaxPowerTorques[Index-1]) + self.MaxPowerTorques[Index-1]
                        NewPowerPoint = RotationalPower(RPMPoint, TorquePoint)
                        PowerPoint = max(PowerPoint, NewPowerPoint)
            self.PeakPower = max(self.PeakPower, PowerPoint)
        self.PeakTorque = max(self.MaxPowerTorques)
        # Extrapolate the map one additional point in each direction for cubic calculations
        ExtrapolatedMap = []
        for RPMIndex in range(0,len(self.MapRPMs)): 
            ExtrapolatedRPMMap = []
            TopValidTorque = 0
            for TorqueIndex in range(0, len(self.MapTorques)): 
                if self.MapTorques[TorqueIndex] < self.MaxPowerTorques[RPMIndex]:
                    ExtrapolatedRPMMap.append(self.MapEfficiencies[RPMIndex][TorqueIndex])
                    TopValidTorque = TorqueIndex
                else:
                    TorqueDenom = self.MaxPowerTorques[RPMIndex] - self.MapTorques[TopValidTorque]
                    TorqueNumerator = self.MapTorques[TorqueIndex] - self.MapTorques[TopValidTorque]
                    ExtrapolatedRPMMap.append(self.MapEfficiencies[RPMIndex][TopValidTorque] + (self.MaxPowerEfficiency[RPMIndex] - self.MapEfficiencies[RPMIndex][TopValidTorque]) * TorqueNumerator / TorqueDenom)
                    
            ExtrapolatedRPMMap.append(ExtrapolatedRPMMap[-1]*2 - ExtrapolatedRPMMap[-2])
            ExtrapolatedRPMMap.append(ExtrapolatedRPMMap[-1]*2 - ExtrapolatedRPMMap[-2])
            ExtrapolatedRPMMap.insert(0, ExtrapolatedRPMMap[0]*2 - ExtrapolatedRPMMap[1])
            ExtrapolatedMap.append(ExtrapolatedRPMMap)
        
        ExtrapolatedRPMMapPre = []
        ExtrapolatedRPMMapPost = []
        for TorqueIndex in range(0,len(ExtrapolatedMap[0])): 
            ExtrapolatedRPMMapPre.append(ExtrapolatedMap[0][TorqueIndex]*2 - ExtrapolatedMap[1][TorqueIndex])
            ExtrapolatedRPMMapPost.append(ExtrapolatedMap[-1][TorqueIndex]*2 - ExtrapolatedMap[-2][TorqueIndex])
        ExtrapolatedMap.insert(0,ExtrapolatedRPMMapPre)
        ExtrapolatedMap.append(ExtrapolatedRPMMapPost)
        ExtrapolatedRPMMapPost = []
        for TorqueIndex in range(0,len(ExtrapolatedMap[0])): 
            ExtrapolatedRPMMapPost.append(ExtrapolatedMap[-1][TorqueIndex]*2 - ExtrapolatedMap[-2][TorqueIndex])
        ExtrapolatedMap.append(ExtrapolatedRPMMapPost)
        # Create the bicubic values for each RPM/Torque point
        for RPMIndex in range(0,len(self.MapRPMs)): 
            PrevDeltaTorque = DeltaTorque = self.MapTorques[1] - self.MapTorques[0]
            self.MapCubicEfficiencies.append([])
            self.MapCubicEfficienciesTranspose.append([])
            for TorqueIndex in range(0, len(self.MapTorques)):
                if TorqueIndex + 2 < len(self.MapTorques):
                    NextDeltaTorque = self.MapTorques[TorqueIndex+2] - self.MapTorques[TorqueIndex+1]
                else:
                    NextDeltaTorque = DeltaTorque
                CubicParameters = []
                for Index in range(0, 4):
                    V0 = ExtrapolatedMap[RPMIndex+Index][TorqueIndex+1] + (ExtrapolatedMap[RPMIndex+Index][TorqueIndex] - ExtrapolatedMap[RPMIndex+Index][TorqueIndex+1]) * DeltaTorque / PrevDeltaTorque
                    V1 = ExtrapolatedMap[RPMIndex+Index][TorqueIndex+1]
                    V2 = ExtrapolatedMap[RPMIndex+Index][TorqueIndex+2]
                    V3 = ExtrapolatedMap[RPMIndex+Index][TorqueIndex+2] + (ExtrapolatedMap[RPMIndex+Index][TorqueIndex+3] - ExtrapolatedMap[RPMIndex+Index][TorqueIndex+2]) * DeltaTorque / NextDeltaTorque
                    CubicParameters.append([V0, V1, V2, V3])
                self.MapCubicEfficiencies[-1].append(CubicParameters)
                # Transpose the efficiencies
                self.MapCubicEfficienciesTranspose[-1].append( list(map(list, zip(*CubicParameters))) )
                PrevDeltaTorque = DeltaTorque
                DeltaTorque = NextDeltaTorque
        
        # Find the bicubic peak efficiency points
        for RPMIndex in range(0,len(self.MapRPMs)):
            SubSampling = 4
            for SubRPMIndex in range(0, SubSampling):
                if len(self.MapRPMs)-1 == RPMIndex and 0 < SubRPMIndex:
                    continue
                RPMRatio = float(SubRPMIndex) / SubSampling
                CurrentRPM = self.MapRPMs[RPMIndex]
                if 0 < SubRPMIndex:
                    CurrentRPM += RPMRatio * (self.MapRPMs[RPMIndex+1] - self.MapRPMs[RPMIndex])
                CurrentConsumption = BicubicInterpolation( self.MapCubicEfficiencies[RPMIndex][0], RPMRatio, 0.0)
                MinEfficiency = CurrentConsumption
                MaxEfficiency = RotationalPower(CurrentRPM, self.MapTorques[0]) / CurrentConsumption
                MinEfficiencyTorque = self.MapTorques[0]
                MaxEfficiencyTorque = self.MapTorques[0]
                
                for TorqueIndex in range(0,len(self.MapTorques)-1):
                    CurrentTorque = self.MapTorques[TorqueIndex]
                    if CurrentTorque < self.CalculateMaxTorque(CurrentRPM):
                        CurrentConsumption = self.MapEfficiencies[RPMIndex][TorqueIndex]
                        if((MinEfficiency > CurrentConsumption)and(0.0 <= CurrentConsumption)):
                            MinEfficiency = CurrentConsumption
                            MinEfficiencyTorque = CurrentTorque
                        if(MaxEfficiency < (RotationalPower(CurrentRPM, CurrentTorque) / CurrentConsumption)):
                            MaxEfficiency = RotationalPower(CurrentRPM, CurrentTorque) / CurrentConsumption
                            MaxEfficiencyTorque = CurrentTorque
                        
                        Inflections = CubicInterpolationInflections( BicubicToCubicInterpolation(self.MapCubicEfficienciesTranspose[RPMIndex][TorqueIndex], RPMRatio) )
                        for Val in Inflections:
                            if type(Val) == float:
                                if(0.0 <= Val) and (1.0 >= Val):
                                    CurrentTorque = (self.MapTorques[TorqueIndex+1] - self.MapTorques[TorqueIndex]) * Val + self.MapTorques[TorqueIndex] 
                                    if CurrentTorque < self.CalculateMaxTorque(CurrentRPM):
                                        CurrentConsumption = BicubicInterpolation( self.MapCubicEfficiencies[RPMIndex][TorqueIndex], RPMRatio, Val)
                                        if((MinEfficiency > CurrentConsumption)and(0.0 <= CurrentConsumption)):
                                            MinEfficiency = CurrentConsumption
                                            MinEfficiencyTorque = CurrentTorque
                                        if(MaxEfficiency < (RotationalPower(CurrentRPM, CurrentTorque) / CurrentConsumption)):
                                            MaxEfficiency = RotationalPower(CurrentRPM, CurrentTorque) / CurrentConsumption
                                            MaxEfficiencyTorque = CurrentTorque
                
                if(self.NormalizedConsumption):
                    self.IdealCubicTorques.append(MinEfficiencyTorque)
                else:
                    self.IdealCubicTorques.append(MaxEfficiencyTorque)
                self.IdealCubicTorqueRPMs.append(CurrentRPM)

    def Save(self, filename, upscale = 1):
        OutputFile = open(filename, 'w', newline='')
        # Create a CSV writer from 
        OutputWriter = csv.writer(OutputFile, quoting=csv.QUOTE_ALL)
        for Parameter in self.Parameters:
            Row = [Parameter, self.Parameters[Parameter]]
            OutputWriter.writerow(Row)
         
        OutputWriter.writerow(['# RPM', 'Nm', 'g/kWh'])
        for Index in range(0,len(self.MaxPowerTorques)):
            for SubIndex in range(0, upscale):
                if len(self.MaxPowerTorques) -1 == Index and 0 < SubIndex:
                    continue
                RPM = self.MaxPowerRPMs[Index]
                if 0 < SubIndex:
                    RPM += (self.MaxPowerRPMs[Index+1] - self.MaxPowerRPMs[Index]) * SubIndex / upscale
                Torque = self.CalculateMaxTorque(RPM)
                for StabilizationSample in range(0, self.StabilizationSamples):
                    Efficiency = self.CalculateEfficiency(RPM, Torque)
                Row = [RPM, Torque, Efficiency]
                OutputWriter.writerow(Row)
            
        OutputWriter.writerow(['# g/kWh by RPM/Nm']) 
        OutputTorques = []
        Row = ['']
        for Index in range(0, len(self.MapTorques)):
            for SubIndex in range(0, upscale):
                if len(self.MapTorques) -1 == Index and 0 < SubIndex:
                    continue
                Torque = self.MapTorques[Index]
                if 0 < SubIndex:
                    Torque += (self.MapTorques[Index+1] - self.MapTorques[Index]) * SubIndex / upscale
                OutputTorques.append(Torque)
        Row.extend(OutputTorques)
        OutputWriter.writerow(Row)
        OutputRPMs = []
        for Index in range(0, len(self.MapRPMs)):
            for SubIndex in range(0, upscale):
                if len(self.MapRPMs) -1 == Index and 0 < SubIndex:
                    continue
                RPM = self.MapRPMs[Index]
                if 0 < SubIndex:
                    RPM += (self.MapRPMs[Index+1] - self.MapRPMs[Index]) * SubIndex / upscale
                OutputRPMs.append(RPM)
        for RPM in OutputRPMs:
            Row = [RPM]
            for Torque in OutputTorques:
                if Torque > self.CalculateMaxTorque(RPM):
                    Row.append(-1)
                else:
                    for StabilizationSample in range(0, self.StabilizationSamples):
                        Efficiency = self.CalculateEfficiency(RPM, Torque)
                    Row.append(Efficiency)
            OutputWriter.writerow(Row)
        OutputFile.close()
        
    def CalculateMaxTorque(self,rpm):
        if self.CalculateLinear:
            return self.CalculateMaxTorqueLinear(rpm)
        else:
            return self.CalculateMaxTorqueCubic(rpm)
            
    def CalculateMaxTorqueLinear(self,rpm):
        # Clip based on Min/Max RPM
        rpm = ClipValue(rpm,self.MapRPMs[0],self.MapRPMs[-1])
        # Look up RPM location in map
        RPMIndex = ArrayValueToIndex(rpm, self.MapRPMs)     
        if((self.PeakPowerListed)and(self.MaxPowerTorques[RPMIndex] > self.MaxPowerTorques[RPMIndex+1])): 
            # Max power of electric motor
            return RotationalTorque(RotationalPower(self.MapRPMs[RPMIndex+1], self.MaxPowerTorques[RPMIndex+1]),rpm)
        # Calculate the RPM Ratio
        RPMRatio = (rpm - self.MapRPMs[RPMIndex]) / (self.MapRPMs[RPMIndex+1] - self.MapRPMs[RPMIndex])
        return self.MaxPowerTorques[RPMIndex] * (1.0 - RPMRatio) + RPMRatio * self.MaxPowerTorques[RPMIndex+1]

    def CalculateMaxTorqueCubic(self,rpm):
        # Clip based on Min/Max RPM
        rpm = ClipValue(rpm,self.MapRPMs[0],self.MapRPMs[-1])
        # Look up RPM location in map
        RPMIndex = ArrayValueToIndex(rpm, self.MapRPMs)     
        if((self.PeakPowerListed)and(self.MaxPowerTorques[RPMIndex] > self.MaxPowerTorques[RPMIndex+1])): 
            # Max power of electric motor
            return RotationalTorque(RotationalPower(self.MapRPMs[RPMIndex+1], self.MaxPowerTorques[RPMIndex+1]),rpm)
        # Calculate the RPM Ratio
        RPMRatio = (rpm - self.MapRPMs[RPMIndex]) / (self.MapRPMs[RPMIndex+1] - self.MapRPMs[RPMIndex])
        # Get Parameters for the max torque values
        if 0 == RPMIndex:
            Parameters = [2.0 * self.MaxPowerTorques[0] - self.MaxPowerTorques[1]]
            Parameters.extend(self.MaxPowerTorques[:3])
        elif len(self.MapRPMs)-2 == RPMIndex:
            Parameters = self.MaxPowerTorques[-3:]
            Parameters.append(2.0 * self.MaxPowerTorques[-1] - self.MaxPowerTorques[-2])
        elif len(self.MapRPMs)-1 == RPMIndex:
            Parameters = self.MaxPowerTorques[-2:]
            Parameters.append(2.0 * self.MaxPowerTorques[-1] - self.MaxPowerTorques[-2])
            Parameters.append(3.0 * self.MaxPowerTorques[-1] - 2.0 * self.MaxPowerTorques[-2])
        else:
            Parameters = self.MaxPowerTorques[RPMIndex-1:RPMIndex+3]
        return CubicInterpolation(Parameters, RPMRatio) 

    def CalculateIdealTorque(self,rpm):
        if self.CalculateLinear:
            return self.CalculateIdealTorqueLinear(rpm)
        else:
            return self.CalculateIdealTorqueCubic(rpm)
            
    def CalculateIdealTorqueLinear(self,rpm):
        # Clip based on Min/Max RPM
        rpm = ClipValue(rpm,self.MapRPMs[0],self.MapRPMs[-1])
        # Look up RPM location in map
        RPMIndex = ArrayValueToIndex(rpm, self.MapRPMs)
        # Calculate the RPM Ratio
        RPMRatio = (rpm - self.MapRPMs[RPMIndex]) / (self.MapRPMs[RPMIndex+1] - self.MapRPMs[RPMIndex])
        return self.IdealTorques[RPMIndex] * (1.0 - RPMRatio) + RPMRatio * self.IdealTorques[RPMIndex+1]
    
    def CalculateIdealTorqueCubic(self,rpm):
        # Clip based on Min/Max RPM
        rpm = ClipValue(rpm,self.IdealCubicTorqueRPMs[0],self.IdealCubicTorqueRPMs[-1])
        # Look up RPM location in map
        RPMIndex = ArrayValueToIndex(rpm, self.IdealCubicTorqueRPMs)
        # Calculate the RPM Ratio
        RPMRatio = (rpm - self.IdealCubicTorqueRPMs[RPMIndex]) / (self.IdealCubicTorqueRPMs[RPMIndex+1] - self.IdealCubicTorqueRPMs[RPMIndex])
        # Get Parameters for the max torque values
        if 0 == RPMIndex:
            Parameters = [2.0 * self.IdealCubicTorques[0] - self.IdealCubicTorques[1]]
            Parameters.extend(self.IdealCubicTorques[:3])
        elif len(self.IdealCubicTorqueRPMs)-2 == RPMIndex:
            Parameters = self.IdealCubicTorques[-3:]
            Parameters.append(2.0 * self.IdealCubicTorques[-1] - self.IdealCubicTorques[-2])
        elif len(self.IdealCubicTorqueRPMs)-1 == RPMIndex:
            Parameters = self.IdealCubicTorques[-2:]
            Parameters.append(2.0 * self.IdealCubicTorques[-1] - self.IdealCubicTorques[-2])
            Parameters.append(3.0 * self.IdealCubicTorques[-1] - 2.0 * self.IdealCubicTorques[-2])
        else:
            Parameters = self.IdealCubicTorques[RPMIndex-1:RPMIndex+3]
        return CubicInterpolation(Parameters, RPMRatio) 
        
    def FindMaxPowerConsumptionRPMs(self, target, rpmmin, rpmmax):
        DeltaRPM = rpmmax - rpmmin
        # If found that min and max are same
        if 0.0 == DeltaRPM:
            if target == EffPoints.append(self.CalculateEfficiencyBicubic(rpmmin, self.CalculateMaxTorqueCubic(rpmmin))):
                return [rpmmin]
            return []
        RPMPoints = []
        EffPoints = []
        Sections = 16
        LastRPM = rpmmin-1.0
        for Index in range(0, Sections+1):
            CurrentRPM = rpmmin + DeltaRPM * Index / Sections
            # Don't add
            if CurrentRPM != LastRPM:
                RPMPoints.append( CurrentRPM )
                EffPoints.append(self.CalculateEfficiencyBicubic(CurrentRPM, self.CalculateMaxTorqueCubic(CurrentRPM)))
            LastRPM = CurrentRPM
        # No reason the further search
        if min(EffPoints) > target or max(EffPoints) < target:
            return []
        # If min and max are minimum distance appart find best point
        if 2 == len(RPMPoints):
            if abs(EffPoints[0] - target) < abs(EffPoints[1] - target):
                return [rpmmin]
            else:
                return [rpmmax]
        TargetRPMs = []
        # For all points search further if sufficient
        for Index in range(0, len(RPMPoints)-1):
            # If target lies between points
            if min(EffPoints[Index], EffPoints[Index+1]) <= target and max(EffPoints[Index], EffPoints[Index+1]) >= target:
                TargetRPMs.extend( self.FindMaxPowerConsumptionRPMs(target, RPMPoints[Index], RPMPoints[Index+1]) )
        return TargetRPMs
        
    # Find the ideal operating point for a particular power output
    # Return tuple (RPM, Torque, Consumption)
    def FindIdealOperation(self,power):
        if self.CalculateLinear:
            return self.FindIdealOperationLinear(power)
        else:
            return self.FindIdealOperationCubic(power)
            
    # Find the ideal operating point for a particular power output
    # Return tuple (RPM, Torque, Consumption)
    def FindIdealOperationLinear(self,power):
        # If power is below the minimum ideal power point
        if(power < RotationalPower(self.MapRPMs[0], self.IdealTorques[0])):
            # If power is below the minimum power of the engine
            if(power < RotationalPower(self.MapRPMs[0], self.MapTorques[0])):
                # Return minimum power values
                return (self.MapRPMs[0], self.MapTorques[0], self.MapEfficiencies[0][0])
            # Else the power is between ideal and asolute minimum
            else:
                # Return interpolated point for minimum RPM and required torque
                return (self.MapRPMs[0], RotationalTorque(power, self.MapRPMs[0]), self.CalculateEfficiency(self.MapRPMs[0], RotationalTorque(power, self.MapRPMs[0])))
        # Search for the ideal power line
        RPMIndex = 0
        while(RPMIndex + 1 < len(self.MapRPMs)):
            # If the power falls between the two points
            if((RotationalPower(self.MapRPMs[RPMIndex],self.IdealTorques[RPMIndex]) <= power)and(RotationalPower(self.MapRPMs[RPMIndex+1],self.IdealTorques[RPMIndex+1]) >= power)):
                # Calculate the torque line values for Y = M*X + B
                TorqueLineMB = LineCalculateMB(self.MapRPMs[RPMIndex],self.IdealTorques[RPMIndex],self.MapRPMs[RPMIndex+1],self.IdealTorques[RPMIndex+1])
                # Calculate the RPM solutions to pseudo power point convert W to N*m*RPM
                SpeedSolutions = QuadraticEquation(TorqueLineMB[0], TorqueLineMB[1], - power / (2 * math.pi / 60.0))
                # Solve based on different results
                if(2 == len(SpeedSolutions)):
                    # For both solutions
                    for SpeedSolution in SpeedSolutions:
                        # If solution is valid
                        if((SpeedSolution>= self.MapRPMs[RPMIndex])and(SpeedSolution <= self.MapRPMs[RPMIndex+1])):
                            return (SpeedSolution, RotationalTorque(power, SpeedSolution),self.CalculateEfficiency(SpeedSolution, RotationalTorque(power, SpeedSolution)))
                elif(1 == len(SpeedSolutions)):
                    # If solution is valid
                    if((SpeedSolutions[0]>= self.MapRPMs[RPMIndex])and(SpeedSolutions[0] <= self.MapRPMs[RPMIndex+1])):
                        return (SpeedSolutions[0], RotationalTorque(power, SpeedSolutions[0]),self.CalculateEfficiency(SpeedSolutions[0], RotationalTorque(power, SpeedSolutions[0])))
                # This shouldn't happen but in case it does use ratio 
                PowerRatio = (power - RotationalPower(self.MapRPMs[RPMIndex],self.IdealTorques[RPMIndex]))/(RotationalPower(self.MapRPMs[RPMIndex+1],self.IdealTorques[RPMIndex+1])-RotationalPower(self.MapRPMs[RPMIndex],self.IdealTorques[RPMIndex]))
                # Calculate the ideal speed 
                IdealSpeed = (1 - PowerRatio) * self.MapRPMs[RPMIndex] + PowerRatio * self.MapRPMs[RPMIndex+1]
                return (IdealSpeed, RotationalTorque(power, IdealSpeed),self.CalculateEfficiency(IdealSpeed, RotationalTorque(power, IdealSpeed)))
            RPMIndex += 1        
        return (self.MapRPMs[-1], RotationalTorque(power, self.MapRPMs[-1]), self.CalculateEfficiency(self.MapRPMs[-1], RotationalTorque(power, self.MapRPMs[-1])))
        
    # Find the ideal operating point for a particular power output
    # Return tuple (RPM, Torque, Consumption)
    def FindIdealOperationCubic(self,power):
        # If power is below the minimum ideal power point
        if(power < RotationalPower(self.IdealCubicTorqueRPMs[0], self.IdealCubicTorques[0])):
            # If power is below the minimum power of the engine
            if(power < RotationalPower(self.MapRPMs[0], self.MapTorques[0])):
                # Return minimum power values
                return (self.MapRPMs[0], self.MapTorques[0], self.MapEfficiencies[0][0])
            # Else the power is between ideal and asolute minimum
            else:
                # Return interpolated point for minimum RPM and required torque
                return (self.MapRPMs[0], RotationalTorque(power, self.MapRPMs[0]), self.CalculateEfficiency(self.MapRPMs[0], RotationalTorque(power, self.MapRPMs[0])))
        # Search for the ideal power line
        RPMIndex = 0
        while(RPMIndex + 1 < len(self.IdealCubicTorqueRPMs)):
            # If the power falls between the two points
            if((RotationalPower(self.IdealCubicTorqueRPMs[RPMIndex],self.IdealCubicTorques[RPMIndex]) <= power)and(RotationalPower(self.IdealCubicTorqueRPMs[RPMIndex+1],self.IdealCubicTorques[RPMIndex+1]) >= power)):
                # Get Parameters for Cubic Interpolation
                if 0 == RPMIndex:
                    ParamTorques = [2.0 * self.IdealCubicTorques[0] - self.IdealCubicTorques[1]]
                    ParamTorques.extend(self.IdealCubicTorques[:3])
                    ParamRPMs = [2.0 * self.IdealCubicTorqueRPMs[0] - self.IdealCubicTorqueRPMs[1]]
                    ParamRPMs.extend(self.IdealCubicTorqueRPMs[:3])
                elif len(self.IdealCubicTorqueRPMs)-2 == RPMIndex:
                    ParamTorques = self.IdealCubicTorques[-3:]
                    ParamTorques.append(2.0 * self.IdealCubicTorques[-1] - self.IdealCubicTorques[-2])
                    ParamRPMs = self.IdealCubicTorqueRPMs[-3:]
                    ParamRPMs.append(2.0 * self.IdealCubicTorqueRPMs[-1] - self.IdealCubicTorqueRPMs[-2])
                else:
                    ParamTorques = self.IdealCubicTorques[RPMIndex-1:RPMIndex+3]
                    ParamRPMs = self.IdealCubicTorqueRPMs[RPMIndex-1:RPMIndex+3]
                Params = []
                for Index in range(0, 4):
                    Params.append(RotationalPower(ParamRPMs[Index], ParamTorques[Index]))
                # Solve base upon power parameters
                Intersections = CubicInterpolationIntersections(Params, power)
                for Val in Intersections:
                    if type(Val) == float:
                        if(0.0 <= Val) and (1.0 > Val):
                            SpeedSolution = self.IdealCubicTorqueRPMs[RPMIndex] + (self.IdealCubicTorqueRPMs[RPMIndex+1] - self.IdealCubicTorqueRPMs[RPMIndex]) * Val
                            return (SpeedSolution, RotationalTorque(power, SpeedSolution),self.CalculateEfficiency(SpeedSolution, RotationalTorque(power, SpeedSolution)))
                # This shouldn't happen but in case it does use ratio 
                PowerRatio = (power - RotationalPower(self.IdealCubicTorqueRPMs[RPMIndex],self.IdealCubicTorques[RPMIndex]))/(RotationalPower(self.IdealCubicTorqueRPMs[RPMIndex+1],self.IdealCubicTorques[RPMIndex+1])-RotationalPower(self.IdealCubicTorqueRPMs[RPMIndex],self.IdealCubicTorques[RPMIndex]))
                # Calculate the ideal speed 
                IdealSpeed = (1 - PowerRatio) * self.IdealCubicTorqueRPMs[RPMIndex] + PowerRatio * self.IdealCubicTorqueRPMs[RPMIndex+1]
                return (IdealSpeed, RotationalTorque(power, IdealSpeed),self.CalculateEfficiency(IdealSpeed, RotationalTorque(power, IdealSpeed)))
            RPMIndex += 1        
        return (self.MapRPMs[-1], RotationalTorque(power, self.MapRPMs[-1]), self.CalculateEfficiency(self.MapRPMs[-1], RotationalTorque(power, self.MapRPMs[-1])))
    
    def CalculateLoadTorque(self,consumption,rpm):
        # Clip based on Min/Max RPM
        rpm = ClipValue(rpm,self.MapRPMs[0],self.MapRPMs[-1])
        # Look up RPM location in map
        RPMIndex = ArrayValueToIndex(rpm, self.MapRPMs)
        # Calculate the RPM Ratio
        RPMRatio = (rpm - self.MapRPMs[RPMIndex]) / (self.MapRPMs[RPMIndex+1] - self.MapRPMs[RPMIndex])
        # Create list of torques and consumption rates
        TorqueList = []
        ConsumptionList = []
        for TorqueIndex in range(0,len(self.MapTorques)):
            if((self.MapTorques[TorqueIndex] < self.MaxPowerTorques[RPMIndex])and(self.MapTorques[TorqueIndex] < self.MaxPowerTorques[RPMIndex+1])):
                TorqueList.append(self.MapTorques[TorqueIndex])
                ConsumptionList.append( self.MapEfficiencies[RPMIndex][TorqueIndex] * (1.0 - RPMRatio) + RPMRatio * self.MapEfficiencies[RPMIndex+1][TorqueIndex] )
        # Add peak torque and consumption
        TorqueList.append( self.MaxPowerTorques[RPMIndex] * (1.0 - RPMRatio) + RPMRatio * self.MaxPowerTorques[RPMIndex+1] )
        ConsumptionList.append( self.MaxPowerEfficiency[RPMIndex] * (1.0 - RPMRatio) + RPMRatio * self.MaxPowerEfficiency[RPMIndex+1] )        
        if(0.0 > consumption):
            for TorqueIndex in range(0,len(TorqueList)):
                InputPower = RotationalPower(rpm, TorqueList[TorqueIndex])
                EnergyEfficiency = InputPower / ConsumptionList[TorqueIndex]
                ConsumptionList[TorqueIndex] = ConsumptionList[0] - InputPower * EnergyEfficiency
                TorqueList[TorqueIndex] = -TorqueList[TorqueIndex]
                
        ReturnTorques = []
        LookupIndices = ArrayValuesToIndices(consumption, ConsumptionList)
        for Index in LookupIndices:
            Ratio = Index - int(Index)
            ReturnTorques.append( TorqueList[int(Index)] * (1.0 - Ratio) + Ratio * TorqueList[int(Index)+1] )
        return tuple( ReturnTorques )
        
    def CalculateEfficiency(self,rpm,torque):
        if self.CalculateLinear:
            return self.CalculateEfficiencyBilinear(rpm,torque)
        else:
            return self.CalculateEfficiencyBicubic(rpm,torque)
            
        
    def CalculateEfficiencyBilinear(self,rpm,torque):
        TorqueIndex = 0
        # Clip based on Min/Max RPM
        rpm = ClipValue(rpm,self.MapRPMs[0],self.MapRPMs[-1])
        if((self.NegativeTorqueAllowed)and(0.0 > torque)):
            #if regen on motor
            MaxTorqueForRPM = self.CalculateMaxTorque(rpm)
            if(-torque > MaxTorqueForRPM):
                torque = -MaxTorqueForRPM
            ConsumptionEnergy = self.CalculateEfficiency(rpm,-torque)
            InputPower = RotationalPower(rpm, -torque)
            EnergyEfficiency = InputPower / ConsumptionEnergy
            if(self.MapRPMs[1] <= rpm):
                return self.CalculateEfficiency(rpm,0.0) - InputPower * EnergyEfficiency
            else:
                SlowSpeedRatio = (rpm - self.MapRPMs[0])/(self.MapRPMs[1] - self.MapRPMs[0])
                return self.CalculateEfficiency(rpm,0.0) - InputPower * EnergyEfficiency * SlowSpeedRatio
            
        # Look up RPM location in map
        RPMIndex = ArrayValueToIndex(rpm, self.MapRPMs)
        # Calculate the RPM Ratio
        RPMRatio = (rpm - self.MapRPMs[RPMIndex]) / (self.MapRPMs[RPMIndex+1] - self.MapRPMs[RPMIndex])
        MaxTorqueForRPM = self.MaxPowerTorques[RPMIndex] * (1.0 - RPMRatio) + RPMRatio * self.MaxPowerTorques[RPMIndex+1]
        # Clip based on Min/Max Torque
        torque = ClipValue(torque,self.MapTorques[0],MaxTorqueForRPM)
        # Look up Torque location in map
        TorqueIndex = ArrayValueToIndex(torque, self.MapTorques)
        # If on edge of map
        if((self.MapTorques[TorqueIndex+1] > self.MaxPowerTorques[RPMIndex])or(self.MapTorques[TorqueIndex+1] > self.MaxPowerTorques[RPMIndex+1])or(self.MaxPowerTorques[RPMIndex] <= torque)or(self.MaxPowerTorques[RPMIndex+1] <= torque)):
            # Interpolate to find the top consumption number
            TopTorque = MaxTorqueForRPM
            TorqueRatio = (torque - self.MapTorques[TorqueIndex])/(MaxTorqueForRPM - self.MapTorques[TorqueIndex])
            ConsumptionHigh = self.MaxPowerEfficiency[RPMIndex] * (1.0 - RPMRatio) + RPMRatio * self.MaxPowerEfficiency[RPMIndex+1]
        # Else in the main part of the map
        else:
            # Interpolate to find the top consumption number
            TopTorque = self.MapTorques[TorqueIndex+1]
            TorqueRatio = (torque - self.MapTorques[TorqueIndex])/(self.MapTorques[TorqueIndex+1] - self.MapTorques[TorqueIndex])
            ConsumptionHigh = self.MapEfficiencies[RPMIndex][TorqueIndex+1] * (1.0 - RPMRatio) + RPMRatio * self.MapEfficiencies[RPMIndex+1][TorqueIndex+1]
        if(self.MapTorques[TorqueIndex] > self.MaxPowerTorques[RPMIndex]):
            BottomTorque = self.MaxPowerTorques[RPMIndex] * (1.0 - RPMRatio) + RPMRatio * self.MapTorques[TorqueIndex]
            # Interpolate to find the bottom consumption number
            ConsumptionLow = self.MaxPowerEfficiency[RPMIndex] * (1.0 - RPMRatio) + RPMRatio * self.MapEfficiencies[RPMIndex+1][TorqueIndex]

        elif(self.MapTorques[TorqueIndex] > self.MaxPowerTorques[RPMIndex+1]):
            BottomTorque = self.MapTorques[TorqueIndex] * (1.0 - RPMRatio) + RPMRatio * self.MaxPowerTorques[RPMIndex+1]
            # Interpolate to find the bottom consumption number
            ConsumptionLow = self.MapEfficiencies[RPMIndex][TorqueIndex] * (1.0 - RPMRatio) + RPMRatio * self.MaxPowerEfficiency[RPMIndex+1]
        else:
            # Interpolate to find the bottom consumption number
            BottomTorque = self.MapTorques[TorqueIndex]
            ConsumptionLow = self.MapEfficiencies[RPMIndex][TorqueIndex] * (1.0 - RPMRatio) + RPMRatio * self.MapEfficiencies[RPMIndex+1][TorqueIndex]
        TorqueRatio = (torque - BottomTorque)/(TopTorque - BottomTorque)
        # Linear interpolate, interpolated points
        return ConsumptionHigh * TorqueRatio + ConsumptionLow * (1 - TorqueRatio);

    def CalculateEfficiencyBicubic(self,rpm,torque):
        TorqueIndex = 0
        # Clip based on Min/Max RPM
        rpm = ClipValue(rpm,self.MapRPMs[0],self.MapRPMs[-1])
        if((self.NegativeTorqueAllowed)and(0.0 > torque)):
            #if regen on motor
            MaxTorqueForRPM = self.CalculateMaxTorqueCubic(rpm)
            if(-torque > MaxTorqueForRPM):
                torque = -MaxTorqueForRPM
            ConsumptionEnergy = self.CalculateEfficiencyBicubic(rpm,-torque)
            InputPower = RotationalPower(rpm, -torque)
            EnergyEfficiency = InputPower / ConsumptionEnergy
            if(self.MapRPMs[1] <= rpm):
                return self.CalculateEfficiencyBicubic(rpm,0.0) - InputPower * EnergyEfficiency
            else:
                SlowSpeedRatio = (rpm - self.MapRPMs[0])/(self.MapRPMs[1] - self.MapRPMs[0])
                return self.CalculateEfficiencyBicubic(rpm,0.0) - InputPower * EnergyEfficiency * SlowSpeedRatio
            
        # Look up RPM location in map
        RPMIndex = ArrayValueToIndex(rpm, self.MapRPMs)
        # Calculate the RPM Ratio
        RPMRatio = (rpm - self.MapRPMs[RPMIndex]) / (self.MapRPMs[RPMIndex+1] - self.MapRPMs[RPMIndex])
        MaxTorqueForRPM = self.CalculateMaxTorqueCubic(rpm) #self.MaxPowerTorques[RPMIndex] * (1.0 - RPMRatio) + RPMRatio * self.MaxPowerTorques[RPMIndex+1]
        # Clip based on Min/Max Torque
        torque = ClipValue(torque,self.MapTorques[0],MaxTorqueForRPM)
        # Look up Torque location in map
        TorqueIndex = ArrayValueToIndex(torque, self.MapTorques)
        # Calculate Torque Ratio
        TorqueRatio = (torque - self.MapTorques[TorqueIndex])/(self.MapTorques[TorqueIndex+1] - self.MapTorques[TorqueIndex])
        
        return BicubicInterpolation( self.MapCubicEfficiencies[RPMIndex][TorqueIndex], RPMRatio, TorqueRatio)
    
   
        
