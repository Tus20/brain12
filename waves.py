import serial
import time
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import butter, lfilter

# Configure the serial port
port = 'COM9'  # Replace with the correct port for your Arduino (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux/Mac)
baud_rate = 9600
sampling_rate = 100  # Hz (based on Arduino delay of 10ms)

# Function to apply a band-pass filter
def butter_bandpass(lowcut, highcut, fs, order=5):
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    return b, a

def bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    return lfilter(b, a, data)

# Initialize serial connection
try:
    arduino = serial.Serial(port=port, baudrate=baud_rate, timeout=1)
    print(f"Connected to Arduino on {port}")
    time.sleep(2)  # Allow time for the connection to establish
except Exception as e:
    print(f"Error: {e}")
    exit()

# Initialize variables for real-time plotting
data = []
filtered_data = []
window_size = 500  # Number of samples to display at a time

# Configure the plot
plt.ion()
fig, ax = plt.subplots()
line1, = ax.plot([], [], label="Raw Signal")
line2, = ax.plot([], [], label="Filtered Signal (Alpha 8-13 Hz)", color='orange')
ax.set_xlim(0, window_size)
ax.set_ylim(0, 1023)  # Adjust based on your signal range (0–1023 for Arduino analogRead)
plt.legend()
plt.xlabel("Samples")
plt.ylabel("Amplitude")
plt.title("Brain Wave Signal")

try:
    while True:
        if arduino.in_waiting > 0:  # Check if there's data in the serial buffer
            try:
                # Read and decode a line from the serial port
                line = arduino.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    value = int(line)  # Convert the data to an integer
                    data.append(value)

                    # Process the signal when enough data is collected
                    if len(data) >= window_size:
                        # Apply a band-pass filter for Alpha waves (8-13 Hz)
                        filtered_signal = bandpass_filter(
                            data[-window_size:], lowcut=8, highcut=13, fs=sampling_rate, order=4
                        )
                        filtered_data = list(filtered_signal)

                        # Update the plot
                        line1.set_data(range(window_size), data[-window_size:])
                        line2.set_data(range(window_size), filtered_data)
                        ax.set_xlim(0, window_size)
                        ax.set_ylim(-30, 200)  # Fixed Y-axis range from -30 to 100
                        plt.pause(0.01)

            except ValueError:
                pass  # Ignore invalid data
            except UnicodeDecodeError:
                pass  # Ignore decoding errors

except KeyboardInterrupt:
    print("\nStopping data collection...")
finally:
    arduino.close()

plt.ioff()
plt.show()
