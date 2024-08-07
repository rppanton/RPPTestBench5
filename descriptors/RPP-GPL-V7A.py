# descripor file for v7 GPL board

BitMask = "11001100"
Platform = "7.0"
RadioNodeLowCurrent = 0.015
RadioNodeHighCurrent = 0.120
NewImageLowCurrent = 0.075
NewImageHighCurrent = 0.105
AIN0Low = 4.0   # voltage from charger
AIN0High = 4.6 # with no load
AIN1Low = 3.2  # main power rail
AIN1High = 3.4
AIN2Low = 2.5  # power source selection (high)
AIN2High = 3.3 # ~5V * 0.66 ratio
SupplyVoltage = 5.0
MaxCurrent = 0.3
ChipFamily = "NRF52"
PreasureSensor = #"BMP388"
FuelGauge = "BQ27441"
Charger = "BQ24250RGET" #"BQ24250"
CBID = "" # GPLT only!