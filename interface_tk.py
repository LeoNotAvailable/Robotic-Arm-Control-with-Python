from ai_robotic_arm import speak, ask_local, main_write, transcribe_audio, save_record, main, change_command_form, translate, ensure_sequence_file
import tkinter as tk
from tkinter import ttk, messagebox
import time
from time import sleep
import serial
import threading
import pyaudio
import json
import os
import numpy as np
from functools import partial
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

port = "COM3"
baudrate = 115200


# Graphic offsets for position 0, with this you can define the position of the servos in the 3D representation
GRAPHIC_ZERO = {
    "S5": 0,   # gripper
    "S4": 0,   # wrist
    "S3": 0,    # elbow
    "S2": 0,   # shoulder
    "S1": 0,  # base
}


# Initial positions for the servos. Must be adjusted depending on the arm of everyone.
INIT_POSITIONS = {
    "S5": 0,
    "S4": 0,
    "S3": 0,
    "S2": 0,
    "S1": 0 
}



try:
    ser = serial.Serial(port, baudrate, timeout=1)
    sleep(2)
    print(f"Connected to serial port: {port}")
except Exception as e:
    print(f"Could not connect to serial port: {port}.\nError: {e}")
    ser = None

servo_ids = ["S1", "S2", "S3", "S4", "S5"]
servo_labels = ["Base", "Shoulder", "Elbow", "Wrist", "Gripper"]
servo_positions = {id: 0 for id in servo_ids}

NAME_TO_ID = {
    "base": "S1",
    "shoulder": "S2",
    "elbow": "S3",
    "wrist": "S4",
    "gripper": "S5",
    "clamp": "S5" # As the AI may return any of both, they're considered.
}

current_recording = []
saved_recordings = {"last": []}
recording = False
last_stable_time = 0 

sequences_file = ensure_sequence_file() # Creates or search for a file to save the sequences in the same folder as the script.

def load_sequences():
    # Returns all the sequences saved.
    if os.path.exists(sequences_file):
        try:
            with open(sequences_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"last": []}
    return {"last": []}


def save_sequences():
    # Save the sequences in the file when they're modified.It doesn't return anything.
    with open(sequences_file, 'w') as f:
        json.dump(saved_recordings, f, indent=2)

saved_recordings = load_sequences()



def send_servo_position(servo_id, angle):
    # If serial is connected, sends the servo_id and angle to de microcontroller. Else, says "simulation..." and doesn't do anything. It doesn't return anything.
    if ser:
        cmd = f"{servo_id}:{angle}\n"
        ser.write(cmd.encode("utf-8"))
        print(f"Send: {cmd.strip()}")
    else:
        print(f"[Simulation] {servo_id} --> {angle} degrees. Order not sent!")

def update_servo(servo_id, angle):
    # Updates all the relative information to the servo, and the graphic simulation. It doesn't return anything.
    servo_positions[servo_id] = angle
    send_servo_position(servo_id, angle)
    if 'ani' in globals():
        update_arm()

def slider_changed(servo_index, new_value):
    # Updates the servos whet the slider change, and save the record if it was recording. It doesn't return anything.
    angle = int(float(new_value))
    servo_id = servo_ids[servo_index]
    update_servo(servo_id, angle)
    if recording:
        schedule_recording()

def schedule_recording():
    # Saves the last change in the recording list. Considers the time, with the var. delta_t. It doesn't return anything.
    global last_stable_time
    now = time.time()
    delta_t = now - last_stable_time
    positions = [servo_positions[id] for id in servo_ids]
    current_recording.append((delta_t,) + tuple(positions))
    last_stable_time = now

def start_recording():
    # Starts all the recording processes. It doesn't return anything.
    global recording, current_recording, last_stable_time
    if not recording:
        recording = True
        current_recording = []
        last_stable_time = time.time()
        saved_recordings["last"] = current_recording
        print("Recording started...")
        speak("Commands recording iniciated...")
        update_recording_list()

def stop_recording():
    # Stops the recording and save the sequences in the sequence "last". It doesn't return anything.
    global recording
    if recording:
        recording = False
        print(f"Recording ended. Duration: {len(current_recording)} moves")
        speak(f"Recording ended with {len(current_recording)} moves.")
        update_recording_list()
        save_sequences()

def save_recording():
    # Save the recording with a different name, differentiating it form "last". It doesn't return anything.
    name = entry_name.get().strip()
    if not name:
        speak("You must introduce a name for the record!")
        messagebox.showerror("Error", "The name cannot be empty")
        return
    if name in saved_recordings:
        speak("You cannot introduce an existing name!")
        messagebox.showerror("Error", "The name already exists")
        return
    if not current_recording:
        speak("There is no recording to be saved!")
        messagebox.showerror("Error", "There's no recording to be saved")
        return
    saved_recordings[name] = current_recording.copy()
    entry_name.delete(0, tk.END)
    update_recording_list()
    print(f"Recording saved as '{name}'")
    speak(f"You have saved the recording as {name}.")
    save_sequences()

