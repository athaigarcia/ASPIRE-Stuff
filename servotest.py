import sys
import time
from pymata4 import pymata4

# Define Pins
SERVO_1_PIN = 9  # Controlled by A / D
SERVO_2_PIN = 10 # Controlled by W / S

# Calibrated pulse limits for MS18 servos
MIN_PULSE = 544
MAX_PULSE = 2400

# Step size: How many degrees the servo moves per command
STEP = 5 

# Initialize angles at the midpoint
angle_1 = 90
angle_2 = 90

# Initialize Arduino
board = pymata4.Pymata4()

try:
    print("Initializing MS18 servos...")
    board.set_pin_mode_servo(SERVO_1_PIN, min_pulse=MIN_PULSE, max_pulse=MAX_PULSE)
    board.set_pin_mode_servo(SERVO_2_PIN, min_pulse=MIN_PULSE, max_pulse=MAX_PULSE)
    time.sleep(1)

    # Move to initial 90-degree positions
    board.servo_write(SERVO_1_PIN, angle_1)
    board.servo_write(SERVO_2_PIN, angle_2)

    print("\n--- WASD Controls (Press Enter after typing) ---")
    print("Servo 1 (Pin 9)  -> A (Left) / D (Right)")
    print("Servo 2 (Pin 10) -> W (Up)   / S (Down)")
    print("Exit             -> Q")
    print("------------------------------------------------")

    while True:
        # Display current positions and prompt for input
        print(f"\n[Current Position] Servo 1: {angle_1}° | Servo 2: {angle_2}°")
        user_input = input("Enter command(s) and press Enter: ").lower().strip()

        # Check for quit command
        if 'q' in user_input:
            print("Exiting...")
            break

        # Process every character typed before the user hit Enter
        for char in user_input:
            if char == 'd':
                angle_1 = max(0, angle_1 - STEP)
                board.servo_write(SERVO_1_PIN, angle_1)
            elif char == 'a':
                angle_1 = min(180, angle_1 + STEP)
                board.servo_write(SERVO_1_PIN, angle_1)
            elif char == 's':
                angle_2 = max(0, angle_2 - STEP)
                board.servo_write(SERVO_2_PIN, angle_2)
            elif char == 'w':
                angle_2 = min(180, angle_2 + STEP)
                board.servo_write(SERVO_2_PIN, angle_2)

except KeyboardInterrupt:
    print("\nScript stopped by user.")

finally:
    print("\nClosing Arduino connection...")
    board.shutdown()