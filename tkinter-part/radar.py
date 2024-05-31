import matplotlib.pyplot as plt
import numpy as np
import paho.mqtt.client as mqtt

angle_data = None
distance_data = None

def on_message(client, userdata, message):
    global angle_data, distance_data
    topic = message.topic
    payload = float(message.payload.decode())

    if topic == "None/f/angle":
        angle_data = payload
    elif topic == "None/f/distance":
        distance_data = payload


client = mqtt.Client()
client.on_message = on_message


client.connect("192.168.159.94", 1883, 60)


client.subscribe("None/f/angle")
client.subscribe("None/f/distance")


fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
ax.set_ylim(-5, 400)  


def update_radar():
    if angle_data is not None and distance_data is not None:
        theta = np.deg2rad(angle_data)
        r = distance_data
        ax.clear()
        ax.set_ylim(-5, 400)
        ax.plot(theta, r, marker='o', markersize=5, linestyle='None')
        ax.set_title("Radar")
        ax.set_theta_zero_location('N')

def mqtt_loop():
    client.loop_start()


try:
    while True:
        mqtt_loop()
        update_radar()
        plt.pause(0.1) 
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
    plt.close()
