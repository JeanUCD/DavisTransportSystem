#
#   TTP Vehicle Load Class
#
import math
from ttputils import *

class VehicleLoad:    
    def __init__(self):
        # Vehicle parameters
        self.Mass = 1200     # kg (this is just the glider mass, need to add in powertrain mass)
        self.Area = 2.67     # m^2
        self.CD = 0.295      # coefficient of drag
        self.CRR = 0.008     # coefficient of rolling resistance   
        self.TireRadius = 0.34                # m
        self.DifferentialRatio = 3.06         # gear ratio from transmission output to wheel
        self.DifferentialEfficiency = 0.99    # efficiency of differential
        self.Reset()
    
    # Helper functions
    def Reset(self):
        self.DistanceTraveled = 0.0
        self.CurrentSpeed = 0.0
        self.LastSpeed = 0.0
        self.MaximumPower = 0.0
        self.LastRollingPower = 0.0
        self.LastAeroPower = 0.0
        self.InertialEnergy = 0.0
        self.BrakingEnergy = 0.0
        self.RollingEnergy = 0.0
        self.AeroEnergy = 0.0
        
    def InertialPower(self,accel):
        return self.Mass * self.CurrentSpeed * accel
    
    def RollingPower(self):
        return self.CRR * self.Mass * self.CurrentSpeed * ConstantGravity()
    
    def AeroPower(self):
        return 0.5 * self.CD * self.Area * ConstantAirDensity() * self.CurrentSpeed**3
    
    def GradePower(self,gradepercent):
        Alpha = math.atan(gradepercent/100.0)
        return self.Mass * self.CurrentSpeed * ConstantGravity() * math.sin(Alpha)

    def MaxAcceleration(self, power):
        power *= self.DifferentialEfficiency
        power -= self.RollingPower() + self.AeroPower()
        if(self.CurrentSpeed < ConvertMPHToMPS(0.1)): # if stopped set to 0.1mph
            return power / (self.Mass * ConvertMPHToMPS(0.1))
        return power / (self.Mass * self.CurrentSpeed)
        
    def KineticEnergy(self):
        return 0.5 * self.Mass * self.CurrentSpeed**2
        
    # Speed in MPH
    def PowerRequired(self,speed, deltatime):
        TargetSpeed = ConvertMPHToMPS(speed)
        TotalPower = 0
        if(0.0 < deltatime):
            Acceleration = (TargetSpeed - self.CurrentSpeed)/deltatime
            # Calculate current step power requirements
            CurrentInertialPower = self.InertialPower(Acceleration)
            CurrentRollingPower = self.RollingPower()
            CurrentAeroPower = self.AeroPower()
            TotalPower = CurrentInertialPower + CurrentRollingPower + CurrentAeroPower

            # Integrate distance over last time step
            self.DistanceTraveled += (speed + self.LastSpeed) * 0.5 * deltatime / 3600.0

            # Ignore negative inertial power
            if(0.0 < CurrentInertialPower):
                self.InertialEnergy += CurrentInertialPower * deltatime

            # Actually have to apply brakes 
            if(0.0 > TotalPower):
                self.BrakingEnergy += -TotalPower * deltatime

            # Integrate rolling and aero energy
            self.RollingEnergy += (self.LastRollingPower + CurrentRollingPower) * 0.5 * deltatime
            self.AeroEnergy += (self.LastAeroPower + CurrentAeroPower) * 0.5 * deltatime

            self.LastRollingPower = CurrentRollingPower
            self.LastAeroPower = CurrentAeroPower
            self.CurrentSpeed = TargetSpeed
            self.LastSpeed = speed
            
            if(0.0 < TotalPower):
                return TotalPower / self.DifferentialEfficiency
            return  TotalPower * self.DifferentialEfficiency
        return 0.0
    # Calculate the speed of the transmission output
    def PostTransmissionSpeed(self):
        return (self.CurrentSpeed/(2 * math.pi * self.TireRadius)) * 60.0 * self.DifferentialRatio

