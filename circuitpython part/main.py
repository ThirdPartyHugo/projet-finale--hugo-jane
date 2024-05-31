import time
import board
import digitalio
import pwmio
from adafruit_motor import servo
import os
import ssl
import socketpool
import wifi
import analogio
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT

# Define pins
trigger_pin = board.IO12  # D7
echo_pin = board.IO13     # D8
motor1 = board.IO8        # D3
motor2 = board.IO9        # D4
motor3 = board.IO10       # D5
motor4 = board.IO14       # D9

# Motor pin setup
coil_A_1_pin = digitalio.DigitalInOut(motor1)
coil_A_2_pin = digitalio.DigitalInOut(motor2)
coil_B_1_pin = digitalio.DigitalInOut(motor3)
coil_B_2_pin = digitalio.DigitalInOut(motor4)

coil_A_1_pin.direction = digitalio.Direction.OUTPUT
coil_A_2_pin.direction = digitalio.Direction.OUTPUT
coil_B_1_pin.direction = digitalio.Direction.OUTPUT
coil_B_2_pin.direction = digitalio.Direction.OUTPUT


sound_sensor = analogio.AnalogIn(board.A1)
light_sensor = analogio.AnalogIn(board.A2)  # Supposons que le capteur de lumière est connecté à la broche A2
 
def scale_value(value, in_min, in_max, out_min, out_max):
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
 
def average_readings(sensor, num_readings=10):
    total = 0
    for _ in range(num_readings):
        total += sensor.value
        time.sleep(0.01)  # Petit délai entre les lectures
    return total // num_readings

# Stepping sequence
StepCount = 8
Seq = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1]
]

# Ultrasonic sensor setup
trigger = digitalio.DigitalInOut(trigger_pin)
trigger.direction = digitalio.Direction.OUTPUT

led = digitalio.DigitalInOut(board.IO7)  # D2
led.direction = digitalio.Direction.OUTPUT

led2 = digitalio.DigitalInOut(board.IO15)
led2.direction = digitalio.Direction.OUTPUT

led3 = digitalio.DigitalInOut(board.IO11)
led3.direction = digitalio.Direction.OUTPUT

echo = digitalio.DigitalInOut(echo_pin)
echo.direction = digitalio.Direction.INPUT

led.value = False

# Variables
total_steps = 0
steps_per_revolution = 536  # Adjust this value based on your stepper motor's specification
manual_mode_active = False
direction = ""

def setStep(w1, w2, w3, w4):
    coil_A_1_pin.value = w1
    coil_A_2_pin.value = w2
    coil_B_1_pin.value = w3
    coil_B_2_pin.value = w4

def connected(client):
    print("Connected to Adafruit IO!")

def subscribe(client, userdata, topic, granted_qos):
    print(f"Subscribed to {topic}")

def unsubscribe(client, userdata, topic, pid):
    print(f"Unsubscribed from {topic} with PID {pid}")

def disconnected(client):
    print("Disconnected from Adafruit IO!")

def message(client, feed_id, payload):
    # La fonction message sera appelée lorsque le flux auquel on est abonné a une nouvelle valeur.
    # Le paramètre feed_id identifie le flux, et le paramètre payload contient la nouvelle valeur.
    print("Le flux {0} a reçu une nouvelle valeur : {1}".format(feed_id, payload))

def handle_button_press(client, feed_id, payload):
    global manual_mode_active
    print(f"Received data from feed {payload}")
    if payload == "1":  # Switch to manual mode
        manual_mode_active = True
        stop_motor()
    elif payload == "0":  # Switch to automatic mode
        manual_mode_active = False


def handle_leftright_press(client, feed_id, payload):
    global manual_mode_active, direction
    print(f"Received data from feed {payload}")
    if payload == "l":  # Switch to manual mode
        direction = "l"
    elif payload == "r":  # Switch to automatic mode
        direction = "r"


def connecter_mqtt():
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
        print("WiFi and Adafruit IO credentials are not available in settings.toml")
        raise


    if not wifi.radio.connected:
        print(f"Connecting to {secrets['ssid']}")
        wifi.radio.connect(secrets["ssid"], secrets["password"])
        print(f"Connected to {secrets['ssid']}!")

    pool = socketpool.SocketPool(wifi.radio)
    mqtt = MQTT.MQTT(socket_pool=pool,
                     broker="192.168.159.94",
                     port=1883)
    io = IO_MQTT(mqtt)

    io.on_connect = connected
    io.on_disconnect = disconnected
    io.on_subscribe = subscribe
    io.on_unsubscribe = unsubscribe

    io.connect()

    

    io.add_feed_callback("button1", handle_button_press)
    io.add_feed_callback("right", handle_leftright_press)
    

    return io

