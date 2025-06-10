import os
import tempfile
import wave
from gtts import gTTS
import pygame
import pyaudio
import keyboard
import cohere
from time import sleep
import requests
from groq import Groq
import ast
import threading
import json
import ast


NAME_TO_ID = {
    "base": "S5",
    "shoulder": "S4",
    "elbow": "S3",
    "wrist": "S2",
    "gripper": "S1",
    "clamp": "S1" 
}

def ensure_audio_folder(folder= "ai_audios"):
    # Checks if there's an existing folder to save the audios of the AI. If not, then creates one. Returns the path.
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), folder)
    os.makedirs(path, exist_ok=True)
    return path

def ensure_sequence_file(file= "arm_sequences.json"):
    # Checks if there's an existing file to save the sequences of moves. If not, then creates one. Returns the path.
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file)
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f)  # Start with empty dict
    return path

def ensure_log_file(file= "ai_register.txt"):
    # Checks if there's an existing file to save the logs of the AI. If not, then creates one. Returns the path.
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file)
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write("")  # Create empty log
    return path

Audios_Folder= ensure_audio_folder()
file_path= ensure_log_file()

def play_audio_async(audio_path):
    if os.path.exists(audio_path):
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            sleep(0.1)
        pygame.mixer.music.stop()
    else:
        print("The path doesn't exist.")


