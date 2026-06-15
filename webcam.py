import cv2

# 1. Initialize the webcam. 
# '0' is usually the built-in webcam. If you have an external USB cam, try 1 or 2.
cap = cv2.VideoCapture(0)

# Check if the webcam opened correctly
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

print("Camera opened successfully! Press 'q' on your keyboard to exit.")

while True:
    # 2. Capture frame-by-frame
    # 'ret' is a boolean (True/False) indicating if the frame was read successfully
    # 'frame' is the actual image array
    ret, frame = cap.read()

    if not ret:
        print("Error: Can't receive frame. Exiting...")
        break

    # 3. Display the resulting frame in a window named 'Webcam Feed'
    cv2.imshow('Webcam Feed', frame)

    # 4. Break the loop if the user presses the 'q' key
    # cv2.waitKey(1) waits for 1 millisecond for a key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 5. When everything is done, release the camera and close all windows
cap.release()
cv2.destroyAllWindows()