def delete_recording():
    # Deletes a saved record, it doesn't allow you to remove "last". It doesn't return anything.
    name = selected_recording.get()
    if name == "last":
        speak("It is not possible to remove the recording last!")
        messagebox.showerror("Error", "You cannot remove the recording 'last'")
        return
    else:
        speak(f"Are you shure you want to remove the sequence {name}?")
    if messagebox.askyesno("Confirm", f"Remove '{name}' definitely?"):
        del saved_recordings[name]
        update_recording_list()
        print(f"Recording '{name}' removed")
        speak("The recording has been removed.")
        save_sequences()

def update_recording_list():
    # Adds a new record, a new sequence. It doesn't return anything.
    global selected_recording
    recordings = ["last"] + [k for k in saved_recordings.keys() if k != "last"]
    recording_menu['values'] = recordings
    selected_recording.set("last" if "last" in recordings else "")

def replay_movements():
    # Reproduces the selected sequence. It doesn't return anything.
    global selected_recording
    name = selected_recording.get()
    log = saved_recordings.get(name, [])
    if not log:
        speak("You have not selected a valid recording!")
        messagebox.showerror("Error", "Select a valid recording")
        return
        
    print(f"Reproducing '{name}' ({len(log)} moves)...")
    speak(f"You are reproducing the sequence {name}!")
    base_time = time.time()
    for entry in log:
        delta_t, *angles = entry
        while time.time() - base_time < delta_t:
            root.update()
            time.sleep(0.01)
        for i, angle in enumerate(angles):
            servo_scales[i].set(angle)
        base_time = time.time()
    sleep(0.05)
    print("Reproduction finished!")
    speak(f"The sequence {name} has been finished!")

def initialize_servos():
    # Set all servos to the initial position. It doesn't return anything.
    for servo_id in servo_ids:
        angle = INIT_POSITIONS.get(servo_id, 0)
        idx = servo_ids.index(servo_id)
        servo_scales[idx].set(angle)
    speak("Servos established to initial position.")

def send_text_command():
    # Sends a text for the AI to answer it. It doesn't return anything, but actives the function process_ia_response().
    user_input = entry_ia_text.get().strip()
    if not user_input:
        speak("You cannot send an empty text!")
        messagebox.showerror("Error", "The text cannot be empty")
        return
        
    try:
        answer = main_write(user_input)
        process_ia_response(answer)
    except Exception as e:
        messagebox.showerror("Error", f"Error while processing the command: {str(e)}")
    finally:
        entry_ia_text.delete(0, tk.END)

def record_audio(frames, stop_event, frecuencia_muestra=16000, canales=1, fragmento=1024):
    # Records the audio record until the button is released. It doesn't return anything.
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=canales,
        rate=frecuencia_muestra,
        input=True,
        frames_per_buffer=fragmento)
        
    while not stop_event.is_set():
        data = stream.read(fragmento)
        frames.append(data)
        
    stream.stop_stream()
    stream.close()
    p.terminate()

def start_audio_recording():
    # Start the audio recording. It doesn't return anything.
    global audio_frames, stop_event, audio_thread
    audio_frames = []
    stop_event = threading.Event()
    audio_thread = threading.Thread(target=record_audio, args=(audio_frames, stop_event))
    audio_thread.start()
    print("Recording...")
    speak("Recording started...")

def stop_audio_recording():
    # Stops the audio recording. It doesn't return anything, but actives the process_audio_command() function.
    global audio_frames, stop_event, audio_thread
    stop_event.set()
    audio_thread.join()
    print("Record finished")
    speak("Record finished, processing the record...")
    
    if audio_frames:
        archivo_audio_temp = save_record(audio_frames, 16000)
        transcripcion = transcribe_audio(archivo_audio_temp)
        if transcripcion:
            process_audio_command(transcripcion)
        else:
            messagebox.showerror("Error", "Failed transcription")
    else:
        messagebox.showwarning("Warning", "The audio wasn't recorded")

def process_audio_command(transcripcion):
    # Processes the transcripted audio, and actives the function process_ia_response() with the answer of the AI. It doesn't return anything.
    if len(transcripcion) >= 3:
        answer = ask_local(translate(transcripcion) + 
            ", Generate a Python list containing tuples with servo positions (in degrees only) and servo names. Format each tuple as (ServoPositionDegrees, ServoName). Use ONLY these English servo names: base, shoulder, elbow, wrist, gripper. If you use any different, it won't work, so ignore any different servo in the input, or find a synonym in the list. Extract only the position values that appear in this message, never invent information, and if you cannot find any valid information, return an empty list []. Never invent information, just return []. return ONLY the list, if you send text, the app won't work.")
        answer = main(answer)
        print(transcripcion)
        
        if answer:
            process_ia_response(answer)

        else:
            speak("The commands are not valids!")
            messagebox.showwarning("Warning", "No valid commands detected")

