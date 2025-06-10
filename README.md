# Robotic-Arm-Control-with-Python,-AI-and-Visualization
This project allows you to control a 5-servo robotic arm using Python and an ESP32 (STEAMakers, MicroPython). Includes a Tkinter GUI, real-time manual control, sequence recording/playback, voice and text command execution, and a basic 3D simulation to visualize movements.

This project began as an attempt to improve communication between a controlling app and a robotic arm. Initially, it was a simple Bluetooth communication between an App Inventor app and an ESP32 STEAMakers board programmed with ArduinoBlocks. The project now includes all these features:

- Manual control with sliders
- Recording of sequences (considering the time) of moves, saving of the sequences (locally) and playback
-  voice and text command execution (example: “set the elbow to 120º”), with support for multiple commands at once
- Visualization of a simulation of the arm in 3D 

About the AI:

The project is designed to use local AI with Ollama (for example, I've used the models llama3, llama3.2:1b and mistral), or use free and online ones, as command-xlarge. Although they work sometimes, they're not very smart, as they're free or optimized to run them locally. So they might give invalid or unexpected answers, but the code is designed to handle them.

The code in the computer communicates with the ESP32 through the computer ports (in my case, COM3. Change that and the baudrate if needed). The communication is created with pyserial, with the computer writing commands with the form ("S1/S2/...S5:0-180º", ex: "S3:120") and the microcontroller reading and processing them. Although it's designed for that, the code works perfectly without a microcontroller, and the graphic representation shows you what you're doing.

All you've got to change before using the project:

- Serial port and Baudrate (in this case, "COM3" and 115200)
- GRAPHIC_ZERO and INIT_POSITIONS, with the best values to your own arm. You can execute the code, and later start improving the values.
- Servo labels if English isn't your language
- servo_freq and min_duty / max_duty in angle_to_duty, depending on the characteristics of your servos.
- The pins where you connect your servos
- API key Groq and API key cohere. Obviously, you’ll need to use your own — I’m not giving you mine.
- The language translation when talking to the AI, if you change the language
- The AI model used (change to any model you want, and change between the functions ask() and ask_local())
- Localhost when using Ollama
- The prompt for the AI. I tried various different prompts, but all give errors. This is the one with less errors I've seen, so don't change much its structure. Also, the AI is really slow sometimes, so be patient. If an error occurs, it's likely because the AI returned a generic or vague answer like "Okay, I'll reply..." instead of a proper command list — not because the system is broken.
I honestly believe that the AI isn't really functional, but it's impressive to be able to connect an AI to a project like this. If you paid some premium AI, I strongly recommend you to connect its API to this project instead the options I'm giving, because once you've got an intelligent AI you can take this project wherever you want.

All generated audio files and logs are saved in folders created automatically inside the project’s root directory. You don’t need to set absolute paths — the script checks if these folders exist and creates them if needed, using ensure_folder_exists(folder_name). The audio of the user is not saved.

This project is, in my opinion, really interesting in order to learn how to establish communication between hardware and software, in a more sophisticated way than ArduinoBlocks and App Inventor, for example. And an impressive example of how far a simple project like a robotic arm can go. The next step could be connecting the arm to a camera, with openCV. For example, it could detect colors, and depending on the color detected activate one sequence or another. You can do whatever you want, but this is a good base to start from. I also recommend, if you're looking for something simpler and easier to introduce, for example, in a class, to take a look at my other robotic arm project, which is essentially the same, but without the AI and graphical simulation.

Lastly, if you're searching for introducing AI in any of your projects, the script (ModeloAIBrazoRobotico) is useful, despite its name, it can be used in any other project, because it allows you to:

- Record audio, translate it and pass it to text
- Pass text to voice, talk
- Ask a local AI (ollama) or an online one, with different free models available (at least when I did the project, it's possible that in the future these models won't be available, or that there'll be better options)
