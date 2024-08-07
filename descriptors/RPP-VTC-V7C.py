# descriptor file for v7 VMT-C boards

BitMask = "11001100"
Platform = "7.0"
RadioNodeLowCurrent = 0.010
RadioNodeHighCurrent = 0.030
NewImageLowCurrent = 0.010
NewImageHighCurrent = 0.30
AIN0Low = 4.8   # 5V0 power real
AIN0High = 5.35 # 
AIN1Low = 2.6  # 3V3 main power rail
AIN1High = 3.6
AIN2Low = 0  # floating
AIN2High = 2.00 # 

ALM2Low = 1.5  # alarm out pin
ALM2High = 1.75 # with low-pass filter
ALM3Low = 9.9  # alarm power out pin
ALM3High = 12.0 # 24/2 - (some drop on connections)

SupplyVoltage = 24.0
MaxCurrent = 0.3

ChipFamily = "NRF52"
HostFamily = "NRF52840_xxAA"
Radio = "DW1000"
IMU = "lsm6dsm"
BT = "nRF52832"
PreasureSensor = "BMP388"
FuelGauge = None
Charger = None
CAN = "MCP2515"
CBID = "bece" #rev.C