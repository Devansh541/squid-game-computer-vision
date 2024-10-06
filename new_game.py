import random
import cv2
import os
import numpy as np
import time
import string

# Load the images from the folder
folderPath = 'frames'
mylist = os.listdir(folderPath)
graphic = [cv2.imread(f'{folderPath}/{imPath}') for imPath in mylist]
green = graphic[0]  # Green light image
red = graphic[1]  # Red light image
kill = graphic[2]  # Kill screen image
winner = graphic[3]  # Winner screen image
intro = graphic[4]  # Intro screen image

# Display intro until 's' is pressed to start the game
cv2.imshow('Squid Game', cv2.resize(intro, (0, 0), fx=0.69, fy=0.69))
print("Intro displayed, waiting for 's' to start.")
while True:
    key = cv2.waitKey(1) & 0xFF
    if key == ord('s'):  # Press 's' to start the game
        print("'s' pressed, starting the game.")
        break
    elif key == ord('q'):  # Press 'q' to quit at intro
        print("'q' pressed, exiting the game from intro.")
        cv2.destroyAllWindows()
        exit()

# Game setup
TIMER_MAX = 10  # Total time for the game
TIMER = TIMER_MAX
green_time = 1 # Random green light duration
red_time = 1  # Random red light duration
light_switch_time = green_time  # Start with green light
isgreen = True  # Game starts with green light
light_change_time = time.time()  # Track time for switching lights

font = cv2.FONT_HERSHEY_SIMPLEX
cap = cv2.VideoCapture(0)

# Verify if the camera is initialized properly
if not cap.isOpened():
    print("Error: Camera not initialized properly.")
    exit()

print("Camera initialized successfully.")
frameHeight = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
frameWidth = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
print(f"Frame size: Width {frameWidth}, Height {frameHeight}")

win = False
maxMove = 6500000  # Threshold for detecting significant movement
movement_detected = False
ref_frame = None  # To store the reference frame during green light

# Generate a sequence of random letters excluding 'q'
sequence_length = 5  # You can change the length of the sequence
possible_keys = list(string.ascii_lowercase.replace('q', ''))  # Exclude 'q'
key_sequence = random.choices(possible_keys, k=sequence_length)
print(f"Key sequence generated: {key_sequence}")

# Function to display the sequence on the screen
def display_sequence(showFrame, sequence):
    sequence_text = 'Press: ' + ' '.join(sequence)
    cv2.putText(showFrame, sequence_text, (50, 100), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

# Player input tracking
current_key_index = 0
prev_time = time.time()  # Time for updating the timer
showFrame = cv2.resize(green, (0, 0), fx=0.69, fy=0.69)  # Start with green light

# Main game loop
while cap.isOpened() and TIMER >= 0:
    ret, frame = cap.read()

    # Check if frame was successfully read
    if not ret:
        print("Error: Failed to capture frame from camera. Exiting...")
        break

    # Handle light switching between green and red
    current_time = time.time()
    if current_time - light_change_time >= light_switch_time:
        if isgreen:
            isgreen = False
            light_switch_time = red_time  # Switch to red for the next cycle
            showFrame = cv2.resize(red, (0, 0), fx=0.69, fy=0.69)  # Show red light
            print("Switched to red light.")

            # Store the reference frame for movement detection
            ref_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            ref_frame = cv2.GaussianBlur(ref_frame, (21, 21), 0)  # Apply blur to smooth out noise

        else:
            isgreen = True
            light_switch_time = green_time  # Switch to green for the next cycle
            showFrame = cv2.resize(green, (0, 0), fx=0.69, fy=0.69)  # Show green light
            print("Switched to green light.")
        light_change_time = current_time  # Reset light change timer

    # Timer logic
    if current_time - prev_time >= 1:  # Decrement timer every second
        TIMER -= 1
        prev_time = current_time
        print(f"Timer updated: {TIMER}")

    # Clear previous timer text by refreshing the frame
    # Redraw the appropriate background frame based on the light
    showFrame = cv2.resize(green if isgreen else red, (0, 0), fx=0.69, fy=0.69)

    # Now show the timer and key sequence
    display_sequence(showFrame, key_sequence)
    cv2.putText(showFrame, str(TIMER), (50, 50), font, 1, 
                (0, int(255 * (TIMER) / TIMER_MAX), int(255 * (TIMER_MAX - TIMER) / TIMER_MAX)), 4, cv2.LINE_AA)

    key_pressed = cv2.waitKey(10) & 0xFF

    if key_pressed == ord('q'):
        # Allow 'q' to quit the game
        print("'q' pressed, exiting the game.")
        break

    # Red light logic: If any key is pressed during red light, the player loses
    if not isgreen and key_pressed != 255:  # Check if any key is pressed during red light
        print("Key pressed during red light! Player loses.")
        break  # End the game if a key is pressed during red light

    # Green light logic: player can press keys
    if isgreen:
        if current_key_index < sequence_length:
            expected_key = ord(key_sequence[current_key_index])
            if key_pressed == expected_key:
                current_key_index += 1  # Move to the next key in the sequence
                print(f"Correct key pressed: {chr(expected_key)}, moving to next key.")
            elif key_pressed != 255:  # Ignore if no key is pressed
                current_key_index = 0  # Reset if a wrong key is pressed
                print(f"Wrong key pressed: {chr(key_pressed)}. Resetting sequence.")
        else:
            win = True
            print("Sequence completed, player won!")
            break  # Exit loop on win

    # Red light logic: movement detection
    else:
        if ref_frame is not None:  # Ensure the reference frame is captured
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)  # Apply blur to smooth out noise
            frame_delta = cv2.absdiff(ref_frame, gray)  # Compare the current frame to the reference
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            movement = np.sum(thresh)  # Calculate the amount of change

            # If movement is above threshold, the player loses
            if movement > maxMove:
                print("Movement detected during red light! Player loses.")
                movement_detected = True
                break

    # Show the camera feed
    camShow = cv2.resize(frame, (0, 0), fx=0.4, fy=0.4)
    camH, camW = camShow.shape[0], camShow.shape[1]
    showFrame[0:camH, -camW:] = camShow

    cv2.imshow('Squid Game', showFrame)

# After game ends
cap.release()
cv2.destroyAllWindows()

if win:
    # Display win screen
    print("Displaying win screen.")
    cv2.imshow('Squid Game', cv2.resize(winner, (0, 0), fx=0.69, fy=0.69))
    cv2.waitKey(0)
elif movement_detected:
    # Display lose screen for movement detection
    print("Displaying lose screen (movement detected).")
    for _ in range(10):
        cv2.imshow('Squid Game', cv2.resize(kill, (0, 0), fx=0.69, fy=0.69))
    cv2.waitKey(0)
else:
    # Display lose screen for incorrect sequence
    print("Displaying lose screen (incorrect key press).")
    for _ in range(10):
        cv2.imshow('Squid Game', cv2.resize(kill, (0, 0), fx=0.69, fy=0.69))
    cv2.waitKey(0)

cv2.destroyAllWindows()
