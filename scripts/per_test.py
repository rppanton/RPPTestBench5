##########################################################################################
# Packet Error rate test for v7 module
# 
#
# (C)2018 Redpoint Positioning
##########################################################################################

from time import sleep
from sys import exit
from pynrfjprog import MultiAPI

global msg
UWB_CHANNELS = ['1', '2', '3', '5']#, '7']
UWB_THRESHOLD = 85 # %
PER_PACKETS_NUMB = 50# 100
PER_PACKETS_SIZE = 128

nrf = None
gn = None
uut = None
GN_MAC = None

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
		sleep(0.5)
	except Exception, e:
		msg = "Unable to write to PPS serial port. {}".format(e)		
		break
	# finally:
		# port.close()
	
	print "\t* Creating interfaces for UUT and GN"
	try:
		print " * Creating APIs..."
		uut = MultiAPI.MultiAPI(desc.ChipFamily[:5])
		gn = MultiAPI.MultiAPI(desc.ChipFamily[:5])
		
		uut.open()
		if uut.is_open():
			print "API for UUT is created"
		
		gn.open()
		if gn.is_open():
			print "API for GN is created"
	except Exception, oe:
		msg = "Error open: {}".format(oe)
		break	
		
	try:
		print " * Connecting APIs..."
		uut.connect_to_emu_with_snr(app.usnr, jlink_speed_khz=4000)
		if uut.is_connected_to_emu():
			uut.sys_reset()
			sleep(0.3)
			uut.go()
			sleep(0.3)
			print "UUT is connected to emulator {}".format(app.usnr)
			
		gn.connect_to_emu_with_snr(app.gsnr, jlink_speed_khz=4000)
		sleep(0.3)
		if gn.is_connected_to_emu():
			gn.sys_reset()
			sleep(0.3)
			gn.go()
			sleep(0.3)
			print "GN is connected to emulator {}".format(app.gsnr)
	except Exception, ce:
		msg = "Error connect to emu: {}".format(ce)
		uut.terminate()
		gn.terminate()
		break
	
	try:
		print " * Opening RTT interface..."
		uut.rtt_start()
		sleep(2)
		# if uut.rtt_is_control_block_found():
		if uut.is_rtt_started():
			print "RTT control block found for UUT"
		else:
			msg = "Control block for UUT is unreachable"
			uut.terminate()
			gn.terminate()
			break
		
		gn.rtt_start()
		sleep(2)
		# if gn.rtt_is_control_block_found():
		if uut.is_rtt_started():
			print "RTT control block found for GN"
		else:
			msg = "Control block for GN is unreachable"
			break
	except Exception, re:
		msg = "Error connect to rtt: {}".format(re)
		uut.terminate()
		gn.terminate()
		break
	else:
		# clear output buffer
		uut.rtt_read(0, 1024)
		gn.rtt_read(0, 1024)
		
		gn.rtt_write(0, "mac\n")
		sleep(0.5)
		text = gn.rtt_read(0, 1024)
		if "MAC address" in text:
			s = text.find(": ")+2
			wmac_str = text[s:s+23].strip()
			wmac = str(wmac_str).replace(':', '', 7)
			GN_MAC = wmac[-4:].lower()
		if GN_MAC:
			print "MAC addres for GN found:", GN_MAC
			msg = 0
			print "\t* Ready for PER test\n"
		else:
			msg = "MAC for GN not found"
			print " * {}: \n{}".format(msg, text)
			break
	
	flag = True
	for chan in UWB_CHANNELS:
		if not flag:
			break
		
		print "* Testing channel", chan
		uut.rtt_write(0, "chan {}\n".format(chan))
		sleep(0.3)
		uut.rtt_read(0, 1024)
		gn.rtt_write(0, "chan {}\n".format(chan))
		sleep(0.3)		
		cnt = 1
		
		while cnt <= 3:
			msg = 0
			try:
				curr_pack = PER_PACKETS_NUMB * cnt
				cmd = "ping {} {}\n".format(GN_MAC, curr_pack)
				uut.rtt_write(0, cmd)
				sleep(1.5)
				text = uut.rtt_read(0, 1024)
				data = text.split(" ")
				for l in data:
					if "resp_n" in l:
						clr = l[:l.find('\n')]
						res_s = clr[clr.find("resp_n")+7:].strip()
						rate = 100 * int(res_s) / curr_pack
						break
				if rate >= UWB_THRESHOLD:
					print "\tAttempt {} : Received {}% of {} sent packets - PASS".format(cnt, rate, curr_pack)
					flag = True
					break
				else:
					print "\tAttempt {} : Received {}% of {} sent packets - FAIL".format(cnt, rate, curr_pack)
					if cnt == 3:
						msg = "Received only {}% with {}% threshold on chan {}".format(rate, UWB_THRESHOLD, chan)
						flag = False
						break
					else:
						rate = 0
						cnt += 1
			except Exception, che:
				msg = "Error testing channel {}: {}".format(chan, che)
				break

	print " * Switching channels back to 2"
	uut.rtt_read(0, 1024)
	uut.rtt_write(0, "chan 2\n")
	sleep(0.3)
	print "UUT:", uut.rtt_read(0, 128).strip()
	uut.terminate()
	gn.rtt_read(0, 1024)
	gn.rtt_write(0, "chan 2\n")
	sleep(0.3)
	print "GN:", gn.rtt_read(0, 128).strip()
	gn.terminate()
	break

if port.isOpen():
	port.close()
