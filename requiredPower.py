"""
requiredPower.py
Looks in aces.vromfs.bin_u for a plane's flight model and uses the information to calculate the required power at different speeds

Changes from last version
Calculates fuel load options and prompts the user for which should be used
Is able to deal with list rather than dict under "bullet" in weapons (ex. cannonmgffm)


Issues with this version
Assumes radiator is closed always
  Ask user how open the radiator should be
The model will be inaccurate outside of region of linaer corelation between CL and AoA
"""

import math
import json

FM_PATH = "aces.vromfs.bin_u/gamedata/flightmodels/fm/"
ROM_FILE_PATH = "aces.vromfs.bin_u/"
FM_LOCATION = "gamedata/flightmodels/"
OUTPUT_FILE = "requiredPower.csv"
PILOT_MASS = 90
GRAVITATIONAL_ACCELERATION = 9.81
STANDARD_AIR_DENSITY = 1.225
DEGREES_TO_RADIANS = math.pi / 180
WATTS_PER_HORSEPOWER = 745.7
WING_PIECES_1 = ["WingLeftIn", "WingLeftMid", "WingLeftOut", "WingRightIn", "WingRightMid", "WingRightOut"]
WING_PIECES_2 = ["LeftIn", "LeftMid", "LeftOut", "RightIn", "RightMid", "RightOut"]
MIN_FUEL_PROPORTION = 0.3
FUEL_LOADS = [20, 30, 45, 60]

fmFormat = 1 #There are two formats for where some coefficients are stored

mass = 0
wingArea = 0
wingSpan = 0
cL0 = 0
cLvsAoACoefficient = 0
cDMin = 0
oswaldEfficiency = 0

#Converts a list of dictionaries to a single dictionary (Useful for some of the files being imported)
def listToDict(listToConvert):
    dictResult = dict()
    #If already a dictionary, no need to convert
    if type(listToConvert) is dict:
        return listToConvert
    #Go through each individual dictionary
    for element in listToConvert:
        if type(element) is dict:
            for key in element.keys():
                #If the key has not already been used, add the element
                if key not in dictResult.keys():
                    dictResult[key] = element[key]
    #Return the dictionary
    return dictResult

#Converts a dictionary to a list of dictionaries (Useful for some of the files being imported to put them in a format consistent with other files of the same type)
def dictToList(dictToConvert):
    listResult = []
    #If already a list, no need to convert
    if type(dictToConvert) is list:
        return dictToConvert
    #Go through the elements in the dictionary and add them to the lsit
    for key in dictToConvert.keys():
        listResult.append(dict())
        listResult[len(listResult) - 1][key] = dictToConvert[key]
    #Return the list
    return listResult

#Searches through a list of dictionaries for the first one with the given key and returns the value associated with that key
def searchList(key, listToSearch):
    for element in listToSearch:
        if type(element) is dict and key in element.keys():
            return element[key]
    #If nothing is found, return null
    return None

#Given a gun file, find all the ammo belts
def findBelts(weapon):
    weaponList = dictToList(weapon)
    #Store the names of all belts
    belts = ["default"]
    #Search for ammo belts
    for element in weaponList:
        if type(element) is dict:
            for key in element.keys():
                if type(element[key]) is list and len(element[key]) > 0 and type(element[key][0]) is dict and "bullet" in element[key][0].keys():
                    belts.append(key)
    #Return
    return belts

#Return the mass of ammo given the "commonWeapons" list
def ammoMass(commonWeapons):
    #Store the ammo type for each type of gun
    guns = dict()
    for element in commonWeapons:
        if type(element) is dict and "Weapon" in element.keys():
            #Sometimes the weapon is in list of dictionaries form and must be fixed (ex. F4F-4)
            weapon = listToDict(element["Weapon"])
            #If the weapon type is already noted, add to its ammo count
            if weapon["blk"] in guns.keys():
                guns[weapon["blk"]] += weapon["bullets"]
            #Otherwise add the weapon type and it's ammo count
            else:
                guns[weapon["blk"]] = weapon["bullets"]
    #Find the ammo mass for each type of gun
    mass = 0
    for gunFile in guns.keys():
        #Read the waepon file
        weapon = []
        try:
            weapon = json.loads(open(ROM_FILE_PATH + gunFile + "x", "r").read())
        except Exception as e:
            print("Could not access weapon file " + str(e))
            exit()
        #Get the ammo belt types
        belts = findBelts(weapon)
        #Ask the user for the belt type
        print("What belt is being used for {}".format(gunFile[gunFile.rfind("/") + 1: gunFile.rfind(".")]))
        for i in range(len(belts)):
            print("{}: {}".format(i, belts[i]))
        index = -1
        while index < 0 or index >= len(belts):
            index = int(input("Give the number next to the desired belt: "))
        #Get the list containing the ammo belt information
        belt = []
        #For the default belt, ammo information is stroed in the main list
        if belts[index] == "default":
            belt = weapon
        else:
            belt = searchList(belts[index], weapon)
        belt = dictToList(belt)
        #Get the mass of each bullet in the belt
        ammoMass = []
        for element in belt:
            if type(element) is dict and "bullet" in element.keys():
                ammoMass.append(listToDict(element["bullet"])["mass"])
        #If the number of rounds in a gun is not a multiple of the number of rounds in a belt, the average mass of a round multiplied by the number of rounds will not be the mass of all ammo in the plane (but will only be off by a very small amount), may want to change code to account for this in the future
        #Calculate the average mass of a round in the belt
        averageMass = 0
        for roundMass in ammoMass:
            averageMass += roundMass
        averageMass /= len(ammoMass)
        #Add to the total ammo mass
        mass += averageMass * guns[gunFile]
    #Return
    return mass

