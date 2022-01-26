"""
requiredPower_01.py
Looks in aces.vromfs.bin_u for a plane's flight model and uses the information to calculate the required power at different speeds

Issues with this version
The user must calculate the mass of the aircraft and submit it to the program
  Must read plane model file to get location of flight model and weapons as well as ammo count to add to mass
Assumes radiator is closed always
"""

import math
import json

FM_PATH = "aces.vromfs.bin_u/gamedata/flightmodels/fm/"
PILOT_MASS = 90
GRAVITATIONAL_ACCELERATION = 9.81
STANDARD_AIR_DENSITY = 1.225
DEGREES_TO_RADIANS = math.pi / 180
WATTS_PER_HORSEPOWER = 745.7
WING_PIECES = ["WingLeftIn", "WingLeftMid", "WingLeftOut", "WingRightIn", "WingRightMid", "WingRightOut"]

mass = 0
wingArea = 0
wingSpan = 0
cL0 = 0
cLvsAoACoefficient = 0
cDMin = 0
oswaldEfficiency = 0

plane = input("Give the plane name as it appears in the flight model file: ")
#Get the flight model data
flightModel = dict()
try:
    flightModel = json.loads(open(FM_PATH + plane + ".blkx", "r").read())
except Exception as e:
    print("Could not access flight model file " + str(e))
    exit()

#Get the mass of the plane
mass = int(input("Give mass: ")) #temp

#Get the necessary flight model characteristics
#Wing area
for piece in WING_PIECES:
    wingArea += flightModel["Areas"][piece]
print("Wing Area: {}".format(wingArea)) #temp
#Wing span
wingSpan = flightModel["Wingspan"]
#CL0
cL0 = flightModel["Aerodynamics"]["NoFlaps"]["Cl0"]
#Change in CL over change in AoA (linear region)
cLvsAoACoefficient = flightModel["Aerodynamics"]["lineClCoeff"]
#CDMin
cDMin = flightModel["Aerodynamics"]["NoFlaps"]["CdMin"] #Wing CD
cDMin += flightModel["Aerodynamics"]["Fuselage"]["CdMin"] #Fuselage CD
cDMin += flightModel["Aerodynamics"]["Stab"]["CdMin"] * flightModel["Areas"]["Stabilizer"] / wingArea #Horizontal stabilizer CD normalized to wing area
cDMin += flightModel["Aerodynamics"]["Fin"]["CdMin"] * flightModel["Areas"]["Keel"] / wingArea #Vertical stabilizer CD normalized to wing area
cDMin += flightModel["Aerodynamics"]["GearCentralCd"] #Central gear leg CD (Should this be included?)
cDMin += flightModel["Aerodynamics"]["OilRadiatorCd"] #Oil radiator CD
#cDMin += flightModel["Aerodynamics"]["RadiatorCd"] #Radiator CD (Radiator may be open or closed)
#Oswald Efficiency
oswaldEfficiency = flightModel["Aerodynamics"]["OswaldsEfficiencyNumber"]

print("m, area, span, CL0, CLvsAoA, CDMin, e")
print("{}, {}, {}, {}, {}, {}, {}".format(mass, wingArea, wingSpan, cL0, cLvsAoACoefficient, cDMin, oswaldEfficiency))

#Get the velocity test points
vMin = int(input("Minimum velocity: "))
vMax = int(input("Maximum velocity: "))
vStep = int(input("Velocity step size: "))
#Print a legend for the data about to be produced
print("Velocity, Angle of attack, Lift, Drag, Thrust, Power")
for velocity in range(vMin, vMax + vStep, vStep):
    #Change velocity from km/h to m/s
    velocity /= 3.6
    #Do 20 itterations of the following to approach the result
    #Start asuming sin(AoA) = 0 (Should be very close to true
    lift = mass * GRAVITATIONAL_ACCELERATION
    angleOfAttack = 0
    drag = 0
    thrust = 0
    for i in range(20):
        #Solve for AoA using the current lift (Will be in degrees)
        angleOfAttack = ((2 * lift) / (STANDARD_AIR_DENSITY * velocity * velocity * wingArea) - cL0) / cLvsAoACoefficient
        #Solve for drag using the AoA
        drag = ((cLvsAoACoefficient * angleOfAttack + cL0) ** 2 / (math.pi * wingSpan *wingSpan / wingArea * oswaldEfficiency) + cDMin) / 2 * STANDARD_AIR_DENSITY * velocity * velocity * wingArea
        #Solve for thrust using the drag and AoA
        thrust = drag / math.cos(angleOfAttack * DEGREES_TO_RADIANS)
        #print("{}, {}, {}, {}, {}, {}".format(i, velocity, angleOfAttack, lift, drag, thrust)) #For debug to check that intterations converge
        #Calculate the lift for the next itteration
        lift = mass * GRAVITATIONAL_ACCELERATION - (thrust * math.sin(angleOfAttack * DEGREES_TO_RADIANS))
    #Print out the data
    power = thrust * math.cos(angleOfAttack * DEGREES_TO_RADIANS) * velocity / WATTS_PER_HORSEPOWER
    print("{}, {}, {}, {}, {}, {}".format(velocity * 3.6, angleOfAttack, lift, drag, thrust, power))
        
        
