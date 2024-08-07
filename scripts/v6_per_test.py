##########################################################################################
# Packet Error rate test for v6 platform
# 
#
# (C)2019 Redpoint Positioning
##########################################################################################

from time import sleep
import pylink

global msg
UWB_CHANNELS = ['1', '2', '3', '5']
UWB_THRESHOLD = 75 # %
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
	
	print "\t* Creating interfaces for UUT and GN"
	
	try:
		ulink = pylink.JLink()
		ulink.open(app.usnr)
		if ulink.opened():
			ulink.set_tif(1)
			ulink.connect(desc.ChipFamily, 4000, False)
			print " * UUT. Connected to core:", ulink.core_name()
			ulink.restart()
			ulink.rtt_start()
			sleep(1)
			num_up = ulink.rtt_get_num_up_buffers()
			num_down = ulink.rtt_get_num_down_buffers()
			print " * UUT. RTT started, {} up bufs, {} down bufs.".format(num_up, num_down)
			ulink.rtt_read(0, 1024)
			sleep(0.3)
		else:
			print "Unable to open UUT JLink interface"
			ulink.close()
			break
	except Exception, ue:
		msg = "Error open UUT: {}".format(ue)
		break
	
	try:
		device = "NRF52832_xxAA"
		glink = pylink.JLink()
		glink.open(app.gsnr)
		if glink.opened():
			glink.set_tif(1)
			glink.connect(device, 4000, False)#(desc.ChipFamily, 4000, False)
			print " * GN. Connected to core:", glink.core_name()
			glink.restart()
			glink.rtt_start()
			sleep(1)
			num_up = glink.rtt_get_num_up_buffers()
			num_down = glink.rtt_get_num_down_buffers()
			print " * GN. RTT started, {} up bufs, {} down bufs.".format(num_up, num_down)
			glink.rtt_read(0, 1024)
			sleep(0.3)
			glink.rtt_write(0, bytes("mac\n"))
			sleep(0.3)
			buf = glink.rtt_read(0, 1024)
			# print "RTT buffer ({} bytes):".format(len(buf))
			text = "".join(map(chr, buf)).strip()
			# print text
			s = text.find(": ")+2
			wmac_str = text[s:s+23].strip()
			wmac = str(wmac_str).replace(':', '', 7)
			GN_MAC = wmac[-4:].lower()
			print " * MAC addres for GN found:", GN_MAC
			# GN_MAC = 
		else:
			print "Unable to open GN JLink interface"
			glink.close()
			break
	except Exception, ge:
		msg = "Error open GN: {}".format(ge)
		break
	
	print "\t* Start testing channels..."
	flag = True
	for chan in UWB_CHANNELS:
		if not flag:
			break
		
		print "* Testing channel", chan
		cmd = bytes("chan {}\n".format(chan))
		ulink.rtt_write(0, cmd)
		sleep(0.3)
		ulink.rtt_read(0, 1024)
		glink.rtt_write(0, cmd)
		sleep(0.3)		
		cnt = 1
		
		while cnt <= 3:
			msg = 0
			try:
				curr_pack = PER_PACKETS_NUMB * cnt
				text = "ping {} {} {}\n".format(GN_MAC, curr_pack, PER_PACKETS_SIZE)
				long_str = lambda x, n: [x[i:i+n] for i in range(0, len(x), n)]
				cmd = long_str(text, 15) # 16 bytes chunks
				for l in cmd:
					ulink.rtt_write(0, l)
					sleep(0.5)
				
				sleep(1)
				buf = ulink.rtt_read(0, 1024)
				text = "".join(map(chr, buf))
				data = text.split(" ")
				for l in data:
					if "resp_n" in l:
						clr = l[:l.find('\n')]
						res_s = clr[clr.find("resp_n")+7:].strip()
						rate = 100 * int(res_s) / curr_pack
						
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
						cnt += 1
			except Exception, che:
				msg = "Error testing channel: {}".format(che)
				break
	break

print "\t* Swith back to chan 2 and close"
ulink.rtt_write(0, bytes("chan 2\n"))
sleep(0.3)
buf = ulink.rtt_read(0, 1024)
text = "".join(map(chr, buf))
print " *", text.strip()
ulink.rtt_stop()
ulink.close()
print " * UUT closed"
glink.rtt_stop()
glink.close()
print " * GN closed"

