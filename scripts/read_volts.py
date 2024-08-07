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
		port.write("REMOTE\n")
		sleep(0.5)
		port.write("OUT1\n")
		sleep(2)
	
	try:
		labjack = u3.U3()
		sleep(1)
	except:
		msg = "Unable to open LabJack interface"
		break
		
	AIN0 = Decimal(labjack.getAIN(0))
	# print "Read AIN0 = {}V".format(AIN0)
	v1 = round(AIN0, 2)
	if desc.AIN0High >= v1 and desc.AIN0Low <= v1:
		print " * AIN0 is OK: {}V".format(v1)
	else:
		msg = "AIN0 voltage unacceptable: {}".format(v1)
		break
	
	AIN1 = Decimal(labjack.getAIN(1))
	# print "Read AIN1 = {}V".format(AIN1)
	v2 = round(AIN1, 2)
	if desc.AIN1High >= v2 and desc.AIN1Low <= v2:
		print " * AIN1 is OK: {}V".format(v2)
	else:
		msg = "AIN1 voltage unacceptable: {}".format(v2)
		break

	AIN2 = Decimal(labjack.getAIN(2))
	v3 = round(AIN2, 2)
	if desc.AIN2High >= v3 and desc.AIN2Low <= v3:
		print " * AIN2 is OK: {}V".format(v3)
	else:
		msg = "AIN2 voltage unacceptable: {}".format(v3)
		break
		
	msg = 0
	labjack.close()
	port.close()
	break