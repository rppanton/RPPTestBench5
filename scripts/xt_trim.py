##########################################################################################
# XT trim calibration. 
#
# (C)2018 Redpoint Positioning
##########################################################################################

import os, subprocess#, pylink
# from pylink import library
from pynrfjprog import API
from time import clock, sleep
from decimal import Decimal
from sys import exit

global msg

centralFreq = 3993.6
attempts = 10
#TruePeakPow = -30

def get_freq():
	prog = ""
	count = 0
	p = None
	f = None
	while count < 50:
		try:
			output = subprocess.check_output(["spectran/spectran.exe", "get", "Peak1Frequency", "Peak1Pow"], stderr=subprocess.PIPE)
		except Exception, e:
			print "Error execution: {}".format(e)
		else:
			str = output.split("\n")
			for l in str:
				if "Peak1Frequency" in l:
					f = l[l.find("=")+2:].strip()
				elif "Peak1Pow" in l:
					p = l[l.find("=")+2:].strip()
			
			if p and float(p) >= peak:
				print ""
				break
			else:
				prog = prog + "#"
				print "\r{}".format(prog),
	
	if count == 49:
		msg = "Unable to detect true peak"
		exit(msg)
	else:
		hz = Decimal(centralFreq - float(f))
		d = round(hz, 3)
		return p, f, d

while True:
	if port == None:
		msg = "Cannot access the PPS port"
		break
	else:
		if not port.isOpen():
			port.open()
			# port.readline()
	try:
		# sleep(0.3)
		port.write("REMOTE\n")
		sleep(0.5)
		port.write("OUT0\n")
		sleep(0.3)
		port.write("VSET1:8.000\n")
		sleep(0.3)
		port.write("ISET1:0.3\n")
		sleep(0.3)
		port.write("OUT1\n")
		sleep(1)
	except Exception, e:
		msg = "Unable to write to PPS serial port. {}".format(e)	
		break
	
	start_time = clock()

	print "\t*Connecting to device..."
	jlink = None
	xt = None

	try:
		jlink = API.API(desc.ChipFamily)
		
		print " * Opening DLL..."
		jlink.open()
		if jlink.is_open():
			print "DLL is open"
		else:
			msg = "Unable open DLL"
			print msg
			break
		
		print " * Connecting to emulator {}...".format(app.usnr)
		jlink.connect_to_emu_with_snr(app.usnr, jlink_speed_khz=4000)	
	except Exception, ce:
		msg = "Emulator connection error: {}".format(ce)
		
	if jlink.is_connected_to_emu():
		print "Connected to emulator"
		
		jlink.sys_reset()
		jlink.go()
		
		print " * Connecting to RTT terminal..."
		jlink.rtt_start()
		sleep(2)
		
		if jlink.rtt_is_control_block_found():
			jlink.rtt_read(0, 1024, encoding='ascii')
			print "RTT control block found"
		else:
			print "Unable to find RTT control block"
	else:
		msg = "Unable connect to emulator"
		print msg
		break
		
	try:
		jlink.rtt_write(0, "thw x\n")
		sleep(0.1)
		jlink.rtt_read(0, 1024)
		jlink.rtt_write(0, bytes("xt 70\n"))
		sleep(0.1)
		buf = jlink.rtt_read(0, 1024)
		data = buf.split('\n')
		for l in data:
			if "XTALT:" in l:
				xt_str = l[l.find(":")+2:].strip()
		print " * Starting XT value:", xt_str
		xt = int(xt_str, 16)
	except Exception, jle:
		msg = "Unable to read RTT: {}".format(jle)
		if jlink:
			jlink.close()
		break
		
	cnt = 1
	while cnt <= attempts:
		pow, freq, delta = get_freq()
		print "Attempt {}:".format(cnt)
		print "* XT:{}; Pow: {} Peak: {}; Delta={}".format(format(xt, 'x'), pow, freq, delta)
		
		if float(freq) == 0.0:
			print "* Bad reading. Skip this attempt"
			cnt += 1
		elif abs(delta) <= 0.005:
			print "* End of calibration. Final xt:", format(xt, 'x')
			msg = 0
			break
		elif delta > 0:
			if xt >= 97:
				print "* Decrease xt value"
				# check if jump is needed (delta>10kH)
				kHzdelta = int(round(abs(delta)*100))
				if kHzdelta > 1:
					xt -= kHzdelta
				else:
					xt -= 1
				cmd = "xt {}\n".format(format(xt, 'x'))
				jlink.rtt_write(0, cmd)
				sleep(0.1)
				cnt += 1
			else:
				msg = "Lower adjustment limit is reached: {}".format(xt)
				break
		else:
			if xt <= 126:
				print "* Increase xt value"
				kHzdelta = int(round(abs(delta)*100))
				if kHzdelta > 1:
					xt += kHzdelta
				else:
					xt += 1
				cmd = "xt {}\n".format(format(xt, 'x'))
				jlink.rtt_write(0, cmd)
				sleep(0.1)
				cnt += 1
			else:
				msg = "Upper adjustment limit is reached: {}".format(xt)
				break

	jlink.rtt_stop()
	jlink.disconnect_from_emu()
	jlink.close()
	port.write("VSET1:0.000\n")
	sleep(0.3)
	port.write("OUT0\n")
	sleep(0.3)
	break

if msg == 0:
	print "\nExecution time:", clock() - start_time, "seconds"


