import streamlit as st
import serial
import time
import numpy as np
from scipy.signal import butter, lfilter
import matplotlib.pyplot as plt
import random

# Configure the serial port
port = 'COM9'  # Replace with your Arduino port
baud_rate = 9600
sampling_rate = 100  # Hz
window_size = 500  # Number of samples to display at a time

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

# Task prioritization logic
def assign_task_priority(brain_state, tasks):
    if brain_state == "Calm and Alert (Alpha)":
        return sorted(tasks, key=lambda x: x['difficulty'])
    elif brain_state == "Active Thinking or Stress (Beta)":
        return sorted(tasks, key=lambda x: x['difficulty'], reverse=True)
    elif brain_state == "Relaxation or Drowsiness (Theta)":
        return sorted(tasks, key=lambda x: x['difficulty'])
    elif brain_state == "Deep Sleep (Delta)":
        return []  # No tasks
    else:
        return tasks  # Default

# Simulate brain state detection (Replace with real logic)
def simulate_brain_state():
    states = ["Calm and Alert (Alpha)", "Active Thinking or Stress (Beta)", 
              "Relaxation or Drowsiness (Theta)", "Deep Sleep (Delta)"]
    return random.choice(states)

# Streamlit UI
st.title("Brainwave Task Prioritization")

# Task input form
tasks = []
task_input = st.text_input("Enter Task Name:")
difficulty_input = st.selectbox("Select Task Difficulty", ["Easy", "Medium", "Hard"], index=0)

if st.button("Add Task"):
    if task_input and difficulty_input:
        difficulty = {"Easy": 0, "Medium": 1, "Hard": 2}[difficulty_input]
        tasks.append({"task": task_input, "difficulty": difficulty})
        st.success(f"Task '{task_input}' added!")

# Display added tasks
if tasks:
    st.subheader("Your Tasks")
    for task in tasks:
        st.write(f"- {task['task']} (Difficulty: {task['difficulty']})")

# Real-time processing
if st.button("Start Brainwave Analysis"):
    if not tasks:
        st.error("Please add tasks before starting analysis.")
    else:
        st.info("Collecting data... Please wait for 40 seconds.")
        data = []
        filtered_data = []
        start_time = time.time()
        try:
            arduino = serial.Serial(port=port, baudrate=baud_rate, timeout=1)
            time.sleep(2)  # Allow time for the connection to establish
        except Exception as e:
            st.error(f"Error connecting to Arduino: {e}")
            arduino = None

        while time.time() - start_time < 40:
            if arduino and arduino.in_waiting > 0:
                try:
                    # Read and decode a line from the serial port
                    line = arduino.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        value = int(line)
                        data.append(value)

                        if len(data) >= window_size:
                            # Apply a band-pass filter for Alpha waves (8-13 Hz)
                            filtered_signal = bandpass_filter(
                                data[-window_size:], lowcut=8, highcut=13, fs=sampling_rate, order=4
                            )
                            filtered_data = list(filtered_signal)

                            # Simulate brain state detection
                            brain_state = simulate_brain_state()

                            # Prioritize tasks
                            prioritized_tasks = assign_task_priority(brain_state, tasks)

                            # Display results
                            st.subheader("Brain State")
                            st.write(f"Brain State Detected: **{brain_state}**")

                            st.subheader("Prioritized Tasks")
                            for idx, task in enumerate(prioritized_tasks):
                                st.write(f"{idx + 1}. {task['task']}")

                            # Plotting live data
                            fig, ax = plt.subplots()
                            ax.plot(data[-window_size:], label="Raw Signal")
                            ax.plot(filtered_data, label="Filtered Signal (Alpha 8-13 Hz)", color="orange")
                            ax.set_title("Brain Wave Signal")
                            ax.set_xlabel("Samples")
                            ax.set_ylabel("Amplitude")
                            ax.legend()
                            st.pyplot(fig)

                except (ValueError, UnicodeDecodeError):
                    pass  # Ignore invalid data
            time.sleep(0.1)  # Allow for updates

        if arduino:
            arduino.close()
