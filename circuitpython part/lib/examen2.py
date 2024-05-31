import board

# Importations pour écran
import time
import math
from adafruit_display_text.label import Label
from displayio import I2CDisplay as BusEcran
from displayio import Group
import displayio
from adafruit_displayio_ssd1306 import SSD1306 as Ecran
import terminalio
import adafruit_lis3dh
from adafruit_display_text import label
import adafruit_displayio_ssd1306
import ssl
import digitalio
import socketpool
import os
import wifi
from adafruit_io.adafruit_io import IO_MQTT
import adafruit_minimqtt.adafruit_minimqtt as MQTT

import aide_examen
# Fonctions disponibles pour l'aide à l'examen
# def connection_serveur_mqtt(self,code_etudiant: str) -> MQTT.MQTT
# def conversion_roulis(self,x: float, y: float, z: float) -> float
# def conversion_tangage(self,x: float, y: float, z: float) -> float
# def recuperation_accelerations(self) -> tuple[float, float, float]
# def envoi_donnees(self,roll: float, pitch: float) -> None
# def recuperation_date_heure(self) -> struct_time

# Vous pouvez remplir les fonctions proposées ou bien en écrire des nouvelles. 
# Vous êtes obligés d'utiliser la fonction __init__() et boucle().
i2c = board.I2C()

def connected(client):
    print("Connecté au serveur du prof !")

def subscribe(client, userdata, topic, granted_qos):
    pass

def unsubscribe(client, userdata, topic, pid):
    print("Désabonné de {0} avec PID {1}".format(topic, pid))

def disconnected(client):
    print("Déconnecté d'Adafruit IO !")

def message(client, feed_id, payload):
    print("Received data from feed {0}: {1}".format(feed_id, payload))


class examen2:

    # Variables globales à la classe
    """self._lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c, address=0x19)
    self._pool = socketpool.SocketPool(wifi.radio)
    self._mqtt = MQTT.MQTT(socket_pool=self.__pool,
                     broker="192.168.207.94",
                     port=1883)
    self._sd = None
    self._aide = None"""

    def __init__(self) -> None:
        self.init_ecran()
        self.initialisation_accelerometre()
         # Remplacez par _aide.connection_serveur_mqtt() si besoin

        # Si vous avez besoin des fonctions d'aide, décommentez la ligne suivante:
        # self._aide = aide_examen.aide_examen()


    def initialisation_accelerometre(self):
        self._lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c, address=0x19) # À remplir
        self._lis3dh.set_tap(2,80)
        io = self.connexion_mqtt()
        
        while True:
            x, y, z = self._lis3dh.acceleration
            texts = "x = "+str(x)+"\ny = "+str(y)
            roulis = math.atan2(y,z)
            tangage =  math.atan2(-x,math.sqrt(y^2,z^2))
            roulisdegrees = roulis * 57.3
            tangagedegrees = tangage * 57.3
            texts = "roulis "+str(roulisdegrees) + "\ntangage"+str(tangagedegrees)
            self.rafraichir_ecran(texts)
            print(texts)
            io.publish("201945297/roll",str(roulisdegrees))
            io.publish("201945297/pitch",str(tangagedegrees))
            time.sleep(5)
        
    def alerte_son():
        buzzer = digitalio.DigitalInOut(board.IO10)

    def connexion_mqtt(self):
        try:
            if os.getenv("AIO_USERNAME") and os.getenv("AIO_KEY"):
                secrets = {
                    "aio_username": os.getenv("AIO_USERNAME"),
                    "aio_key": os.getenv("AIO_KEY"),
                    "ssid": os.getenv("CIRCUITPY_WIFI_SSID"),
                    "password": os.getenv("CIRCUITPY_WIFI_PASSWORD"),
                }
            else:
                raise ImportError
        except ImportError:
            print(
                "Les informations pour la connexion au WIFI et pour Adafruit IO ne sont pas disponibles dans le fichier settings.toml")
            raise

        aio_username = secrets["aio_username"]
        aio_key = secrets["aio_key"]

        if not wifi.radio.connected:
            print("Connexion à %s" % secrets["ssid"])
            wifi.radio.connect(secrets["ssid"], secrets["password"])
            print("Connecté à %s!" % secrets["ssid"])

        self._pool = socketpool.SocketPool(wifi.radio)
        self._mqtt = MQTT.MQTT(socket_pool=self._pool,
                        username="examen",
                        password="vacances",
                        ssl_context=ssl.create_default_context(),
                        client_id = "201945297",
                        broker="kf4b994b.ala.us-east-1.emqxsl.com",
                        is_ssl=True,
                        port=8883)
        io = IO_MQTT(self._mqtt)

        io.on_connect = connected
        io.on_disconnect = disconnected
        io.on_subscribe = subscribe
        io.on_unsubscribe = unsubscribe
        io.on_message = message

        io.connect()
        return io

    def initialisation_lecteurSD(self):
        self._sd = None

    def init_ecran(self):
        displayio.release_displays()
        self._bus_ecran = BusEcran(board.I2C(), device_address=0x3C)
        self._ecran = Ecran(self._bus_ecran, width=128, height=64, rotation=180)
        self._splash = Group()
        self._ecran.root_group = self._splash
        self._zone_texte = Label(terminalio.FONT, text="acceleration", color=0xFFFFFF, x=5, y=10)
        self._splash.append(self._zone_texte)

    def rafraichir_ecran(self, texte: str) -> None:
        self._zone_texte.text = texte
        self._ecran.refresh()

    def boucle(self) -> None:
        while True:
            pass