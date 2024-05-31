import tkinter as tk
import subprocess

# Function to handle button press event
def handle_button():
    if switch_var.get():
        print("Switch is ON")
        publish_data("1")  
    else:
        print("Switch is OFF")
        publish_data("0")

def handle_leftright():
    if leftright_var.get():
        print("Switch is ON")
        publish_right("l")  
    else:
        print("Switch is OFF")
        publish_right("r")



# Function to publish data to Mosquitto MQTT broker
def publish_data(data):
    topic = "None/f/button1"  # Replace with your MQTT topic
    command = ["mosquitto_pub", "-h", "192.168.159.94", "-t", topic, "-m", data]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Published {data} to {topic}")
        print(f"Command output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to publish data: {e}")
        print(f"Command output: {e.output}")
        print(f"Command stderr: {e.stderr}")


def publish_right(data):
    topic = "None/f/right"  # Replace with your MQTT topic
    command = ["mosquitto_pub", "-h", "192.168.159.94", "-t", topic, "-m", data]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Published {data} to {topic}")
        print(f"Command output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to publish data: {e}")
        print(f"Command output: {e.output}")
        print(f"Command stderr: {e.stderr}")

# Setup Tkinter GUI
root = tk.Tk()
root.title("Tkinter and MQTT Example")
root.geometry("700x500")

# Create Tkinter switch (checkbox)
switch_var = tk.BooleanVar()
switch = tk.Checkbutton(root, text="Activate free mode", variable=switch_var, command=handle_button)
switch.pack(pady=20)

leftright_var = tk.BooleanVar()
switch2 = tk.Checkbutton(root, text="left or right", variable=leftright_var, command=handle_leftright)
switch2.pack(pady=20)

# Start Tkinter event loop
root.mainloop()
