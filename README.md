# WarThunderScripts
Scripts to get or use data from the game, War Thunder.

## telemetry.py
Gets some select telemetry data and prints it to the console
Uses the [http://localhost:8111](http://localhost:8111) site set up by the game

## requiredPower.py
Looks at flight model files and calculates required power at different speeds using the data in them, the results are put in a csv file
aces.vromfs.bin_u must be in the current directory when this is run and must contain the extracted resources from the game
- This can be extracted using the tools [here](https://github.com/kotiq/wt-tools/tree/new-format)
- Or can be downloaded from [here](https://github.com/gszabi99/War-Thunder-Datamine) as long as this is kept up to date
