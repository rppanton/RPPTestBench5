##########################################################################################
# Programm v7 module board (any carrier)
#
# (C)2018 Redpoint Positioning
##########################################################################################

import u3, sys
from PyQt5.QtWidgets import QTableWidgetItem
from pynrfjprog import API
from intelhex import IntelHex
from time import sleep

while True:
	# print "\t* Swithing SWD to the v7 module interface"
	# try: 
		# labjack = u3.U3()
		# labjack.getFeedback(u3.DAC8(0, 0x00))
	# except:
		# msg = "Cannot create LabJack interface"
		# break

	if port == None:
		msg = "Cannot access the PPS port"
		break
	else:
		if not port.isOpen():
			port.open()
		port.write("REMOTE\n")
		sleep(0.5)
		cmdVstr = "VSET2:{}\n".format(desc.SupplyVoltage)
		port.write(cmdVstr)
		sleep(0.3)
		port.write("OUT1\n")
		sleep(2)

	nrf = None
	ih = None
	
	print "\t* Erasing host processor..."
	try: 
		labjack = u3.U3()
		labjack.getFeedback(u3.DAC8(0, 0xfe))
	except:
		msg = "Cannot create LabJack interface"
		break
	
	try:
		nrf = API.API(desc.ChipFamily)
		
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
	except Exception, ce:
		if nrf:
			nrf.close()
		msg = "Emulator connection error: {}".format(ce)
		port.close()
		labjack.close()
		break
	
	try:
		# nrf.halt()
		nrf.erase_all()
		msg = 0
	except Exception, pe:
		msg = "Emulator error: {}".format(pe)
		port.close()
		labjack.close()
		break
	finally:
		nrf.disconnect_from_emu()
		nrf.close()
	
	
	print "\t* Swithing SWD to the v7 module interface"
	try: 
		labjack = u3.U3()
		labjack.getFeedback(u3.DAC8(0, 0x00))
	except:
		msg = "Cannot create LabJack interface"
		break
	
	try:
		nrf = API.API(desc.ChipFamily)
		
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
	except Exception, ce:
		msg = "Emulator connection error: {}".format(ce)
		break
		
	try:
		ih = IntelHex()
		file = app.test_file.currentText()
		print "\t\t* Loading file:", file
		if file.endswith(".hex"):
			ih.fromfile("firmware/" + file, format="hex")
		else:
			ih.loadbin("firmware/" + file, offset=0x0)

		for segment in ih.segments():
			seg = segment[0]
			while seg <= segment[1]+0x2000:
				nrf.erase_page(seg)
				seg = seg + 0x1000
		nrf.sys_reset()
		
		for segment in ih.segments():
			binarray = ih.tobinarray(start=segment[0], size=segment[1]-segment[0])
			print " * Writing segment at address {}. Stop address: {}".format(hex(segment[0]), hex(segment[1]))
			nrf.write(segment[0], binarray, True)
			content = nrf.read(segment[0], segment[1]-segment[0])
			if not binarray.tolist() == content:
				msg = "Segment data mismatch starting at address: {}, end address: {}".format(hex(segment[0]), hex(segment[1]))
				break
			else:
				print "Programmed successfully"
				fw = file[:file.find("_")]
				app.param_box.setItem(4, 1, QTableWidgetItem(fw))
				msg = 0
		nrf.sys_reset()
		nrf.go()
	except Exception, pe:
		msg = "Emulator error: {}".format(pe)
	finally:
		nrf.disconnect_from_emu()
		nrf.close()
		port.close()
		labjack.close()
		break
	break		
		