io = connecter_mqtt()

io.subscribe("button1")
io.subscribe("right")

button_pressed = False

# Function to convert steps to angle
def steps_to_angle(steps):
    return (steps % steps_per_revolution) * (360.0 / steps_per_revolution)

# Function to rotate stepper motor clockwise
def stepper_forward(delay, steps):
    global total_steps
    for i in range(steps):
        if manual_mode_active:
            break
        for j in range(StepCount):
            setStep(Seq[j][0], Seq[j][1], Seq[j][2], Seq[j][3])
            time.sleep(delay)
        total_steps += 1
        if i % 20 == 0:  # Publish distance and angle every 20 steps
            distance = get_distance()
            if distance != 0 and distance < 400:
                led.value = True  # Turn on the LED
            else:
                led.value = False
            io.publish("distance", distance)
            current_angle = steps_to_angle(total_steps)
            io.publish("angle", current_angle)
            print(f"Distance: {distance:.2f} cm, Angle: {current_angle:.2f} degrees")
            raw_sound_value = average_readings(sound_sensor)  # Obtenir la valeur moyenne du capteur de son
            scaled_sound_value = scale_value(raw_sound_value, 0, 65535, 0, 100)  # Mise à l'échelle vers une plage plus haute si nécessaire
        
            # Lire et traiter les valeurs du capteur de lumière
            raw_light_value = average_readings(light_sensor)  # Obtenir la valeur moyenne du capteur de lumière
            scaled_light_value = scale_value(raw_light_value, 0, 65535, 0, 100)  # Mise à l'échelle vers une plage plus haute si nécessaire
        
            if scaled_light_value > 60:
                led2.value = True
            else:
                led2.value = False

            # Afficher les résultats
            print(f"Capteur de Son - Valeur brute : {raw_sound_value}, Valeur mise à l'échelle : {scaled_sound_value}")
            print(f"Capteur de Lumière - Valeur brute : {raw_light_value}, Valeur mise à l'échelle : {scaled_light_value}")
            io.loop()  # Process MQTT messages and handle callbacks

# Function to rotate stepper motor counterclockwise
def stepper_backward(delay, steps):
    global total_steps
    for i in range(steps):
        if manual_mode_active:
            break
        for j in reversed(range(StepCount)):
            setStep(Seq[j][0], Seq[j][1], Seq[j][2], Seq[j][3])
            time.sleep(delay)
        total_steps -= 1
        if i % 20 == 0:  # Publish distance and angle every 20 steps
            distance = get_distance()
            if distance != 0 and distance < 400:
                led.value = True  # Turn on the LED
            else:
                led.value = False
            io.publish("distance", distance)
            current_angle = steps_to_angle(total_steps)
            io.publish("angle", current_angle)
            print(f"Distance: {distance:.2f} cm, Angle: {current_angle:.2f} degrees")
            raw_sound_value = average_readings(sound_sensor)  # Obtenir la valeur moyenne du capteur de son
            scaled_sound_value = scale_value(raw_sound_value, 0, 65535, 0, 100)  # Mise à l'échelle vers une plage plus haute si nécessaire
        
            # Lire et traiter les valeurs du capteur de lumière
            raw_light_value = average_readings(light_sensor)  # Obtenir la valeur moyenne du capteur de lumière
            scaled_light_value = scale_value(raw_light_value, 0, 65535, 0, 100)  # Mise à l'échelle vers une plage plus haute si nécessaire
        
            if scaled_light_value > 60:
                led2.value = True
            else:
                led2.value = False

            # Afficher les résultats
            print(f"Capteur de Son - Valeur brute : {raw_sound_value}, Valeur mise à l'échelle : {scaled_sound_value}")
            print(f"Capteur de Lumière - Valeur brute : {raw_light_value}, Valeur mise à l'échelle : {scaled_light_value}")
            io.loop()  # Process MQTT messages and handle callbacks
        
        

# Function to get distance from ultrasonic sensor
def get_distance():
    trigger.value = True
    time.sleep(0.00001)
    trigger.value = False

    timeout_start = time.monotonic()
    while echo.value == False:
        if (time.monotonic() - timeout_start) > 0.1:
            print("Error: Echo pin not responding (LOW)")
            return None

    pulse_start = time.monotonic()
    while echo.value == True:
        if (time.monotonic() - timeout_start) > 0.1:
            print("Error: Echo pin not responding (HIGH)")
            return None

    pulse_end = time.monotonic()
    pulse_duration = pulse_end - pulse_start

    speed_of_sound = 34300
    distance = (pulse_duration * speed_of_sound) / 2

    return distance


