# Server
#
# Empfängt Daten vom Fahrrad Controller und kommuniziert mit der API
import socket, random, os, json, pymysql
clear = lambda: os.system('cls')

socket_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket_receive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

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

	def sollDatenAktualisieren(self):
		db= pymysql.connect(host='localhost',user='root',password='',db='fahrradergometer',charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor)
		cur=db.cursor()
		cur.execute("SELECT sollLeistung,sollDrehmoment FROM fahrrad WHERE ip='"+self.ip+"'")
		
		sollLeistung = None
		sollDrehmoment = None
		for row in cur:
			sollLeistung   = row["sollLeistung"]
			sollDrehmoment = row["sollDrehmoment"]
		
		# Ist kein Wert, oder beide Werte gesetzt liegt ein Fehler vor und keine Änderung wird angewendet
		if((sollLeistung != None and sollDrehmoment == None) or (sollLeistung == None and sollDrehmoment != None)):
			# Leistung anpassen
			if(sollLeistung != None and sollDrehmoment == None):
				sollLeistung = int(sollLeistung)
				if(self.sollLeistung != bytes([sollLeistung])): # Änderung notwendig?
					self.sollLeistung = bytes([sollLeistung])
					self.sendToFC(1)
				
			# Drehmoment anpassen
			if(sollLeistung == None and sollDrehmoment != None):
				sollDrehmoment = int(sollDrehmoment)
				if(self.sollDrehmoment != bytes([sollDrehmoment])): # Änderung notwendig?
					self.sollDrehmoment = bytes([sollDrehmoment])
					self.sendToFC(2)
	
	# Sendet die Daten an den Fahrradcontroller zur Anpassung der Regelung
	def sendToFC(self, mode):
		byte_ip = bytes([int((self.ip).split(".")[0])])+bytes([int((self.ip).split(".")[1])])+bytes([int((self.ip).split(".")[2])])+bytes([int((self.ip).split(".")[3])])
		
		byte_port = bytes([0])+bytes([91])
		
		packet_who = byte_ip + byte_port
		packet_what = bytes([mode]) + (self.sollLeistung if mode == 1 else self.sollDrehmoment)
		
		ap_ip = "192.168.4.1"
		
		socket_send.sendto(packet_who,  (ap_ip, 91)) # 6 Byte [IP,PORT]
		socket_send.sendto(packet_what, (ap_ip, 91))# 2 Byte [MODUS,VALUE]
		
		print("who: " + str(packet_who) + ", what: " + str(packet_what))
		
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
		
		# Änderungen an die API senden
		print("Update " + self.ip + " mit istLeistung=" + str(self.istLeistung) + " strecke=" + str(self.strecke_gesamt)+ " geschwindigkeit=" + str(self.geschwindigkeit))
		
		db= pymysql.connect(host='localhost',user='root',password='',db='fahrradergometer',charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor)
		cur=db.cursor()
		
		cur.execute ("UPDATE fahrrad SET geschwindigkeit=%s, istLeistung=%s, strecke=%s WHERE (ip=%s AND fahrer_id is not NULL)", (str(self.geschwindigkeit), str(self.istLeistung), str(self.strecke_gesamt), self.ip))
		db.commit()
		
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

def batteryUpdate(data):
	uBat  = int.from_bytes([data[1],data[2]], byteorder='big') / 1000  # mV / 1000 = V
	iGen  = int.from_bytes([data[3],data[4]], byteorder='big') / 1000  # mA / 1000 = A
	iLoad = int.from_bytes([data[5],data[6]], byteorder='big') / 1000  # mA / 1000 = A
	
	# Änderung notwendig?
	db= pymysql.connect(host='localhost',user='root',password='',db='fahrradergometer',charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor)
	cur=db.cursor()
	
	num_rows = cur.execute ("SELECT * FROM batterie ORDER BY id DESC LIMIT 1")
	res = cur.fetchone()
	
	uBat_rounded  = round(uBat, 2)
	iGen_rounded  = round(iGen, 2)
	iLoad_rounded = round(iLoad, 2)
	
	if(num_rows == 0 or ((str(res["spannung"]) != str(uBat_rounded)) or (str(res["generatorstrom"]) != str(iGen_rounded)) or (str(res["laststrom"]) != str(iLoad_rounded)))):
		# Änderungen an die API senden
		print("Update Batterie: Spannung="+str(uBat)+" Generatorstrom="+str(iGen)+" Laststrom="+str(iLoad))

		cur.execute ("INSERT INTO batterie(spannung, generatorstrom, laststrom) VALUES(%s, %s, %s)",(str(uBat), str(iGen), str(iLoad)))
		db.commit()
	
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
		print(len(data), addr[0])
		
		
		if(len(data) == 7):# Batteriepaket
			batteryUpdate(data)
		
		elif(len(data) == 8):# Fahrradpaket
			for fahrrad in fahrraeder:
				#if(fahrrad.ip == addr): # Daten kommen von diesem Fahrrad
				fahrrad.compute(data)
					
			# Solldaten auswerten
			for fahrrad in fahrraeder:
				fahrrad.sollDatenAktualisieren()
			
		
