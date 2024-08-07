
import u3
from time import sleep
from pynrfjprog import API

global msg
# 0-7    FIO0-FIO7 (0-3 unavailable on U3-HV)
# 8-15   EIO0-EIO7
# 16-19  CIO0-CIO3
pins = [16, 15, 14, 13, 19, 18, 17]

mask = [0,1,0,1,0]
result = []
nrf = None
	
while True:	
	print "\t* Starting LabJack..."
	try:
		lj = u3.U3()
	except:
		lj = None
		msg = "Error connecting LabJack"
		break
	else:
		print "LabJack connected"
	
	print "\t* Opening J-Link interface..."
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
		lj.close()
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
			# clear buffer
			nrf.rtt_read(0, 1024)
		
		print ""
		for i, pin in enumerate(pins):
			print "\t* Testing GPIO{}".format(i)
			del result[:]
			# result.append(lj.getFeedback(u3.BitStateRead(pin))[0])
			nrf.rtt_write(0, "gpio m {} do\n".format(i))
			sleep(0.1)
			nrf.rtt_write(0, "gpio w {} 0\n".format(i))
			sleep(0.1)
			out = nrf.rtt_read(0, 1024).strip()
			result.append(lj.getFeedback(u3.BitStateRead(pin))[0])
			nrf.rtt_write(0, "gpio w {} 1\n".format(i))
			sleep(0.1)
			out = nrf.rtt_read(0, 1024).strip()
			result.append(lj.getFeedback(u3.BitStateRead(pin))[0])
			nrf.rtt_write(0, "gpio w {} 0\n".format(i))
			sleep(0.1)
			out = nrf.rtt_read(0, 1024).strip()
			result.append(lj.getFeedback(u3.BitStateRead(pin))[0])
			nrf.rtt_write(0, "gpio w {} 1\n".format(i))
			sleep(0.1)
			out = nrf.rtt_read(0, 1024).strip()
			result.append(lj.getFeedback(u3.BitStateRead(pin))[0])
			nrf.rtt_write(0, "gpio w {} 0\n".format(i))
			sleep(0.1)
			out = nrf.rtt_read(0, 1024).strip()
			result.append(lj.getFeedback(u3.BitStateRead(pin))[0])
			print mask
			print result
			if result == mask:
				print "Passed"
				msg = 0
				# sleep(0.3)
			else:
				print "Failed"
				msg = "Failed test on GPIO{}".format(i)
				break
		# msg = 0
		break
	except Exception, et:
		msg = "Error connectin RTT: {}".format(et)
		break
	finally:
		nrf.rtt_stop()
		nrf.disconnect_from_emu()
		nrf.close()
		lj.close()

