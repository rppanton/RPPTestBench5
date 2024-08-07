#
# mysql_connector.py
#
import xml.etree.ElementTree as ET
import sys
import pymysql
from os import path

cur = None
conn = None

rds_host = None
soc = None
name = None
password = None
db_name = None

def mysql_connect():
	
	global cur
	global conn
	
	try:
		tree = ET.parse("./configuration.xml")
		root = tree.getroot()
		rds_host = root.find("rds_host").text
		soc = int(root.find("socket").text)
		name = root.find("username").text
		password = root.find("password").text
		db_name = root.find("db_name").text
	except Exception, pe:
		return None
	
	try:
		conn = pymysql.connect(rds_host, port=soc, user=name, passwd=password, db=db_name, connect_timeout=5)
	except Exception, e:
		print "ERROR:", e
		return None
		sys.exit(1)
	print "SUCCESS: DB connected"
	cur = conn.cursor()
	return conn

def mysql_disconnect():
	global cur
	global conn
	
	cur.close()
	conn.close()
	print "SUCCESS: DB disconnected"

# search for MAC with record id, returns record MAC
def search_mac_by_id(id):
	global cur
	global conn
	
	sql = "SELECT mac_address FROM passed WHERE device_id = {}".format(id)
	rec = cur.execute(sql)
	if rec == 1:
		row = cur.fetchone()
		return row[0]

# update given record. set MAC field
def update_mac_by_id(id, mac):
	global cur
	global conn
	
	sql = "UPDATE passed SET mac_address='{}' WHERE device_id={}".format(mac, id)
	rec = cur.execute(sql)
	if rec == 1:
		conn.commit()
		return True
	else:
		return False

# creates new record with serial, returns record id
def new_with_sn(sn):
	global cur
	global conn
	
	sql = "INSERT INTO passed (serial_number) VALUES ('{}')".format(sn)
	rec = cur.execute(sql)
	if rec == 1:
		conn.commit()
		sql = "SELECT device_id FROM passed WHERE serial_number = '{}'".format(sn)
		rec = cur.execute(sql)
		row = cur.fetchone()
		return row[0]
	else:
		print "Error executing:", rec
	
# creates new record with MAC, returns record id
def new_with_mac(mac): 
	global cur
	global conn
	
	# MAC is not unique, so check for existance
	exist = search_mac(mac)
	temp_sn = "newdevice{}".format(mac[-6:])
	if exist == -3:
		sql = "INSERT INTO passed (serial_number, mac_address) VALUES ('{}', '{}')".format(temp_sn, mac)
		try:
			rec = cur.execute(sql)
		except Exception, ex:
			print ex
			sys.exit(1)
		
		if rec == 1:
			conn.commit()
			sql = "SELECT device_id FROM passed WHERE mac_address = '{}'".format(mac)
			rec = cur.execute(sql)
			row = cur.fetchone()
			# print "Record #", row[0]
			return row[0]
	else:
		return -1

# search for MAC, return record id
def search_mac(mac):
	global cur
	global conn
	
	sql = "SELECT device_id FROM passed WHERE mac_address = '{}'".format(mac)
	rec = cur.execute(sql)
	if rec == 1:
		row = cur.fetchone()
		id = row[0]
		qry = "UPDATE passed SET device_status_id=2 WHERE device_id={}".format(id)
		res = cur.execute(qry)
		if res == 1:
			conn.commit()
		return id
	elif rec == 0:
		return -3
	elif rec > 1:
		return -2
	else:
		return -1
		
def search_sn(sn):
	global cur
	global conn
	
	sql = "SELECT device_id FROM passed WHERE serial_number = '{}'".format(sn)
	rec = cur.execute(sql)
	if rec == 1:
		row = cur.fetchone()
		return row[0]
	elif rec == 0:
		return -3
	elif rec > 1:
		return -2
	else:
		return -1

def update_rec(id, sn, bn, mac, hw, sw, bm, stat, ant, xt, pow, mod, user, station):
	global cur
	global conn
	
	sql = "UPDATE passed SET serial_number='{}', batch_number='{}', mac_address='{}', hardware_version='{}', software_version='{}', node_type_id={}, device_status_id={}, antenna_delay={}, crystal_trim={}, power_level={}, model='{}', user_id='{}', station_id='{}' WHERE device_id={}".format(sn, bn, mac, hw, sw, bm, stat, ant, xt, pow, mod, user, station, id)
	try:
		rec = cur.execute(sql)
	except pymysql.InternalError as e:
		code, message = e.args
		print "Code {}: {}".format(code, message)
		return message
	else:
		conn.commit()
		return rec

