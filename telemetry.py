"""
telemetry.py
Gets War Thunder telemetry form localhost:8111 and prints some to the terminal
"""

import requests

URL_STATE = 'http://localhost:8111/state'

#data points to be looked at (power, prop efficiency, IAS, TAS, altitude)
dataProfile = ["power 1, hp", "efficiency 1, %", "IAS, km/h", "TAS, km/h", "H, m"]

#show what data is being printed
for key in dataProfile:
    print(key, end=", ")
print()

while(1):
    #Get data from the game
    try:
        #Get data about the state of the plane from the site
        state_response = requests.get(URL_STATE)
        state = state_response.json()

        #if valid data is recieved
        if state["valid"]:
            #Print the requested data profile
            for key in dataProfile:
                try:
                    print(state[key], end=", ")
                except Exception as e:
                    print("Key error: {}".format(e))
            print()
            
        
        #Otherwise send a message about the invalid data
        else:
            print("No valid data recieved")

    except Exception as e:
        print(e)
    
