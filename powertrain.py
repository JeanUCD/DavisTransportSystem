#
#   TTP Powertrain Class
#
import math
from ttputils import *
from engineefficiencymap import *
from transmission import *
from battery import *
from vehicleload import *

class Powertrain:
    def __init__(self, engine, motor, battery, trans, vehicle):
        self.BatteryPack = battery
        self.EngineMap = engine
        self.MotorMap = motor
        self.Transmission = trans
        self.Vehicle = vehicle
        self.Vehicle.Mass += self.Mass()
        self.Reset()
    
    def Reset(self, resettemps = True):
        if self.EngineMap:
            InitialSOC = 0.60
            if resettemps:
                self.EngineMap.Reset()
        else:
            InitialSOC = 1.00
        PackCapacity = 4000.0 # Wh
        
        if self.BatteryPack:
            PackCapacity = self.BatteryPack.EnergyCapacity
            self.BatteryPack.Reset(PackCapacity * InitialSOC)
            
        self.Vehicle.Reset()
        self.InitialEnergy = PackCapacity * InitialSOC    
        self.ChargeThreshold = 0.65
        self.DischargeThreshold = 0.55
        self.SOCTarget = 0.60
        self.EffectiveSOCTarget = 0.60
        self.Charging = False
        self.PowerOutputBuffer = []
        self.LastTime = 0.0
        if self.Transmission.IsCVT:
            self.CurrentGear = 0
        else:
            self.CurrentGear = 1
        
        
    def Mass(self):
        ReturnedMass = 0.0
        if self.BatteryPack:
            ReturnedMass = ReturnedMass + self.BatteryPack.Mass
        if self.EngineMap:
            ReturnedMass = ReturnedMass + self.EngineMap.Mass
        if self.MotorMap:
            ReturnedMass = ReturnedMass + self.MotorMap.Mass
        return ReturnedMass
                    
    def CalculateTimestep(self, speed, nexttime):
        # Calculate delta time
        DeltaTime = nexttime - self.LastTime
        # Calculate power output
        PostTransmissionPower = self.Vehicle.PowerRequired(speed,DeltaTime)
        # Calculate RPM out of transmission
        PostTransmissionRPM = self.Vehicle.PostTransmissionSpeed()
        # Determine powertrain settings
        PowertrainSettings = self.DeterminePowertrainSettings(PostTransmissionPower, PostTransmissionRPM)
        if self.MotorMap:
            # Determine motor power
            MotorPower = self.MotorMap.CalculateEfficiency(PowertrainSettings[1],PowertrainSettings[2])
        else:
            MotorPower = 0.0
        
        EngineTemperatures = (0.0, 0.0, 0.0)
        if self.EngineMap and (0.0 < PowertrainSettings[3]):
            # Determine engine outputs
            EngineOutputs = self.EngineMap.CalculateEfficiencyAndEmissions(PowertrainSettings[1],PowertrainSettings[3])
            EngineEnergyOutput = PowerTimeTokWh(RotationalPower(PowertrainSettings[1],PowertrainSettings[3]), DeltaTime)
        else:
            EngineOutputs = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            EngineEnergyOutput = 0.0

        self.LastTime = nexttime
        # Time, Speed, Distance, Gear, Powertrain RPM
        OutputList = [ nexttime,speed,self.Vehicle.DistanceTraveled, PowertrainSettings[0], PowertrainSettings[1] ]
        if(0.0 < DeltaTime):
            if self.EngineMap:
                self.EngineMap.UpdateTemperatures(DeltaTime)
                EngineTemperatures = self.EngineMap.GetTemperatures()
            EngineGramsFuel = EngineOutputs[0] * DeltaTime
            EngineGramsHC = EngineOutputs[1] * DeltaTime
            EngineGramsCO = EngineOutputs[2] * DeltaTime
            EngineGramsNOx = EngineOutputs[3] * DeltaTime
            EngineGramsPM = EngineOutputs[4] * DeltaTime
            HeatInJoules = EngineOutputs[5] * DeltaTime
            CatalystGramsHC = EngineOutputs[6] * DeltaTime
            CatalystGramsCO = EngineOutputs[7] * DeltaTime
            CatalystGramsNOx = EngineOutputs[8] * DeltaTime
            CatalystGramsPM = EngineOutputs[9] * DeltaTime
            
            if self.BatteryPack:                    
                PackData = self.BatteryPack.UpdatePackLoad(MotorPower,DeltaTime)
                DeltaElectricalEnergy = self.InitialEnergy-self.BatteryPack.CurrentEnergy
            else:
                PackData = (0.0, 0.0, 0.0)
                DeltaElectricalEnergy = 0.0
            # Add Motor Power, Pack Energy, SOC, V, I
            OutputList.extend([MotorPower, DeltaElectricalEnergy, PackData[0], PackData[1], PackData[2]])
            # Add Fuel, HC', CO', NOx', PM', Heat, ICE Temp, Coolant Temp
            OutputList.extend([EngineGramsFuel, EngineGramsHC, EngineGramsCO, EngineGramsNOx, EngineGramsPM, HeatInJoules, EngineTemperatures[0], EngineTemperatures[1]])
            # Add HC, CO, NOx, PM
            OutputList.extend([ CatalystGramsHC, CatalystGramsCO, CatalystGramsNOx, CatalystGramsPM, EngineTemperatures[2]])
        else:
            if self.EngineMap:
                EngineTemperatures = self.EngineMap.GetTemperatures()
            if self.BatteryPack:                    
                PackData = (self.BatteryPack.SOC(), self.BatteryPack.OpenCircuitVoltage(), 0.0)
            else:
                PackData = (0.0, 0.0, 0.0)
            DeltaElectricalEnergy = 0.0            
            # Add Motor Power, Pack Energy, SOC, V, I
            OutputList.extend([MotorPower, DeltaElectricalEnergy, PackData[0], PackData[1], PackData[2]])
            # Add Fuel, HC', CO', NOx', PM', Heat, ICE Temp, Coolant Temp
            OutputList.extend([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, EngineTemperatures[0], EngineTemperatures[1]])
            # Add HC, CO, NOx, PM
            OutputList.extend([ 0.0, 0.0, 0.0, 0.0, EngineTemperatures[2]])
        return tuple(OutputList)
                  
                  
    # Returns vehicle fuel type
    def FuelType(self):
        
        if self.EngineMap:
            return self.EngineMap.Parameters[ "fueltype" ] 
        else:
            # Just return gasoline even though none is used
            return "gasoline"
            
    # Returns Gear, RPM, Motor Torque, Engine Torque                
    def DeterminePowertrainSettings(self,outpower,outrpm):
        
        if self.EngineMap:
            if self.MotorMap:
                return self.DeterminePowertrainSettingsHEV(outpower, outrpm)
            else:
                return self.DeterminePowertrainSettingsConventional(outpower, outrpm)
        elif self.MotorMap:
            return self.DeterminePowertrainSettingsEV(outpower, outrpm)
        else:
            print("ERROR: Need to specify at least one propulsion mode")
            return None
                    
    # Returns Gear, RPM, Motor Torque, Engine Torque                
    def DeterminePowertrainSettingsHEV(self,outpower,outrpm):
        
        if self.Transmission.IsCVT:
            BestGear = 0
            if(0.0 < outrpm):
                RequiredInputMin = self.Transmission.CalculateInputs(outpower, outrpm, 0.0)
                RequiredInputMax = self.Transmission.CalculateInputs(outpower, outrpm, 1.0)
                if((self.EngineMap.MapRPMs[0] <= RequiredInputMin[1])and(RequiredInputMax[1] <= self.EngineMap.MapRPMs[-1])):
                    BestGear = self.Transmission.FindClosestGear(self.EngineMap.FindIdealOperation(RequiredInputMin[0])[0], outrpm)
        else:
            # limit shifting to 2 gears per second
            MaxGearChanges = 2
            # Set gears to check for best consumption
            MinGearRange = self.CurrentGear - MaxGearChanges - 1
            if(MinGearRange < 1):
                MinGearRange = 1
            MaxGearRange = self.CurrentGear + MaxGearChanges + 1 
            if(MaxGearRange > len(self.Transmission.Ratios)):
                MaxGearRange = len(self.Transmission.Ratios)
            BestGear = 1
            BestConsumption = 1000000000.0
            BestIsBelowIOL = False
            # For each gear in the range check if it is best consumption
            for Index in range(MinGearRange,MaxGearRange):
                if(0.0 < outrpm):
                    RequiredInput = self.Transmission.CalculateInputs(outpower, outrpm, Index)
                    # If in operational range of the engine consider it
                    if((self.EngineMap.MapRPMs[0] <= RequiredInput[1])and(RequiredInput[1] <= self.EngineMap.MapRPMs[-1])):
                        # Get consumption for RPM/Torque
                        CurrentConsumption = self.EngineMap.CalculateEfficiency(RequiredInput[1], RequiredInput[2])
                        if(CurrentConsumption < BestConsumption):
                            BelowIOL = RequiredInput[2] <= self.EngineMap.CalculateIdealTorque(RequiredInput[1])
                            if BelowIOL or BestIsBelowIOL == BelowIOL:
                                BestConsumption = CurrentConsumption
                                BestGear = Index
                                BestIsBelowIOL = BelowIOL
                            
        self.CurrentGear = BestGear
        # Determine required inputs for the selected gear
        EngineAndMotorRequirements = self.Transmission.CalculateInputs(outpower, outrpm, self.CurrentGear)
        # Add value to the power buffer to get a 5 second running average
        if(4 < len(self.PowerOutputBuffer)):
            self.PowerOutputBuffer.pop(0)
        self.PowerOutputBuffer.append( EngineAndMotorRequirements[0] )
        AveragePower = 0.0
        for PowerValue in self.PowerOutputBuffer:
            AveragePower += PowerValue
        AveragePower /= len(self.PowerOutputBuffer)
        # Grab torque and RPM output of engine/motor
        TotalTorque = EngineAndMotorRequirements[2]
        InputRPM = EngineAndMotorRequirements[1]
        TorqueRatio = 1.0
        if(outpower < 0.0):
            # Implement mechanical braking
            BrakingThreshold = 10000.0
            if((abs(outpower) / BrakingThreshold) < 1.0):
                TorqueRatio = 0.90 - (abs(outpower) / BrakingThreshold) * 0.40
            else:
                TorqueRatio = BrakingThreshold / (2.0 * abs(outpower))
            TotalTorque *= TorqueRatio
        self.EffectiveSOCTarget = self.SOCTarget - ((0.25 * self.Vehicle.KineticEnergy() / 3600.0)/self.BatteryPack.EnergyCapacity)
        # If RPM is less than minimum for engine use motor only
        if(InputRPM < self.EngineMap.MapRPMs[0]):
            MotorTorque = TotalTorque
            EngineTorque = 0.0
        # Else engine can be used
        else:
            # Initially assume engine provides all torque
            EngineTorque = TotalTorque
            if(EngineTorque < self.EngineMap.MapTorques[0]):
                # Set engine to minimum torque output
                EngineTorque = self.EngineMap.MapTorques[0]
                # Make up rest of torque with motor
                MotorTorque = TotalTorque - EngineTorque
                self.Charging = False
            else:
                ChargeDischargeTorque = 0.0
                # Calculate additional power for charging
                if(self.Charging):
                    # Determine energy deficit
                    EnergyRequired = (self.EffectiveSOCTarget - self.BatteryPack.SOC()) * self.BatteryPack.EnergyCapacity
                    # Account for kinetic energy
                    #EnergyRequired -= 0.25 * self.Vehicle.KineticEnergy() / 3600.0
                    # Set Time constant
                    TimeConstant = 60.0 # Charge in 60 seconds
                    # Calculate the charge rate in W
                    ChargeRate = EnergyRequired * 3600.0 / TimeConstant
                    if(ChargeRate < 0.0):
                        ChargeRate *= 10.0
                    # Calculate the additional torque
                    PossibleTorques = self.MotorMap.CalculateLoadTorque(-ChargeRate, InputRPM)
                    if(1 <= len(PossibleTorques)):
                        ChargeDischargeTorque = -max(PossibleTorques)
                    else:
                        ChargeDischargeTorque = RotationalTorque(ChargeRate, InputRPM)
                    AveragePowerTrigger =  (self.EngineMap.PeakPower + self.MotorMap.PeakPower) * 0.10 * (1.0 - (self.ChargeThreshold - self.BatteryPack.SOC())/(self.ChargeThreshold - self.EffectiveSOCTarget))
                    if(self.BatteryPack.SOC() > self.ChargeThreshold):
                        self.Charging = False
                    elif((AveragePower > AveragePowerTrigger)and(self.EffectiveSOCTarget < self.BatteryPack.SOC())):
                        self.Charging = False
                else:
                    PowerRatio = ((outpower / self.MotorMap.PeakPower)**3) * 0.5
                    ChargeDischargeTorque = -RotationalTorque(PowerRatio * outpower, InputRPM)
                    AveragePowerTrigger =  (self.EngineMap.PeakPower + self.MotorMap.PeakPower) * 0.10 * (1.0 - (self.BatteryPack.SOC() - self.DischargeThreshold)/(self.EffectiveSOCTarget - self.DischargeThreshold))
                    if(self.BatteryPack.SOC() < self.DischargeThreshold):
                        self.Charging = True
                    elif((AveragePower < AveragePowerTrigger)and(self.EffectiveSOCTarget > self.BatteryPack.SOC())):
                        self.Charging = True    

                # If above ideal torque of engine scale back
                IdealEngineTorque = self.EngineMap.CalculateIdealTorque(InputRPM)
                if(EngineTorque + ChargeDischargeTorque > IdealEngineTorque):
                    if(EngineTorque < IdealEngineTorque):
                        EngineTorque = IdealEngineTorque
                # If below minimum engine torque set to minimum
                elif(EngineTorque + ChargeDischargeTorque < self.EngineMap.MapTorques[0]):
                    EngineTorque = self.EngineMap.MapTorques[0]
                else:
                    EngineTorque += ChargeDischargeTorque
                # Make up rest of torque with motor
                MotorTorque = TotalTorque - EngineTorque
                  
        return (self.CurrentGear, InputRPM, MotorTorque, EngineTorque)    

    # Returns Gear, RPM, Motor Torque, Engine Torque                
    def DeterminePowertrainSettingsConventional(self,outpower,outrpm):
        if self.Transmission.IsCVT:
            BestGear = 0
            if(0.0 < outrpm):
                RequiredInputMin = self.Transmission.CalculateInputs(outpower, outrpm, 0.0)
                RequiredInputMax = self.Transmission.CalculateInputs(outpower, outrpm, 1.0)
                if((self.EngineMap.MapRPMs[0] <= RequiredInputMin[1])and(RequiredInputMax[1] <= self.EngineMap.MapRPMs[-1])):
                    BestGear = self.Transmission.FindClosestGear(self.EngineMap.FindIdealOperation(RequiredInputMin[0])[0], outrpm)

        else:
            # limit shifting to 2 gears per second
            MaxGearChanges = 2
            # Set gears to check for best consumption
            MinGearRange = self.CurrentGear - MaxGearChanges - 1
            if(MinGearRange < 1):
                MinGearRange = 1
            MaxGearRange = self.CurrentGear + MaxGearChanges + 1 
            if(MaxGearRange > len(self.Transmission.Ratios)):
                MaxGearRange = len(self.Transmission.Ratios)
            BestGear = 1
            BestConsumption = 1000000000.0
            BestIsBelowIOL = False
            # For each gear in the range check if it is best consumption
            for Index in range(MinGearRange,MaxGearRange):
                if(0.0 < outrpm):
                    RequiredInput = self.Transmission.CalculateInputs(outpower, outrpm, Index)
                    # If in operational range of the engine consider it
                    if((self.EngineMap.MapRPMs[0] <= RequiredInput[1])and(RequiredInput[1] <= self.EngineMap.MapRPMs[-1])):
                        # Get consumption for RPM/Torque
                        CurrentConsumption = self.EngineMap.CalculateEfficiency(RequiredInput[1], RequiredInput[2])
                        if(CurrentConsumption < BestConsumption):
                            BelowIOL = RequiredInput[2] <= self.EngineMap.CalculateIdealTorque(RequiredInput[1])
                            if BelowIOL or BestIsBelowIOL == BelowIOL:
                                BestConsumption = CurrentConsumption
                                BestGear = Index
                                BestIsBelowIOL = BelowIOL
        
        self.CurrentGear = BestGear
        EngineAndMotorRequirements = self.Transmission.CalculateInputs(outpower, outrpm, self.CurrentGear)
        EngineTorque = EngineAndMotorRequirements[2]
        InputRPM = EngineAndMotorRequirements[1]
        # If RPM is less than minimum for engine use motor only
        if(InputRPM < self.EngineMap.MapRPMs[0]):
            if(0.0 < InputRPM):
                EngineTorque = RotationalTorque(outpower,self.EngineMap.MapRPMs[0])
            InputRPM = self.EngineMap.MapRPMs[0]            
        if(EngineTorque < self.EngineMap.MapTorques[0]):
            EngineTorque = self.EngineMap.MapTorques[0]
                  
        return (self.CurrentGear, InputRPM, 0.0, EngineTorque)   

    # Returns Gear, RPM, Motor Torque, Engine Torque                
    def DeterminePowertrainSettingsEV(self,outpower,outrpm):
        if self.Transmission.IsCVT:
            BestGear = 0
            if(0.0 < outrpm):
                RequiredInputMin = self.Transmission.CalculateInputs(outpower, outrpm, 0.0)
                RequiredInputMax = self.Transmission.CalculateInputs(outpower, outrpm, 1.0)
                if((self.MotorMap.MapRPMs[0] <= RequiredInputMin[1])and(RequiredInputMax[1] <= self.MotorMap.MapRPMs[-1])):
                    BestGear = self.Transmission.FindClosestGear(self.MotorMap.FindIdealOperation(RequiredInputMin[0])[0], outrpm)
        else:
            BestGear = 1
            BestConsumption = 1000000000.0
            # For each gear in the range check if it is best consumption
            for Index in range(1,len(self.Transmission.Ratios)):
                if(0.0 < outrpm):
                    RequiredInput = self.Transmission.CalculateInputs(outpower, outrpm, Index)
                    # If in operational range of the engine consider it
                    if((self.MotorMap.MapRPMs[0] <= RequiredInput[1])and(RequiredInput[1] <= self.MotorMap.MapRPMs[-1])):
                        # Get consumption for RPM/Torque
                        CurrentConsumption = self.MotorMap.CalculateEfficiency(RequiredInput[1], RequiredInput[2])
                        if(CurrentConsumption < BestConsumption):
                            BestConsumption = CurrentConsumption
                            BestGear = Index
        self.CurrentGear = BestGear
        # Determine required inputs for the selected gear
        EngineAndMotorRequirements = self.Transmission.CalculateInputs(outpower, outrpm, self.CurrentGear)
        # Grab torque and RPM output of engine/motor
        TotalTorque = EngineAndMotorRequirements[2]
        InputRPM = EngineAndMotorRequirements[1]
        TorqueRatio = 1.0
        if(outpower < 0.0):
            # Implement mechanical braking
            BrakingThreshold = 10000.0
            if((abs(outpower) / BrakingThreshold) < 1.0):
                TorqueRatio = 0.90 - (abs(outpower) / BrakingThreshold) * 0.40
            else:
                TorqueRatio = BrakingThreshold / (2.0 * abs(outpower))
            TotalTorque *= TorqueRatio        
        return (self.CurrentGear, InputRPM, TotalTorque, 0.0)  

    def Calculate0to60(self):
        # Initialize speed at zero
        self.Vehicle.LastSpeed = 0.0
        self.Vehicle.CurrentSpeed = 0.0
        Time = 0.0
        MaxPower = 0.0
        # While speed is less than 60MPH
        while(self.Vehicle.CurrentSpeed < ConvertMPHToMPS(60.0)):
            # Determin power transmission RPM
            PostTransmissionRPM = self.Vehicle.PostTransmissionSpeed()
            MaxPower = 0.0
            if self.Transmission.IsCVT:
                RPMSToCheck = [ self.Transmission.Ratios[0] * PostTransmissionRPM ]
                if self.EngineMap:
                    RPMSToCheck.extend(list(self.EngineMap.MapRPMs))
                if self.MotorMap:
                    RPMSToCheck.extend(list(self.MotorMap.MapRPMs))
                    
                RPMSToCheck.sort()
                
                # for each gear find max power configuration
                for InputRPM in RPMSToCheck:
                    if (self.Transmission.Ratios[0] * PostTransmissionRPM >= InputRPM) and (self.Transmission.Ratios[1] * PostTransmissionRPM <= InputRPM): 
                        Index = 1
                        if (InputRPM >= self.Transmission.Ratios[0] * PostTransmissionRPM):
                            Index = 0
                        CurrentPower = 0.0
                        
                        if self.EngineMap:
                            # if in first gear determine max power at minimum RPM
                            if((Index == 0)and(InputRPM < self.EngineMap.MapRPMs[0])):
                                CurrentPower += RotationalPower(self.EngineMap.MapRPMs[0], self.EngineMap.CalculateMaxTorque(self.EngineMap.MapRPMs[0]))
                            # if able to use this gear determin max power output
                            elif((self.EngineMap.MapRPMs[0] <= InputRPM)and(InputRPM <= self.EngineMap.MapRPMs[-1])):
                                CurrentPower += RotationalPower(InputRPM, self.EngineMap.CalculateMaxTorque(InputRPM))
                        if self.MotorMap:
                            # if in first gear determine max power at minimum RPM
                            if((Index == 0)and(InputRPM < self.MotorMap.MapRPMs[0])):
                                CurrentPower += RotationalPower(self.MotorMap.MapRPMs[0], self.MotorMap.CalculateMaxTorque(self.MotorMap.MapRPMs[0]))
                            # if able to use this gear determin max power output
                            elif((self.MotorMap.MapRPMs[0] <= InputRPM)and(InputRPM <= self.MotorMap.MapRPMs[-1])):
                                CurrentPower += RotationalPower(InputRPM, self.MotorMap.CalculateMaxTorque(InputRPM))
                        # if this gear has more power than max power found, update
                        MaxPower = max(CurrentPower, MaxPower)
            else:
                # for each gear find max power configuration
                for Index in range(1,len(self.Transmission.Ratios)):
                    InputRPM = self.Transmission.Ratios[Index] * PostTransmissionRPM
                    CurrentPower = 0.0
                    
                    if self.EngineMap:
                        # if in first gear determine max power at minimum RPM
                        if((Index == 1)and(InputRPM < self.EngineMap.MapRPMs[0])):
                            CurrentPower += RotationalPower(self.EngineMap.MapRPMs[0], self.EngineMap.CalculateMaxTorque(self.EngineMap.MapRPMs[0]))
                        # if able to use this gear determin max power output
                        elif((self.EngineMap.MapRPMs[0] <= InputRPM)and(InputRPM <= self.EngineMap.MapRPMs[-1])):
                            CurrentPower += RotationalPower(InputRPM, self.EngineMap.CalculateMaxTorque(InputRPM))
                    if self.MotorMap:
                        # if in first gear determine max power at minimum RPM
                        if((Index == 1)and(InputRPM <= self.MotorMap.MapRPMs[0])):
                            if 0.0 == self.MotorMap.MapRPMs[0]:
                                CurrentPower += RotationalPower(100.0, self.MotorMap.CalculateMaxTorque(self.MotorMap.MapRPMs[0]))
                            else:
                                CurrentPower += RotationalPower(self.MotorMap.MapRPMs[0], self.MotorMap.CalculateMaxTorque(self.MotorMap.MapRPMs[0]))
                        # if able to use this gear determin max power output
                        elif((self.MotorMap.MapRPMs[0] <= InputRPM)and(InputRPM <= self.MotorMap.MapRPMs[-1])):
                            CurrentPower += RotationalPower(InputRPM, self.MotorMap.CalculateMaxTorque(InputRPM))
                        
                    # if this gear has more power than max power found, update
                    MaxPower = max(CurrentPower, MaxPower)
            # Adjust for transmission efficiency
            MaxPower *= self.Transmission.Efficiency
            # Determine acceleration from max power output
            Acceleration = self.Vehicle.MaxAcceleration(MaxPower)
            # Do acceleration 
            self.Vehicle.LastSpeed = self.Vehicle.CurrentSpeed
            self.Vehicle.CurrentSpeed += Acceleration * 0.001
            Time += 0.001
        return Time
        
    def Calculate6PercentGradeSpeed(self):
        LowSpeed = 0.0
        HighSpeed = 1000.0
        DeltaSpeed = 500.0
        # Determine usable capacity of battery pack and 10min drain rate
        DischargeRate10min = (self.BatteryPack.EnergyCapacity * 0.8 * 3600.0) / 600.0
        while(DeltaSpeed > 0.001):
            # Set target speed narrowing in on speed for the grade
            self.Vehicle.LastSpeed = (HighSpeed + LowSpeed) * 0.5
            self.Vehicle.CurrentSpeed = self.Vehicle.LastSpeed
            # Calculate the power required for the particular speed and post transmission RPM
            PostTransmissionPower = (self.Vehicle.RollingPower() + self.Vehicle.AeroPower() + self.Vehicle.GradePower(6)) / self.Vehicle.DifferentialEfficiency
            PostTransmissionRPM = self.Vehicle.PostTransmissionSpeed()
            MaxPower = 0.0
            
            if self.Transmission.IsCVT:
                RPMSToCheck = [ self.Transmission.Ratios[0] * PostTransmissionRPM ]
                if self.EngineMap:
                    RPMSToCheck.extend(list(self.EngineMap.MapRPMs))
                if self.MotorMap:
                    RPMSToCheck.extend(list(self.MotorMap.MapRPMs))
                    
                RPMSToCheck.sort()
                
                # for each gear find max power configuration
                for InputRPM in RPMSToCheck:
                    if (self.Transmission.Ratios[0] * PostTransmissionRPM >= InputRPM) and (self.Transmission.Ratios[1] * PostTransmissionRPM <= InputRPM): 
                        Index = 1
                        if (InputRPM >= self.Transmission.Ratios[0] * PostTransmissionRPM):
                            Index = 0
                        CurrentPower = 0.0
                        if self.EngineMap:
                            # if in first gear determine max power at minimum RPM
                            if((Index == 0)and(InputRPM < self.EngineMap.MapRPMs[0])):
                                CurrentPower += RotationalPower(self.EngineMap.MapRPMs[0], self.EngineMap.CalculateMaxTorque(self.EngineMap.MapRPMs[0]))
                            # if able to use this gear determin max power output
                            elif((self.EngineMap.MapRPMs[0] <= InputRPM)and(InputRPM <= self.EngineMap.MapRPMs[-1])):
                                CurrentPower += RotationalPower(InputRPM, self.EngineMap.CalculateMaxTorque(InputRPM))
                        if self.MotorMap:        
                            # If speed is below minimum then assume 1st gear
                            if((Index == 0)and(InputRPM < self.MotorMap.MapRPMs[0])):
                                # Determin the possible settings of electric motor for electrical draw
                                PossibleTorques = self.MotorMap.CalculateLoadTorque(DischargeRate10min, self.EngineMap.MapRPMs[0])
                                if(1 <= len(PossibleTorques)):
                                    CurrentPower += RotationalPower(InputRPM, max(PossibleTorques))
                                else:
                                    if(DischargeRate10min > self.MotorMap.CalculateEfficiency(InputRPM, self.MotorMap.CalculateMaxTorque(InputRPM))):
                                        CurrentPower += RotationalPower(InputRPM, self.MotorMap.CalculateMaxTorque(InputRPM))
                            elif((self.MotorMap.MapRPMs[0] <= InputRPM)and(InputRPM <= self.MotorMap.MapRPMs[-1])):
                                # Determin the possible settings of electric motor for electrical draw
                                PossibleTorques = self.MotorMap.CalculateLoadTorque(DischargeRate10min, InputRPM)
                                if(1 <= len(PossibleTorques)):
                                    CurrentPower += RotationalPower(InputRPM, max(PossibleTorques))
                                else:
                                    if(DischargeRate10min > self.MotorMap.CalculateEfficiency(InputRPM, self.MotorMap.CalculateMaxTorque(InputRPM))):
                                        CurrentPower += RotationalPower(InputRPM, self.MotorMap.CalculateMaxTorque(InputRPM))
                        # If current power is greater than max power found 
                        MaxPower = max(CurrentPower, MaxPower)
                        
            else:
                # Test to see if each gear will work
                for Index in range(1,len(self.Transmission.Ratios)):
                    InputRPM = self.Transmission.Ratios[Index] * PostTransmissionRPM
                    CurrentPower = 0.0
                    if self.EngineMap:
                        # if in first gear determine max power at minimum RPM
                        if((Index == 1)and(InputRPM < self.EngineMap.MapRPMs[0])):
                            CurrentPower += RotationalPower(self.EngineMap.MapRPMs[0], self.EngineMap.CalculateMaxTorque(self.EngineMap.MapRPMs[0]))
                        # if able to use this gear determin max power output
                        elif((self.EngineMap.MapRPMs[0] <= InputRPM)and(InputRPM <= self.EngineMap.MapRPMs[-1])):
                            CurrentPower += RotationalPower(InputRPM, self.EngineMap.CalculateMaxTorque(InputRPM))
                    if self.MotorMap:        
                        # If speed is below minimum then assume 1st gear
                        if((Index == 1)and(InputRPM < self.MotorMap.MapRPMs[0])):
                            # Determin the possible settings of electric motor for electrical draw
                            PossibleTorques = self.MotorMap.CalculateLoadTorque(DischargeRate10min, self.EngineMap.MapRPMs[0])
                            if(1 <= len(PossibleTorques)):
                                CurrentPower += RotationalPower(InputRPM, max(PossibleTorques))
                            else:
                                if(DischargeRate10min > self.MotorMap.CalculateEfficiency(InputRPM, self.MotorMap.CalculateMaxTorque(InputRPM))):
                                    CurrentPower += RotationalPower(InputRPM, self.MotorMap.CalculateMaxTorque(InputRPM))
                        elif((self.MotorMap.MapRPMs[0] <= InputRPM)and(InputRPM <= self.MotorMap.MapRPMs[-1])):
                            # Determin the possible settings of electric motor for electrical draw
                            PossibleTorques = self.MotorMap.CalculateLoadTorque(DischargeRate10min, InputRPM)
                            if(1 <= len(PossibleTorques)):
                                CurrentPower += RotationalPower(InputRPM, max(PossibleTorques))
                            else:
                                if(DischargeRate10min > self.MotorMap.CalculateEfficiency(InputRPM, self.MotorMap.CalculateMaxTorque(InputRPM))):
                                    CurrentPower += RotationalPower(InputRPM, self.MotorMap.CalculateMaxTorque(InputRPM))
                    # If current power is greater than max power found 
                    MaxPower = max(CurrentPower, MaxPower)
            # Determine max power is greater than required or not
            MaxPower *= self.Transmission.Efficiency
            if(PostTransmissionPower > MaxPower):
                HighSpeed = self.Vehicle.CurrentSpeed 
            else:
                LowSpeed = self.Vehicle.CurrentSpeed 
            DeltaSpeed = (HighSpeed - LowSpeed) * 0.5
        return ConvertMPSToMPH(self.Vehicle.CurrentSpeed)