# create new record in 'faults' table
def fail_test_all(mac, step, user, error, station, batch):
	# update status in 'passed' table
	id = search_mac(mac)
	if id >= 0: 
		qry = "UPDATE passed SET device_status_id=5 WHERE device_id={}".format(id)
		res = cur.execute(qry)
		if res == 1:
			conn.commit()
		device_id = id
	else:
		print "MAC address not found"
		return -1
		
	# create record
	sql = "INSERT INTO faults (mac_addr, last_step, rec_id, user_id, comment, test_station, batch_id) VALUES ('{}', '{}', {}, '{}', '{}', '{}', '{}')".format(mac, step, device_id, user, error, station, batch)
	try:
		r = cur.execute(sql)
	except pymysql.InternalError as e:
		code, message = e.args
		print "Code {}: {}".format(code, message)
		return message
	else:
		conn.commit()
		return r
	
# insert or update 'faults' table
def fail_test(mac, step, user, error, station, batch):
	# update status in 'passed' table
	id = search_mac(mac)
	if id >= 0: 
		qry = "UPDATE passed SET device_status_id=5 WHERE device_id={}".format(id)
		res = cur.execute(qry)
		if res == 1:
			conn.commit()
		device_id = id
	else:
		print "MAC address not found"
		return -1
		
	# look up for existing record in 'faults'
	sql = "SELECT unit_id FROM faults WHERE mac_addr = '{}'".format(mac)
	rec = cur.execute(sql)
	unit = cur.fetchone()
	if rec == 1: # update record
		print "Updating record #{}".format(unit[0])
		sql = "UPDATE faults SET last_step='{}', rec_id={}, user_id='{}', comment='{}', test_station='{}', batch_id='{}' WHERE unit_id={}".format(step, device_id, user, error, station, batch, unit[0])
	elif rec == 0: # create record
		sql = "INSERT INTO faults (mac_addr, last_step, rec_id, user_id, comment, test_station, batch_id) VALUES ('{}', '{}', {}, '{}', '{}', '{}', '{}')".format(mac, step, device_id, user, error, station, batch)
	try:
		r = cur.execute(sql)
	except pymysql.InternalError as e:
		code, message = e.args
		print "Code {}: {}".format(code, message)
		return message
	else:
		conn.commit()
		return r
		
def get_new_mac(reg): # returs new mac by region
	global cur
	global conn
	new_mac = ""
	
	sql = "SELECT * FROM mac_current WHERE region = {}".format(reg)
	rec = cur.execute(sql)
	row = cur.fetchone()
	
	if reg == 31:
		new_mac = "BAD{:013x}".format(row[2] + 1)
		if len(new_mac) == 16:
			sql = "UPDATE mac_current SET generated = {} WHERE region = {}".format(row[2] + 1, reg)
			rec = cur.execute(sql)
			conn.commit()
			return new_mac.upper()
		else:
			return -1
	else:
		new_mac = "{}{:x}{:04x}".format(row[0], row[1], row[2] + 1)
		if len(new_mac) == 16:
			sql = "UPDATE mac_current SET generated = {} WHERE region = {}".format(row[2] + 1, reg)
			rec = cur.execute(sql)
			conn.commit()
			return new_mac.upper()
		else:
			return -1

def mac_rollback(reg):
	global cur
	global conn
	
	try:
		prew = "SELECT generated FROM mac_current WHERE region = {}".format(reg)
		rec = cur.execute(prew)
		row = cur.fetchone()
		next = "UPDATE mac_current SET generated = {} WHERE region = {}".format(row[2] - 1, reg)
		rec = cur.execute(next)
		conn.commit()
	except Exception, ex:
		print ex
		sys.exit(1)

def get_unused_mac(reg):
	global cur
	global conn

	sql = "SELECT mac_address FROM passed WHERE serial_number LIKE 'newdevice%' AND SUBSTRING(mac_address,12,1) = '{:X}'".format(reg)
	rec = cur.execute(sql)
	if rec >= 1:
		row = cur.fetchone()
		if "E4956EFFFEA" in row[0]:
			return row[0]
		else:
			return -1
	else:
		return 0
	
		
def listV7():
	global cur
	global conn

	mysql_connect()
	# nmac = get_new_mac(14)
	# new_with_mac(nmac)
	# new_with_sn("ff0e1b1833202020504d32389afa66c3")
	mysql_disconnect()

	sys.exit(0)

if __name__ == '__main__':
	listV7()