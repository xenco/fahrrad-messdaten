# Server
#
# Empfängt Daten vom Fahrrad Controller und kommuniziert mit der API

import socket, requests, random, os
clear = lambda: os.system('cls')

API_URL = "http://localhost/fahrrad/public/"

# Paketformat:
# 8 Byte
# 	Frame-No 					(1 Byte)
#	Power W 					(1 Byte)
# 	T: Zeit für N umdrehungen 	(2 Byte)
#	N: Anzahl Umdrehungen 		(1 Byte)
#	Pedalzeit halber Umlauf 	(2 Byte)
#	Mode 						(1 Byte)

def computeData(data):
	reifenUmfang = 2.1													# M
	u = 10

	pGen = data[0] 														# mittlere IST-Leistung in W
	T = int.from_bytes([data[1],data[2]], byteorder='big')				# Zeit für eine Tretlagerumdrehung in Sekunden
	nLm = int.from_bytes([data[3],data[4]], byteorder='big')			# Umdrehungen Lichtmaschine
	
	strecke = nLm * (reifenUmfang / u)
	geschwindigkeit = (strecke / (T / 15625)) * 3.6
	istLeistung = pGen
	
	clear()
	print("Raw: ", data)
	print()
	print("pGen: ", pGen)
	print("T: ", T)
	print("nLm: ", nLm)
	print()
	print("Umdrehungen: ", nLm)
	print("Zeit in Ticks: ", T)
	print("Zeit in Sekunden: ", T / 15625)
	print("Strecke: ", strecke)
	print("Geschwindigkeit: ", geschwindigkeit)
	print("istLeistung: ", istLeistung)
	
	return strecke, geschwindigkeit, istLeistung

if __name__ == "__main__":
	socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	socket.bind(("", 90))

	print("waiting on port:", 90)

	while 1:
		try:
			data, addr = socket.recvfrom(8)
			print(addr, data)
			strecke, geschwindigkeit, istLeistung = computeData(data)
			
			requests.post(API_URL + "data", data = {
				"ip": "10.0.0."+ str(random.choice([1,2,3])),
				"strecke": strecke,
				"geschwindigkeit": geschwindigkeit,
				"istLeistung": istLeistung
			})
		except:
			print("Error")
