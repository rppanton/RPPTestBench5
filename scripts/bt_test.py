##########################################################################################
# Bluetooth module test for v7 based boards
# 
#
# (C)2018 Redpoint Positioning
##########################################################################################

from time import sleep
from sys import exit
from pynrfjprog import MultiAPI

global msg

PER_PACKETS_NUMB = 50
PER_PACKETS_SIZE = 128

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
		uut = MultiAPI.MultiAPI(desc.ChipFamily)
		gn = MultiAPI.MultiAPI(desc.ChipFamily)
		
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
		if gn.is_connected_to_emu():
			gn.sys_reset()
			sleep(0.3)
			gn.go()
			sleep(0.3)
			print "GN is connected to emulator {}".format(app.gsnr)
	except Exception, ce:
		msg = "Error connect to emu: {}".format(ce)
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
			print "\t* Ready for BT test\n"
		else:
			msg = "MAC for GN not found"
			print " * {}: \n{}".format(msg, text)
			break	
	
	flag = True		
	cnt = 1
	
	while cnt <= 3:
		msg = 0
		rate = 0
		try:
			curr_pack = PER_PACKETS_NUMB * cnt
			print " * Sending {} packets of {} bytes to {}".format(curr_pack, PER_PACKETS_SIZE, GN_MAC)
			cmd = "bleping {} {} {}\n".format(GN_MAC, curr_pack, PER_PACKETS_SIZE)
			
			# RTT input buffer size is 16 bytes, so split into 15 bytes chunks
			split_string = lambda x, n: [x[i:i+n] for i in range(0, len(x), n)]
			parts = split_string(cmd, 15)
			
			for l in parts:
				uut.rtt_write(0, l)
				sleep(0.5) 
			
			sleep(2)
			text = uut.rtt_read(0, 1024)
			# print "For a log only:", text
			data = text.split(" ")
			for l in data:
				if "resp_n" in l:
					clr = l[:l.find('\n')]
					res_s = clr[clr.find("=")+1:].strip()
					# print "Received:", res_s, int(res_s)
					rate = int(res_s)
					
			if rate >= curr_pack - (cnt * 2):
				print "\tAttempt {} : Received {} of {} sent packets - PASS".format(cnt, rate, curr_pack)
				flag = True
				break
			else:
				print "\tAttempt {} : Received {} of {} sent packets - FAIL".format(cnt, rate, curr_pack)
				if cnt == 3:
					msg = "Failed to transmit/receive on BT channel"
					flag = False
					break
				else:
					cnt += 1
		except Exception, che:
			msg = "Error testing BT: {}".format(che)
			break		
	break

print " * Terminating connections..."
uut.terminate()
gn.terminate()

# 


# if __name__ == '__main__':
	# uut = MultiAPI.MultiAPI(desc.ChipFamily[:5])
	# gn = MultiAPI.MultiAPI(desc.ChipFamily[:5])
		
	# uut.open()
	# rtt.open()