def manual_forward(delay, steps):
    global total_steps
    for i in range(steps):
        for j in range(StepCount):
            setStep(Seq[j][0], Seq[j][1], Seq[j][2], Seq[j][3])
            time.sleep(delay)
        total_steps += 1
        if i % 20 == 0:  # Publish distance and angle every 20 steps
            distance = get_distance()
            if distance != 0 and distance < 400:
                led.value = True  # Turn on the LED
            else:
                led.value = False
            io.publish("distance", distance)
            current_angle = steps_to_angle(total_steps)
            io.publish("angle", current_angle)
            print(f"Distance: {distance:.2f} cm, Angle: {current_angle:.2f} degrees")
            raw_sound_value = average_readings(sound_sensor)  # Obtenir la valeur moyenne du capteur de son
            scaled_sound_value = scale_value(raw_sound_value, 0, 65535, 0, 100)  # Mise à l'échelle vers une plage plus haute si nécessaire
        
            # Lire et traiter les valeurs du capteur de lumière
            raw_light_value = average_readings(light_sensor)  # Obtenir la valeur moyenne du capteur de lumière
            scaled_light_value = scale_value(raw_light_value, 0, 65535, 0, 100)  # Mise à l'échelle vers une plage plus haute si nécessaire
        
            if scaled_light_value > 60:
                led2.value = True
            else:
                led2.value = False

            # Afficher les résultats
            print(f"Capteur de Son - Valeur brute : {raw_sound_value}, Valeur mise à l'échelle : {scaled_sound_value}")
            print(f"Capteur de Lumière - Valeur brute : {raw_light_value}, Valeur mise à l'échelle : {scaled_light_value}")
            io.loop()  # Process MQTT messages and handle callbacks


def manual_backward(delay, steps):
    global total_steps
    for i in range(steps):
        for j in reversed(range(StepCount)):
            setStep(Seq[j][0], Seq[j][1], Seq[j][2], Seq[j][3])
            time.sleep(delay)
        total_steps -= 1
        if i % 20 == 0:  # Publish distance and angle every 20 steps
            distance = get_distance()
            if distance != 0 and distance < 400:
                led.value = True  # Turn on the LED
            else:
                led.value = False
            io.publish("distance", distance)
            current_angle = steps_to_angle(total_steps)
            io.publish("angle", current_angle)
            print(f"Distance: {distance:.2f} cm, Angle: {current_angle:.2f} degrees")
            raw_sound_value = average_readings(sound_sensor)  # Obtenir la valeur moyenne du capteur de son
            scaled_sound_value = scale_value(raw_sound_value, 0, 65535, 0, 100)  # Mise à l'échelle vers une plage plus haute si nécessaire
        
            # Lire et traiter les valeurs du capteur de lumière
            raw_light_value = average_readings(light_sensor)  # Obtenir la valeur moyenne du capteur de lumière
            scaled_light_value = scale_value(raw_light_value, 0, 65535, 0, 100)  # Mise à l'échelle vers une plage plus haute si nécessaire
        
            if scaled_light_value > 60:
                led2.value = True
            else:
                led2.value = False

            # Afficher les résultats
            print(f"Capteur de Son - Valeur brute : {raw_sound_value}, Valeur mise à l'échelle : {scaled_sound_value}")
            print(f"Capteur de Lumière - Valeur brute : {raw_light_value}, Valeur mise à l'échelle : {scaled_light_value}")
            io.loop()  # Process MQTT messages and handle callbacks




def manual_mode():
    while manual_mode_active:
        global direction
        io.loop()  # Process MQTT messages and handle callbacks
        
        # Check if "left" or "right" command is received
        print(direction)
        if direction == "l":
            manual_backward(delay=0.005, steps=120)  # Move 60 steps counterclockwise (backward)
        elif direction == "r":
            manual_forward(delay=0.005, steps=120)  # Move 60 steps clockwise (forward)
        else:
            pass

# Function to stop the motor
def stop_motor():
    setStep(0, 0, 0, 0)

# Main loop
while True:
    io.loop()  # Process MQTT messages and handle callbacks

    if manual_mode_active:
        
        manual_mode()
    else:
        stepper_backward(delay=0.005, steps=536)
        stepper_forward(delay=0.005, steps=536)


# mqtt mosquitto command line
# mosquitto_sub -h 192.168.0.94 -t "+/+/distance"
# mosquitto_sub -h 192.168.207.94 -t button1



 
# Initialiser les entrées analogiques pour les capteurs de son et de lumière

 
