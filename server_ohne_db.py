# Server
#
# Empfängt Daten vom Fahrrad Controller und speichert diese in einem Array
import socket, random, os, json, datetime
clear = lambda: os.system('cls')

socket_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket_receive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Gesammelte Messdaten Fahrradcontroller
fc_data  = []

# Gesammelte Messdaten Batteriecontroller
bat_data = []

class Fahrrad:
	def __init__(self, ip, mac):
		self.ip = ip
		self.mac = mac
		
		self.strecke = 0
		self.strecke_gesamt = 0
		self.geschwindigkeit = 0
		self.istLeistung = 0
		
		self.sollDrehmoment = None # 1 Byte
		self.sollLeistung   = None # 1 Byte
		
		self.reifenUmfang = 2.1
		self.u = 10
		
		self.data 	= 0
		self.pGen 	= 0
		self.T 		= 0
		self.nLm 	= 0
		
	def compute(self, data):
		# Paketformat (FC-Daten):
		# 8 Byte
		# 	Frame-No 					(1 Byte)
		#	Power W 					(1 Byte)
		# 	T: Zeit für N umdrehungen 	(2 Byte)
		#	N: Anzahl Umdrehungen 		(1 Byte)
		#	Pedalzeit halber Umlauf 	(2 Byte)
		#	Mode 						(1 Byte)
		self.data = data

		self.pGen 	= data[1] 											 # mittlere IST-Leistung in W
		self.T 		= int.from_bytes([data[2],data[3]], byteorder='big') # Zeit für eine Tretlagerumdrehung in Sekunden
		self.nLm 	= data[4] # Umdrehungen Lichtmaschine
		
		self.strecke 		 = int(self.nLm * (self.reifenUmfang / self.u))
		self.strecke_gesamt	 = self.strecke_gesamt + self.strecke
		self.geschwindigkeit = int((self.strecke / (self.T / 15625)) * 3.6)
		self.istLeistung 	 = self.pGen
		
		fc_data.append([self.pGen, self.T, self.nLm, self.strecke, self.geschwindigkeit, self.istLeistung, datetime.date.today().strftime("%B %d, %Y")])
		
		clear()
		print(fc_data)
		
def batteryUpdate(data):
	uBat  = int.from_bytes([data[1],data[2]], byteorder='big') / 1000  # mV / 1000 = V
	iGen  = int.from_bytes([data[3],data[4]], byteorder='big') / 1000  # mA / 1000 = A
	iLoad = int.from_bytes([data[5],data[6]], byteorder='big') / 1000  # mA / 1000 = A
	
	uBat_rounded  = round(uBat, 2)
	iGen_rounded  = round(iGen, 2)
	iLoad_rounded = round(iLoad, 2)
	
	# Push to bat_data
	bat_data.append([uBat, iGen, iLoad, datetime.date.today().strftime("%B %d, %Y")])
	
	clear()
	print(bat_data)
	
if __name__ == "__main__":
	fahrraeder = [
		Fahrrad("192.168.4.3", "00:00:00:00:00:00"),
		Fahrrad("192.168.4.4", "00:00:00:00:00:01"),
		Fahrrad("192.168.4.5", "00:00:00:00:00:02")
	]
	
	socket_receive.bind(("", 90))
	print("Waiting on port:", 90)

	while 1:
		# Ist Daten aktualisieren
		data, addr = socket_receive.recvfrom(8)		
		
		if(len(data) == 7):# Batteriepaket
			batteryUpdate(data)
		
		elif(len(data) == 8):# Fahrradpaket
			for fahrrad in fahrraeder:
				# Diese zeile bitte mit den IP Adressen weiter oben anpassen, oder es funktioniert nicht
				#if(fahrrad.ip == addr[0]): 
				fahrrad.compute(data)