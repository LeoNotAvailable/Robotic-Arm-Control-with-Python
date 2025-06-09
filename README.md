# Robotic-Arm-Control-with-Python
Control a 5-servo robotic arm using Python and an ESP32 (STEAMakers, MicroPython). Includes a Tkinter GUI, real-time manual control, sequence recording/playback, voice and text command execution, and a basic simulation to visualize movements.

This project was started in order to imrpove the comunication between the app that control the robotic arm, and the arm itself. As, at an initial point, it started as a simple comunication via bluetooth between an app created with app inventor and the code, uploaded to an ESP23 STEAMakers, with ArduinoBlocks. Finally, the project ended with all these funcitionalities:

- Manual control with sliders
- Recording of sequences (considering the time) of moves, saving of the sequences (in local) and reproduction of them
- Simple voice and text-controlled command execution (Example: set the elbow to 120º), allows multiple orders at once.
- Visualization of a simulation of the arm in 3 

About the AI:

The project is designed to use local AI with ollama (for example, I've used the models llama3, llama3.2:1b and mistral), or use free and online ones, as command-xlarge. Although they work sometimes, they're not very smart, as they're free or optimized in order to use them inside a computer. So they might give wrong or unprocessable answers, but the code is designed in order to manage them. Also, the AI is prepared to work in Spanish and provide answers in English, but it's as simple as change (or directly translate) the promts given to them, in the function ask() or ask_local(), in the script model_ai_robotic_arm.py .
