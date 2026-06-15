import cv2
import numpy as np

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 1. Convert the frame to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 2. Define strict boundaries for BRIGHT GREEN
    # Hue range for green is usually between 35 and 85.
    # Saturation is kept high (100+) so it ignores washed-out grays/whites.
    # Value (Brightness) is set very high (200+) so it only triggers when it glows.
    lower_bright_green = np.array([35, 100, 200])
    upper_bright_green = np.array([85, 255, 255])

    # 3. Create the mask
    green_mask = cv2.inRange(hsv, lower_bright_green, upper_bright_green)
    
    # 4. Clean up the mask using "morphological opening" 
    # This removes tiny, flickering random pixels (noise) that might look green for a split second
    kernel = np.ones((5, 5), np.uint8)
    green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel)

    # 5. Find contours of the bright green shapes
    contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    led_is_on = False

    for contour in contours:
        # LEDs are small, so a minimum area of 50 or 100 pixels is plenty.
        if cv2.contourArea(contour) > 50:
            led_is_on = True
            
            # Get bounding box coordinates
            x, y, w, h = cv2.boundingRect(contour)
            
            # Draw a bright green box around the detected LED
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # 6. Visual indicator on the screen showing the status of the LED
    if led_is_on:
        cv2.putText(frame, "LED STATUS: ON", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
    else:
        cv2.putText(frame, "LED STATUS: OFF", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

    # Show the results
    cv2.imshow("LED Detector", frame)
    cv2.imshow("Green Mask (What OpenCV Sees)", green_mask)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()