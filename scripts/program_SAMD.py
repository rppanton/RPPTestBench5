##########################################################################################
# Programm ATSAMD chip. Check current and power convertors
#
# (C)2019 Redpoint Positioning
##########################################################################################

import u3, pylink, os
from pylink import library
from decimal import Decimal
from time import sleep

global msg

while True:
	print "\t* Swithing SWD to ATSAMD interface"
	try: 
		labjack = u3.U3()
		labjack.getFeedback(u3.DAC8(0, 0x00))
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
		sleep(0.3)

	jlink = None

	try:
		jlink = pylink.JLink()
		print " * Emulator found: {}".format(app.usnr)
		jlink.open(app.usnr)
		if jlink.opened():
			print " * Emulator interface is opened"
			jlink.set_tif(1)
			print " * MCU found: {}".format(desc.ChipFamily)
			jlink.connect(desc.ChipFamily, 4000, False)
			print " * Connected to:", jlink.core_name()
		else:
			msg = "Unable to open JLink interface"
			break
	except Exception, jle:
		msg = "Unabe to find connected JLink: {}".format(jle)
		break
	
	try:
		print " * Feedback voltage:", jlink.hardware_status.VTarget, "mV"
		jlink.reset()
		print " * System halted:", jlink.halted()
		print "\t* Load SAMD file: {}".format(file)
		res = jlink.flash_file("firmware/" + file, 0x0)
		jlink.reset()
		rs = jlink.restart()
		if res >= 0 and rs:
			print " * File programmed successful"
			msg = 0
		else:
			msg = "Error loading a file"
			break
	except Exception, ex:
		msg = "ERROR programing SAMD: {}".format(ex)
		break
	finally:
		jlink.restart()
		sleep(0.3)
		jlink.close()
	
	sleep(2) # wait for a boot-up

	try:	
		port.readline()
		port.write("IOUT2?\n")
		sleep(0.3)
		
		cnt = 0
		while cnt < 3:
			current_str = port.readline().strip()
			try:
				current = float(current_str[:-1])
				print "\t* Read current: {} Amps".format(current)
			except ValueError:
				msg = "Wrong current value:" + current_str
				print msg
			
			if current < desc.NewImageLowCurrent:
				msg = "Measured current value {} is too low.\nAcceptable low limit is {} Amps".format(current, desc.NewImageLowCurrent)
				print msg
				cnt += 1
			elif current > desc.NewImageHighCurrent:
				msg = "Measured current value {} is too high.\nAcceptable high limit is {} Amps".format(current, desc.NewImageHighCurrent)
				print msg
				cnt += 1
			else:
				msg = 0
				print " * Measured current is acceptable:", current, "Amps"
				break
		
		if msg != 0:
			# print "Finished with error code:", msg
			break
		else:	
			print "\t* Read voltages on test points"
			AIN1 = Decimal(labjack.getAIN(1))
			v1 = round(AIN1, 2)
			if desc.AIN1High > v1 and desc.AIN1Low <= v1:
				print " * 3V0 voltage is OK:", v1
			else:
				msg = "3V0 voltage unacceptable: {}".format(v1)
				break
			AIN2 = Decimal(labjack.getAIN(2))
			v2 = round(AIN2, 2)
			if desc.AIN2High > v2 and desc.AIN2Low <= v2:
				print " * 1V8 voltage is OK:", v2
			else:
				msg = "1V8 voltage unacceptable: {}".format(v2)
				break
	except Exception, e:
		msg = "Error: "+e.message
		break
	finally:
		labjack.close()
		port.write("OUT0\n")
		sleep(1)
		port.write("OUT1\n")
		sleep(0.3)
		port.close()
	
	if msg == 0:
		print " * Programmed successfull"
	break

