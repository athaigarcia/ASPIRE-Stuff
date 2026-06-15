import cv2
import numpy as np

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Convert to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define the range for the color BLUE in HSV space
    # [Hue, Saturation, Value]
    # In OpenCV, Hue goes from 0-179 instead of 0-360. Blue sits around 100-130.
    lower_blue = np.array([100, 100, 50])
    upper_blue = np.array([130, 255, 255])

    # Create a mask that ONLY keeps pixels inside our blue range
    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Find the outlines of the blue objects
    contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        # Ignore tiny specks of noise
        if cv2.contourArea(contour) > 500:
            x, y, w, h = cv2.boundingRect(contour)
            # Draw a blue rectangle around the blue object
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(frame, "Blue Object Detected", (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    cv2.imshow("Object Tracker", frame)
    cv2.imshow("Blue Mask Only", blue_mask)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()