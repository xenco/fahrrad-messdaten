# Server
#
# Empfängt Daten vom Fahrrad Controller und kommuniziert mit der API

import socket, requests, random, os, json
clear = lambda: os.system('cls')

API_URL = "http://localhost/fahrrad/public/"

class Fahrrad:
	def __init__(self, ip, mac):
		self.ip = ip
		self.mac = mac
		
		self.strecke = 0
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

	def sollDatenAktualisieren(self):
		response = requests.get(API_URL + "data/" + self.ip)
		if(response.status_code == 200):
			json_data = json.loads(response.text)
			
			sollDrehmoment = json_data["fahrrad"]["sollDrehmoment"] # Int
			sollLeistung   = json_data["fahrrad"]["sollLeistung"] 	# Int
			
			# Ist kein Wert, oder beide Werte gesetzt liegt ein Fehler vor und keine Änderung wird angewendet
			if((sollLeistung == None and sollDrehmoment == None) or (sollLeistung != None and sollDrehmoment != None)):
				print("Keine Änderung, da fehlerhafte Daten")
			else:
				# Leistung anpassen
				if(sollLeistung != None and sollDrehmoment == None):
					if(self.sollLeistung != bytes([sollLeistung])): # Änderung notwendig?
						self.sollLeistung = bytes([sollLeistung])
						self.sendToFC(1)
					
				# Drehmoment anpassen
				if(sollLeistung == None and sollDrehmoment != None):
					if(self.sollDrehmoment != bytes([sollDrehmoment])): # Änderung notwendig?
						self.sollDrehmoment = bytes([sollDrehmoment])
						self.sendToFC(2)
	
	# Sendet die Daten an den Fahrradcontroller zur Anpassung der Regelung
	def sendToFC(self, mode):
		bytestring = bytes([mode]) + (self.sollLeistung if mode == 1 else self.sollDrehmoment)
		print(bytestring)
		
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

		self.pGen 	= data[0] 											 # mittlere IST-Leistung in W
		self.T 		= int.from_bytes([data[1],data[2]], byteorder='big') # Zeit für eine Tretlagerumdrehung in Sekunden
		self.nLm 	= int.from_bytes([data[3],data[4]], byteorder='big') # Umdrehungen Lichtmaschine
		
		self.strecke 		 = self.nLm * (self.reifenUmfang / self.u)
		self.geschwindigkeit = (self.strecke / (self.T / 15625)) * 3.6
		self.istLeistung 	 = self.pGen
		
		# Änderungen an die API senden
		requests.post(API_URL + "data", data = { 
			"ip": self.ip, 
			"strecke": self.strecke,
			"geschwindigkeit": self.geschwindigkeit,
			"istLeistung": self.istLeistung
		})
		
	def printData(self):
		print("Raw: ", self.data)
		print()
		print("pGen: ", self.pGen)
		print("T: ", self.T)
		print("nLm: ", self.nLm)
		print()
		print("Umdrehungen: ", self.nLm)
		print("Zeit in Ticks: ", self.T)
		print("Zeit in Sekunden: ", self.T / 15625)
		print("Strecke: ", self.strecke)
		print("Geschwindigkeit: ", self.geschwindigkeit)
		print("istLeistung: ", self.istLeistung)

if __name__ == "__main__":
	fahrraeder = [
		Fahrrad("10.0.0.0", "00:00:00:00:00:00"),
		Fahrrad("10.0.0.1", "00:00:00:00:00:01"),
		Fahrrad("10.0.0.2", "00:00:00:00:00:02")
	]
	
	socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	socket.bind(("", 90))

	print("Waiting on port:", 90)

	while 1:
		# Ist Daten aktualisieren
		data, addr = socket.recvfrom(8)
		
		#clear()
		for fahrrad in fahrraeder:
			#if(fahrrad.ip == addr): # Daten kommen von diesem Fahrrad
			fahrrad.compute(data)
				
		# Solldaten auswerten
		for fahrrad in fahrraeder:
			fahrrad.sollDatenAktualisieren()