def translate(text, language_from= "es", language_to= "en"):
    # Translate from one language to another. Returns the transcription.
    url = "https://api.mymemory.translated.net/get"
    params = {
        "q": text,
        "langpair": f"{language_from}|{language_to}"  # Traduces from Spanish (es) to English (en). Can be changed.
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raises an error if the traduction fails.
        data = response.json()
        traduction = data["responseData"]["translatedText"]
        return traduction
    except Exception as e:
        print(f"Error while translating: {str(e)}")
        return None

pygame.mixer.init()
client= Groq(api_key="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") # You must introduce your own API keys.
api_key_llm = "1xZvuPLYfZeNnYQxk365ygyMYjUDK3O8vzs5fhgW"
co = cohere.Client(api_key_llm)

def speak(text, language= "en"):
    # Says loudly the text given. The language can be changed. It doesn't return anything.
    files = os.listdir(Audios_Folder)
    nameFile = "Record" + str(len(files)) + ".mp3"
    audio_path = os.path.join(Audios_Folder, nameFile)
    tts = gTTS(text, lang= language) # Possible values: 'es', 'en', 'ca', 'fr', 'de', etc.
    tts.save(audio_path)
    
    audio_thread = threading.Thread(target=play_audio_async, args=(audio_path,))
    audio_thread.daemon = True  # The voice will shut down if the main program stops.
    audio_thread.start()


def record_audio_ins(sample_frequency=1600, canals=1, fragment=1024):
    # Record the audio while pressing "INS", and saves it when releasing the button. Return the frames and the sample_frequency.
    p= pyaudio.PyAudio()
    stream= p.open(
        format=pyaudio.paInt16,
        channels=canals,
        rate=sample_frequency,
        input=True,
        frames_per_buffer=fragment)
    print("Press and hold INS to record")
    frames= []
    keyboard.wait("insert")
    print("Recording...")
    while keyboard.is_pressed("insert"):
        data= stream.read(fragment)
        frames.append(data)
    print("Recording finished.")
    stream.stop_stream()
    stream.close()
    p.terminate()
    return frames, sample_frequency

def save_record(frames, sample_frequency):
    # Takes the returned variables of the record_audio_ins() function and saves them as an audio. Returns the name of the audio.
    with tempfile.NamedTemporaryFile(suffix= ".wav", delete= False) as audio_temp:
        wf= wave.open(audio_temp.name, mode= "wb")
        wf.setnchannels(1)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
        wf.setframerate(sample_frequency)
        wf.writeframes(b"".join(frames))
        wf.close()
    return audio_temp.name

def transcribe_audio(Path, language= "en"):
    # Passes the audio to text, returns the transcription.
    try:
        with open(Path, "rb") as file:
            transcription= client.audio.transcriptions.create(
            file= (os.path.basename(Path), file.read()),
            model= "whisper-large-v3", # May be changed
            prompt= "The audio is from someone commanding a robot arm with servos and degrees",
            response_format= "text",
            language=language) # You can change the language
        return transcription
    except Exception as e:
        print(f"An error took place: {str(e)}")
        return None
    
def ask(task, maxTokens= 250):
    # Ask an online AI. Returns the answer.
    response = co.generate(
        model='command-xlarge',  # You can change the model
        prompt=task,
        max_tokens= maxTokens)
    return response.generations[0].text

def register_info(user_text, ai_answer):
    # Registers the AI answer in the file ai_register.txt
    content = f"Input: {user_text}  -->  -->  Response: {ai_answer}\n\n"
    try:
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(content)
        print("Register added correctly.")
        return ai_answer
    except Exception as e:
        print(f"Error while registering the ai response: {str(e)}")

def change_command_form(english_name):
    return NAME_TO_ID.get(english_name.lower(), "S1")


def main_write(user_text):
    # Ask a local AI and returns it answer. You can change the AI to online by changing the function ask_local() --> ask()
    answer= ask_local(translate(user_text) + ", Generate a Python list containing tuples with servo positions (in degrees only) and servo names. Format each tuple as (ServoPositionDegrees, ServoName). Use these English servo names: base, shoulder, elbow, wrist, gripper. Extract only the position values that appear in this message. If you cannot find any position values, return an empty list []. return ONLY the list, don't say nothing more, if you give any background, the app breakes.")
    register_info(user_text, answer)
    answer= main(answer)
    if answer:
        return answer


def main_record():
    # Records, translates, and asks a local AI. Returns it answer. You can change the AI to online by changing the function ask_local() --> ask()
    frames, sample_frequency= record_audio_ins()
    archivo_audio_temp= save_record(frames, sample_frequency)
    print("Transcribiendo...")
    transcription= transcribe_audio(archivo_audio_temp)
    if transcription:
        answer= ask_local(translate(transcription) + ", Generate a Python list containing tuples with servo positions (in degrees only) and servo names. Format each tuple as (ServoPositionDegrees, ServoName). Use these English servo names: base, shoulder, elbow, wrist, gripper. Extract only the position values that appear in this message, never invent information, and if you cannot find any valid information, return an empty list []. return ONLY the list, if you send text, the app won't work.")
        register_info(transcription, answer)
        return main(answer)
    else:
        print("The transcription failed")


def main(ai_answer):
    # Checks if the answer of the AI is valid, and transform an input like "[(S1:50), (S3:130)]" to an output like [(S1:50), (S3:130)]
    try:
        answer = []
        ai_answer = ast.literal_eval(ai_answer)
        print("AI Answer:", ai_answer)
        
        if not isinstance(ai_answer, list):
            print("ERROR: AI response isn't a list")
            return False
            
        for item in ai_answer:
            if not isinstance(item, (tuple, list)) or len(item) != 2:
                print(f"Invalid item: {item}")
                return False
                
            pos_grads, nom_servo = item
            
            try:
                pos_grads = int(pos_grads)
            except (ValueError, TypeError):
                print(f"Invalid value: {pos_grads}")
                return False
                
            nom_servo = nom_servo.lower()
            
            # Validar nombre y rango
            if (nom_servo not in NAME_TO_ID or 
                not (0 <= pos_grads <= 180)):
                print(f"Error: {nom_servo} o {pos_grads}° no valids")
                return False
                
            answer.append((nom_servo, pos_grads))
            
        return answer if answer else False
        
    except SyntaxError as e:
        print(f"Error in the AI response: {e}")
        return False


def ask_local(task):
    # Ask a local AI (with Ollama) and returns its answer.
    url = "http://localhost:11434/api/generate" # Add your lokalhost
    data = {
        "model": "mistral",  # Examples (you've got to install Ollama and the models): llama3, llama3.2:1b, mistral
        "prompt": task,
        "stream": False
    }
    # Hacer la solicitud
    response = requests.post(url, json=data)
    return response.json()["response"]