#Find all fuel loads and return the mass of the user selected load
def fuelMass(flightModel):
    mass = 0
    maxFuel = flightModel["Mass"]["MaxFuelMass0"]
    #Find how quickly the engine consumes fuel (kg/min)
    if "EngineType0" in flightModel.keys():
        consumptionRate = flightModel["EngineType0"]["Main"]["FuelConsumptionOnFullThr"] * flightModel["EngineType0"]["Main"]["Power"] / 60
    else:
        consumptionRate = flightModel["Engine0"]["Main"]["FuelConsumptionOnFullThr"] * flightModel["Engine0"]["Main"]["Power"] / 60
    #Create a list of the fuel loads by the time the fuel will last (approx)
    fuelLoadTimes = [maxFuel * MIN_FUEL_PROPORTION / consumptionRate]
    for load in FUEL_LOADS:
        if load > fuelLoadTimes[0] and load < maxFuel / consumptionRate:
            fuelLoadTimes.append(load)
    fuelLoadTimes.append(maxFuel / consumptionRate)
    #Ask the user for the fuel load
    print("What fuel load is being used?")
    for i in range(len(fuelLoadTimes)):
        print("{}: {}".format(i, int(fuelLoadTimes[i])))
    index = -1
    while index < 0 or index >= len(fuelLoadTimes):
        index = int(input("Give the number next to the desired fuel load: "))
    #Convert time to mass
    mass = fuelLoadTimes[index] * consumptionRate
    print("Fuel mass {}".format(mass)) #temp
    return mass

plane = input("Give the plane name as it appears in the flight model file: ")
#Get the flight model data
"""
flightModel = dict()
try:
    flightModel = json.loads(open(FM_PATH + plane + ".blkx", "r").read())
except Exception as e:
    print("Could not access flight model file " + str(e))
    exit()
"""

#Get the flight model of the plane
planeModel = []
try:
    planeModel = json.loads(open(ROM_FILE_PATH + FM_LOCATION + plane + ".blkx", "r").read())
except Exception as e:
    print("Could not access plane model file " + str(e))
    exit()
#Get the flight model file
planeModel = dictToList(planeModel)
flightModelFile = searchList("fmFile", planeModel)
#If there was no "fmFile" element, the flightmodel file should have the same name as the plane model file
if flightModelFile == None:
    flightModelFile = "fm/" + plane + ".blk"
flightModel = dict()
try:
    flightModel = json.loads(open(ROM_FILE_PATH + FM_LOCATION + flightModelFile + "x", "r").read())
except Exception as e:
    print("Could not access flight model file " + str(e))
    exit()
flightModel = listToDict(flightModel)

#Detect the flight model format
if "Areas" not in flightModel.keys():
    fmFormat = 2

#Get the mass of the plane
mass = 0
#Get mass from flight model
mass += flightModel["Mass"]["EmptyMass"]
mass += fuelMass(flightModel)
mass += flightModel["Mass"]["MaxNitro"]
mass += flightModel["Mass"]["OilMass"]
mass += PILOT_MASS
#Get the ammo mass
mass += ammoMass(searchList("commonWeapons", planeModel))

#Get the necessary flight model characteristics
#Wing area
if fmFormat == 1:
    for piece in WING_PIECES_1:
        wingArea += flightModel["Areas"][piece]
else:
    for piece in WING_PIECES_2:
        wingArea += flightModel["Aerodynamics"]["WingPlane"]["Areas"][piece]

