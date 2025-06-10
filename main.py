from machine import Pin, PWM
import sys

servo_freq= 50
servo_pins= {
    "S1": PWM(Pin(25)),
    "S2": PWM(Pin(17)),
    "S3": PWM(Pin(16)),
    "S4": PWM(Pin(27)),
    "S5": PWM(Pin(14))
} # You've got to define the Pins you'll use

for pwm in servo_pins.values():
    pwm.freq(servo_freq)

def angle_to_duty(angle):
    # Transforms an angle (between 0 and 180) to a value that the servo can read. min_duty and max_duty depend on every type of servo, so adjust them as needed. Returns the value.
    min_duty= 52
    max_duty= 105
    duty_range= max_duty-min_duty
    mapped= int(min_duty + (angle/180) * duty_range)
    return mapped

def set_servo_position(servo_id, angle):
    # Sets the servo into the position specified. It doesn't return anything.
    if servo_id not in servo_pins:
        return
    duty_val= angle_to_duty(angle)
    servo_pins[servo_id].duty(duty_val)

def parse_command(cmd):
    # Takes the command from the terminal and actives the set_servo_position() functoin. It doesn't return anything.
    parts= cmd.strip().split(":")
    if len(parts) != 2:
        return
    servo_id, angle_str= parts
    try:
        angle= int(angle_str)
        if 0 <= angle <= 180:
            set_servo_position(servo_id, angle)
    except Exception as e:
        print(f"Error mentres s'intentava posar el servo {servo_id} a {angle} graus.\nError: {e}.")
    
while True:
    line= sys.stdin.readline() # Every time there's a command, executes the code below.
    if line:
        parse_command(line)