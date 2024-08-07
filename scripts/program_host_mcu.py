##########################################################################################
# Program host MCU on carrier boards
#
# (C)2020 Redpoint Positioning
##########################################################################################

import u3, pylink
from intelhex import IntelHex
from time import sleep

while True:
	print "\t* Switching SWD to the host MCU interface"
	try: 
		labjack = u3.U3()
		labjack.getFeedback(u3.DAC8(0, 0xfe)) # high for a host
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
		port.write("REMOTE\n")
		sleep(0.5)
		port.write("OUT1\n")
		sleep(1)

	jlink = None

	try:
		jlink = pylink.JLink()
		print " * Emulator found: {}".format(app.usnr)
		jlink.open(app.usnr)
		if jlink.opened():
			print " * Emulator interface is opened"
			jlink.set_tif(1)
			print " * MCU found: {}".format(desc.HostFamily)
			jlink.connect(desc.HostFamily, 4000, False)
			print " * Connected to:", jlink.core_name()
		else:
			msg = "Unable to open JLink interface"
			break
	except Exception, jle:
		msg = "Unable to find connected JLink: {}".format(jle)
		jlink.close()
		break
	
	try:
		print " * Feedback voltage:", jlink.hardware_status.VTarget, "mV"
		jlink.reset()
		jlink.erase()
		print " * System halted:", jlink.halted()
		jlink.reset()
		filename = app.softdev_file.currentText()
		
		if app.boot_file.currentText() == "":
			print "No bootloader image detected"
		else:
			print "\t* Load bootloader for {}: {}".format(desc.HostFamily, filename)
			file = "firmware/" + app.boot_file.currentText()
			addr = IntelHex(file).start_addr['CS']
			res = jlink.flash_file(file, addr)
			jlink.reset()
			rs = jlink.restart()
			if res >= 0 and rs:
				print " * Host MCU bootloader programmed successful"
				msg = 0
			else:
				msg = "Error loading a file"
				break
		
		print "\t* Load file for {}: {}".format(desc.HostFamily, filename)
		file = "firmware/" + filename
		addr = IntelHex(file).start_addr['CS']
		res = jlink.flash_file(file, addr)#, 0x0)
		jlink.reset()
		rs = jlink.restart()
		if res >= 0 and rs:
			print " * Host MCU application programmed successful"
			msg = 0
		else:
			msg = "Error loading a file"
			break
	except Exception, ex:
		msg = "ERROR programing host MCU: {}".format(ex)
		break
	finally:
		jlink.restart()
		jlink.close()
		
		port.write("OUT0\n")
		sleep(0.5)
		port.close()
	break		
		