#Wing span
if fmFormat == 1:
    wingSpan = flightModel["Wingspan"]
else:
    wingSpan = flightModel["Aerodynamics"]["WingPlane"]["Span"]
    
#CL0
if fmFormat == 1:
    cL0 = flightModel["Aerodynamics"]["NoFlaps"]["Cl0"]
else:
    cL0 = flightModel["Aerodynamics"]["WingPlane"]["Polar"]["NoFlaps"]["Cl0"]
    
#Change in CL over change in AoA (linear region)
if fmFormat == 1:
    cLvsAoACoefficient = flightModel["Aerodynamics"]["lineClCoeff"]
else:
    cLvsAoACoefficient = flightModel["Aerodynamics"]["WingPlane"]["Polar"]["lineClCoeff"]
    
#CDMin
if fmFormat == 1:
    cDMin = flightModel["Aerodynamics"]["NoFlaps"]["CdMin"] #Wing CD
    cDMin += flightModel["Aerodynamics"]["Fuselage"]["CdMin"] #Fuselage CD
    cDMin += flightModel["Aerodynamics"]["Stab"]["CdMin"] * flightModel["Areas"]["Stabilizer"] / wingArea #Horizontal stabilizer CD normalized to wing area
    cDMin += flightModel["Aerodynamics"]["Fin"]["CdMin"] * flightModel["Areas"]["Keel"] / wingArea #Vertical stabilizer CD normalized to wing area
    if "GearCentralCd" in flightModel["Aerodynamics"].keys():
        cDMin += flightModel["Aerodynamics"]["GearCentralCd"] #Central gear leg CD (Should this be included?) (Sometimes does not exist in fm files)
    #if "OilRadiatorCd" in flightModel["Aerodynamics"].keys():
        #cDMin += flightModel["Aerodynamics"]["OilRadiatorCd"] #Oil radiator CD (Sometimes does not exist in fm files) (May be closed)
    #cDMin += flightModel["Aerodynamics"]["RadiatorCd"] #Radiator CD (Radiator may be open or closed)
else:
    cDMin = flightModel["Aerodynamics"]["WingPlane"]["Polar"]["NoFlaps"]["CdMin"] #Wing CD
    cDMin += flightModel["Aerodynamics"]["FuselagePlane"]["Polar"]["CdMin"] * flightModel["Aerodynamics"]["FuselagePlane"]["Areas"]["Main"] / wingArea #Fuselage CD normalized to wing area
    cDMin += flightModel["Aerodynamics"]["HorStabPlane"]["Polar"]["CdMin"] * flightModel["Aerodynamics"]["HorStabPlane"]["Areas"]["Main"] / wingArea #Horizontal stabilizer CD normalized to wing area
    cDMin += flightModel["Aerodynamics"]["VerStabPlane"]["Polar"]["CdMin"] * flightModel["Aerodynamics"]["VerStabPlane"]["Areas"]["Main"] / wingArea #Vertical stabilizer CD normalized to wing area
    if "GearCentralCd" in flightModel["Aerodynamics"].keys():
        cDMin += flightModel["Aerodynamics"]["GearCentralCd"] #Central gear leg CD (Should this be included?) (Sometimes does not exist in fm files)
        
#Oswald Efficiency
if fmFormat == 1:
    oswaldEfficiency = flightModel["Aerodynamics"]["OswaldsEfficiencyNumber"]
else:
    oswaldEfficiency = flightModel["Aerodynamics"]["WingPlane"]["Polar"]["OswaldsEfficiencyNumber"]

print("m, area, span, CL0, CLvsAoA, CDMin, e")
print("{}, {}, {}, {}, {}, {}, {}".format(mass, wingArea, wingSpan, cL0, cLvsAoACoefficient, cDMin, oswaldEfficiency))

#Get the velocity test points
vMin = int(input("Minimum velocity: "))
vMax = int(input("Maximum velocity: "))
vStep = int(input("Velocity step size: "))
#Open an output file
outputFile = open(OUTPUT_FILE, "w")
outputFile.write("Velocity, Angle of attack, Lift, Drag, Thrust, Power\n")
#Print a legend for the data about to be produced
#print("Velocity, Angle of attack, Lift, Drag, Thrust, Power")
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
    #print("{}, {}, {}, {}, {}, {}".format(velocity * 3.6, angleOfAttack, lift, drag, thrust, power))
    outputFile.write("{}, {}, {}, {}, {}, {}\n".format(velocity * 3.6, angleOfAttack, lift, drag, thrust, power))

#Close the file
outputFile.close()
        
        
