##########################################################################################
# Switch the board to alarm state
# Read alarm_out and alarm_power_out pins voltages
#
# (C)2020 Redpoint Positioning
##########################################################################################

from time import sleep
from pynrfjprog import API
from decimal import Decimal
import u3

global msg

while True:
	msg = 0
	print " * Creating LabJack interface..."
	try: 
		labjack = u3.U3()
		labjack.getFeedback(u3.DAC8(0, 0xfe))
	except Exception, le:
		msg = "Cannot create LabJack interface: {}".format(le)
		break
	else:
		print "LabJack is connected"
	
	print " * Opening J-Link interface..."
	try:
		nrf = API.API(desc.ChipFamily)
		
		print " * Opening DLL..."
		nrf.open()
		if nrf.is_open():
			print "DLL is connected"
		else:
			msg = "Unable open DLL"
			print msg
			break
		
		print " * Connecting to emulator {}...".format(app.usnr)
		nrf.connect_to_emu_with_snr(app.usnr, jlink_speed_khz=4000)
		if nrf.is_connected_to_emu():
			print "Connected to emulator"
		else:
			msg = "Unable connect to emulator"
			print msg
			break
	except Exception, jce:
		msg = "J-Link connection error: {}".format(jce)
		labjack.close()
		nrf.close()
		break
	
	try:	
		print "\t* Opening RTT interface..."
		nrf.rtt_start()
		sleep(2)
		if not nrf.rtt_is_control_block_found():
			msg = "Unable to find RTT control block"
			break
		else:
			nrf.rtt_write(0, "almpin on\n")
	except Exception, et:
		msg = "Error connection RTT: {}".format(et)
		break
		
	sleep(1) # wait for state

	try:
		AIN2 = Decimal(labjack.getAIN(2))
		v2 = round(AIN2, 2)
		if desc.ALM2High >= v2 and desc.ALM2Low <= v2:
			print " * AIN2 is OK: {}V".format(v2)
			msg = 0
		else:
			msg = "AIN2 voltage unacceptable: {}".format(v2)
			break
			
		AIN3 = Decimal(labjack.getAIN(3))
		v3 = round(AIN3, 2)
		if desc.ALM3High >= v3 and desc.ALM3Low <= v3:
			print " * AIN3 is OK: {}V".format(v3)
			msg = 0
		else:
			msg = "AIN3 voltage unacceptable: {}".format(v3)
			break
	except Exception, rv:
		msg = "Unable to read voltage: {}".format(rv)
		break
	finally:
		nrf.close()
		labjack.close()
		break

