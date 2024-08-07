##########################################################################################
# XT trim calibration for v6 family. 
#
# (C)2019 Redpoint Positioning
##########################################################################################

import subprocess, pylink
from time import clock, sleep
from decimal import Decimal
from sys import exit

global msg

centralFreq = 3993.68
attempts = 10

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
		jlink = pylink.JLink()
		jlink.open(app.usnr)
		if jlink.opened():
			print " * Emulator interface is opened"
			jlink.set_tif(1)
			jlink.connect(desc.ChipFamily, 4000, False)
			print " * Connected to core:", jlink.core_name()
			jlink.restart()
		else:
			print "Unable to open JLink interface"
			exit(1)
		print "\t*Connecting to RTT terminal..."	
		jlink.rtt_start()
		sleep(1)
		num_up = jlink.rtt_get_num_up_buffers()
		num_down = jlink.rtt_get_num_down_buffers()
		print " * RTT started, {} up bufs, {} down bufs.".format(num_up, num_down)
		jlink.rtt_write(0, bytes("thw x\n"))
		sleep(0.1)
		jlink.rtt_read(0, 1024)
		jlink.rtt_write(0, bytes("xt 70\n"))
		sleep(0.1)
		buf = jlink.rtt_read(0, 1024)
		text = "".join(map(chr, buf))
		# print text
		xt_str = text[text.find("XTALT:")+7:].strip()
		print " * Starting XT value:", xt_str
		xt = int(xt_str, 16)
	except Exception, jle:
		msg = "Unable to find connected JLink: {}".format(jle)
		if jlink:
			jlink.close()
		break
		
	cnt = 1
	while cnt <= attempts:
		pow, freq, delta = get_freq()
		print "Attempt {}:".format(cnt)
		print " * XT:{}; Pow: {} Peak: {}; Delta={}".format(format(xt, 'x'), pow, freq, delta)
		
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
				jlink.rtt_write(0, bytes(cmd))
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
				jlink.rtt_write(0, bytes(cmd))
				sleep(0.1)
				cnt += 1
			else:
				msg = "Upper adjustment limit is reached: {}".format(xt)
				break

	jlink.rtt_stop()
	jlink.close()
	port.write("VSET1:0.000\n")
	sleep(0.3)
	port.write("OUT0\n")
	sleep(0.3)
	# port.write("OUT1\n")
	# sleep(0.3)
	break

if msg == 0:
	print "\nExecution time:", clock() - start_time, "seconds"