def process_ia_response(answer):
    # Assures that the answer has the form: [(S1:29), (S3:50)...] and it's valid. Updates the servos. It doesn't return anything.
    if not answer:
        speak("The commands are not valids!")
        messagebox.showwarning("Warning", "No valid commands detected")
        return

    try: 
        for servo_name, grados in answer:
            servo_id = NAME_TO_ID.get(servo_name, "S1")
            idx = servo_ids.index(servo_id)
            servo_scales[idx].set(grados)
        speak("All servos have been modified.")
    except Exception as e:
        messagebox.showerror("Error", f"Error while executing the commands: {str(e)}")

# Configuration of the UI, the interface.

root = tk.Tk()
root.title("Robotic Arm with 5 Servos, AI and Graphic Visualization")
selected_recording= tk.StringVar(value="last")
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

title_label = tk.Label(root, text="Control and Intelligent Recording", font=("Arial", 14, "bold"))
title_label.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew")

main_frame = tk.Frame(root)
main_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure((0,1), weight=1)

root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

sliders_frame = tk.Frame(main_frame)
sliders_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

servo_scales = []
for i, label_text in enumerate(servo_labels):
    lbl = tk.Label(sliders_frame, text=label_text)
    lbl.grid(row=i, column=0, padx=5, pady=5, sticky="e")
    
    scale = tk.Scale(
        sliders_frame,
        from_=0,
        to=180,
        orient=tk.HORIZONTAL,
        command=partial(slider_changed, i)
    )
    scale.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
    servo_scales.append(scale)

rec_frame = tk.LabelFrame(main_frame, text="Recording Management")
rec_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
rec_frame.grid_rowconfigure(3, weight=1)

tk.Label(rec_frame, text="Select:").grid(row=0, column=0, padx=5, pady=5)
recording_menu = ttk.Combobox(rec_frame, textvariable=selected_recording, state="readonly")
recording_menu.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
update_recording_list()

entry_name = tk.Entry(rec_frame)
entry_name.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

btn_frame = tk.Frame(rec_frame)
btn_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

btn_start = tk.Button(btn_frame, text="Start Recording", command=start_recording)
btn_start.grid(row=0, column=0, padx=2, pady=2, sticky="ew")

btn_stop = tk.Button(btn_frame, text="Stop Recording", command=stop_recording)

btn_stop.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

btn_save = tk.Button(btn_frame, text="Save Recording", command=save_recording)
btn_save.grid(row=0, column=2, padx=2, pady=2, sticky="ew")

btn_delete = tk.Button(btn_frame, text="Remove", command=delete_recording)
btn_delete.grid(row=0, column=3, padx=2, pady=2, sticky="ew")

ia_frame = tk.LabelFrame(main_frame, text="Control by AI")
ia_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
ia_frame.grid_columnconfigure((0,1), weight=1)

entry_ia_text = tk.Entry(ia_frame)
entry_ia_text.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

btn_ia_text = tk.Button(ia_frame, text="Send Text", command=send_text_command)
btn_ia_text.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

btn_ia_audio = tk.Button(ia_frame, text="Voice Recording")
btn_ia_audio.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
btn_ia_audio.bind("<ButtonPress-1>", lambda e: start_audio_recording())
btn_ia_audio.bind("<ButtonRelease-1>", lambda e: stop_audio_recording())

buttons_frame = tk.Frame(root)
buttons_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
buttons_frame.grid_columnconfigure((0,1,2), weight=1)

btn_zero = tk.Button(buttons_frame, text="Initial Position", command=initialize_servos)
btn_zero.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

btn_play = tk.Button(buttons_frame, text="Play Recording", command=replay_movements)
btn_play.grid(row=0, column=1, padx=5, pady=5, sticky="ew")


# Configuration of the 3D mathematical visualization.
fig = plt.figure(figsize=(6, 5))
ax = fig.add_subplot(111, projection='3d')
ax.set_xlim([-200, 200])
ax.set_ylim([-200, 200])
ax.set_zlim([0, 300])
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.view_init(elev=25, azim=45)

# Parameters of the arm in the visualization, length in mm.
LINK_LENGTHS = {
    'base': 0,
    'shoulder': 50,
    'elbow': 120,
    'wrist': 100,
    'gripper': 80 
}


toolbar_frame = tk.Frame(root)
toolbar_frame.grid(row=2, column=1, sticky="ew", padx=5, pady=(0,5))


canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=1, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)

toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
toolbar.update()
toolbar.pack_forget()
toolbar.grid(row=2, column=1, sticky="ew", padx=5)

ani = FuncAnimation(fig, lambda i: update_arm(), interval=200)


# Initialize plot elements
lines = []
points = []
texts = []
for _ in range(5):
    gripper_lines = []
    for _ in range(2):
        line, = ax.plot([], [], [], lw=4, color='blue')
        gripper_lines.append(line)
    line, = ax.plot([], [], [], lw=4, marker='o', markersize=8)
    point = ax.plot([], [], [], 'ro', markersize=10)[0]
    text = ax.text(0, 0, 0, '', fontsize=10)
    lines.append(line)
    points.append(point)
    texts.append(text)


def update_arm():
    # Shows the position that the arm should have, depending on the values of the servos. It doesn't return anything.
    angles = [servo_positions[id] - GRAPHIC_ZERO[id] for id in reversed(servo_ids)]
    gripper_angle, wrist_angle, elbow_angle, shoulder_angle, base_angle = angles

    def rotate_z(theta):
        return np.array([
            [np.cos(theta), -np.sin(theta), 0],
            [np.sin(theta), np.cos(theta), 0],
            [0, 0, 1]
        ])

    def rotate_y(theta):
        return np.array([
            [np.cos(theta), 0, np.sin(theta)],
            [0, 1, 0],
            [-np.sin(theta), 0, np.cos(theta)]
        ])

    T_base = rotate_z(np.radians(base_angle))
    # Base
    p0 = np.array([0, 0, 0])
    R_base = rotate_z(np.radians(base_angle))

    # Shoulder
    R_shoulder = rotate_y(np.radians(shoulder_angle))
    p1 = p0 + R_base @ np.array([0, 0, LINK_LENGTHS['shoulder']])

    # Elbow
    R_elbow = rotate_y(np.radians(elbow_angle))
    p2 = p1 + R_base @ R_shoulder @ np.array([0, 0, LINK_LENGTHS['elbow']])

    # Wrist
    R_wrist = rotate_y(np.radians(wrist_angle))
    p3 = p2 + R_base @ R_shoulder @ R_elbow @ np.array([0, 0, LINK_LENGTHS['wrist']])

    # Gripper
    R_gripper = rotate_z(np.radians(gripper_angle))
    p4 = p3 + R_base @ R_shoulder @ R_elbow @ R_wrist @ np.array([0, 0, LINK_LENGTHS['gripper']])


    # Actualizes lines and points
    segments = [
        (p0, p1),
        (p1, p2),
        (p2, p3),
        (p3, p4)
    ]

    for i, (start, end) in enumerate(segments):
        x = [start[0], end[0]]
        y = [start[1], end[1]]
        z = [start[2], end[2]]
        lines[i].set_data(x, y)
        lines[i].set_3d_properties(z)
        points[i+1].set_data([end[0]], [end[1]])
        points[i+1].set_3d_properties([end[2]])
        texts[i+1].set_position((end[0], end[1]))
        texts[i+1].set_text(f"{servo_labels[i+1]}")
        texts[i+1].set_3d_properties(end[2]+10, zdir='x')

    points[0].set_data([p0[0]], [p0[1]])
    points[0].set_3d_properties([p0[2]])
    texts[0].set_position((p0[0], p0[1]))
    texts[0].set_text("Base")
    texts[0].set_3d_properties(p0[2]+10, zdir='x')

    v = p4 - p3
    norm_v = np.linalg.norm(v)
    if norm_v < 1e-6:
        dir3d = np.array([0, 0, 1])
    else:
        dir3d = v / norm_v

    ez = np.array([0.0, 0.0, 1.0])
    perp = np.cross(dir3d, ez)
    perp_norm = np.linalg.norm(perp)
    if perp_norm < 1e-6:
        perp = np.array([1.0, 0.0, 0.0])
    else:
        perp = perp / perp_norm


    sep_max = 20        # max separation
    sep = (gripper_angle / 180.0) * sep_max
    bar_len = 25        # length of the bar


    start1 = p4 +  perp * ( sep/2 )
    end1   = start1 + dir3d * bar_len
    start2 = p4 -  perp * ( sep/2 )
    end2   = start2 + dir3d * bar_len

    # Actualizes the lines of the gripper
    gripper_lines[0].set_data(       [start1[0], end1[0]], [start1[1], end1[1]] )
    gripper_lines[0].set_3d_properties([start1[2], end1[2]])
    gripper_lines[1].set_data(       [start2[0], end2[0]], [start2[1], end2[1]] )
    gripper_lines[1].set_3d_properties([start2[2], end2[2]])


    fig.canvas.draw_idle()


btn_exit = tk.Button(buttons_frame, text="Sortir", command=root.quit)
btn_exit.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

root.mainloop()