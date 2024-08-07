##########################################################################################
# Program NRF51 chip
# Single file with softdevice and application
#
# (C)2019 Redpoint Positioning
##########################################################################################

from time import sleep
from pynrfjprog import API
from intelhex import IntelHex
import u3

global msg

while True: # one-only-loop (break)
	print "\t* Swithing SWD to NRF interface"
	try: 
		labjack = u3.U3()
		labjack.getFeedback(u3.DAC8(0, 0xfe))
		labjack.close()
	except:
		msg = "Cannot create LabJack interface"
		break
	
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
		sleep(0.5)
	except Exception, pse:
		msg = "Error write to PPS: {}".format(pse)
		break
	
	nrf = None
	ih = None
	
	try:
		device = API.DeviceFamily(desc.HostFamilyEnum)
		nrf = API.API(device)
	except Exception, ce:
		msg = "Connection error: {}".format(ce)
		break
		
	try:
		print " * Opening DLL..."
		nrf.open()
		if nrf.is_open():
			print "DLL is open"
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
		
		ih = IntelHex()
		filename = app.softdev_file.currentText()
		print "\t\t* Loading file:", filename
		ih.fromfile("firmware/" + filename, format="hex")
		nrf.erase_all()
		for segment in ih.segments():
			binarray = ih.tobinarray(start=segment[0], size=segment[1]-segment[0])
			print " * Writing segment at address {}. Stop address: {}".format(hex(segment[0]), hex(segment[1]))
			nrf.write(segment[0], binarray, True)
			content = nrf.read(segment[0], segment[1]-segment[0])
			if not binarray.tolist() == content:
				msg = "Segment data mismatch starting at address: {}, end address: {}".format(hex(segment[0]), hex(segment[1]))
				break
			else:
				msg = 0
		nrf.sys_reset()
		nrf.go()
	except Exception, pe:
		msg = "Emulator error: {}".format(pe)
		break
	finally:
		if msg == 0:
			print " * Programmed successfull"
		if nrf:
			nrf.disconnect_from_emu()
			nrf.close()
		port.write("OUT0\n")
		sleep(0.3)
		port.close()
		break