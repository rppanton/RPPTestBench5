##########################################################################################
# Read output voltages on GP tag board
#
# (C)2018 Redpoint Positioning
##########################################################################################

import subprocess, u3
from time import sleep
from decimal import Decimal

global msg

while True:
	if port == None:
		msg = "Cannot access the PPS port"
		break
	else:
		if not port.isOpen():
			port.open()
	
	try:
		port.write("REMOTE\n")
		sleep(0.5)
		port.write("OUT1\n")
	except Exception, pse:
		msg = "Error write to PPS: {}".format(pse)
	
	try:
		lj = u3.U3()
		lj.configIO(EIOAnalog = 31) # EIO 0-4
		# sleep(2)
	except:
		msg = "Unable to open LabJack interface"
		break
	
	sleep(2)
	EIO0 = Decimal(lj.getAIN(8))
	EIO0_volt = round(EIO0, 1)
	# print "Reading on DEC2:", EIO0_volt
	if EIO0_volt < desc.EIO0Low:
		msg = "Votlage on DEC2 regulator too low: {}. Acceptable value is {}".format(EIO0_volt, desc.EIO0Low)
		break
	elif EIO0_volt > desc.EIO0High:
		msg = "Votlage on DEC2 regulator too high: {}. Acceptable value is {}".format(EIO0_volt, desc.EIO0High)
		break
	else:
		print "Measure DEC2   voltage:", EIO0_volt, "Volts  --OK"
	
	EIO1 = Decimal(lj.getAIN(9))
	EIO1_volt = round(EIO1, 1)
	if EIO1_volt < desc.EIO1Low:
		msg = "Votlage on DEC1 regulator too low: {}. Acceptable value is {}".format(EIO1_volt, desc.EIO1Low)
		break
	elif EIO1_volt > desc.EIO1High:
		msg = "Votlage on DEC1 regulator too high: {}. Acceptable value is {}".format(EIO1_volt, desc.EIO1High)
		break
	else:
		print "Measure DEC1   voltage:", EIO1_volt, "Volts  --OK"
		
	EIO2 = Decimal(lj.getAIN(10))
	EIO2_volt = round(EIO2, 1)
	if EIO2_volt < desc.EIO2Low:
		msg = "Votlage on VDDCLK regulator too low: {}. Acceptable value is {}".format(EIO2_volt, desc.EIO2Low)
		break
	elif EIO2_volt > desc.EIO2High:
		msg = "Votlage on VDDCLK regulator too high: {}. Acceptable value is {}".format(EIO2_volt, desc.EIO2High)
		break
	else:
		print "Measure VDDCLK voltage:", EIO2_volt, "Volts  --OK"
		
	EIO3 = Decimal(lj.getAIN(11))
	EIO3_volt = round(EIO3, 1)
	if EIO3_volt < desc.EIO3Low:
		msg = "Votlage on VDDREG regulator too low: {}. Acceptable value is {}".format(EIO3_volt, desc.EIO3Low)
		break
	elif EIO3_volt > desc.EIO3High:
		msg = "Votlage on VDDREG regulator too high: {}. Acceptable value is {}".format(EIO3_volt, desc.EIO3High)
		break
	else:
		print "Measure VDDREG voltage:", EIO3_volt, "Volts  --OK"
		
	EIO4 = Decimal(lj.getAIN(12))
	EIO4_volt = round(EIO4, 1)
	if EIO4_volt < desc.EIO4Low:
		msg = "Votlage on 1V8 regulator too low: {}. Acceptable value is {}".format(EIO4_volt, desc.EIO4Low)
		break
	elif EIO4_volt > desc.EIO4High:
		msg = "Votlage on 1V8 regulator too high: {}. Acceptable value is {}".format(EIO4_volt, desc.EIO4High)
		break
	else:
		print "Measure 1V8    voltage:", EIO4_volt, "Volts  --OK"
	
	msg = 0
	lj.close()
	break