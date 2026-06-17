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
    lower_bright_green = np.array([35, 100, 200])
    upper_bright_green = np.array([85, 255, 255])
    green_mask = cv2.inRange(hsv, lower_bright_green, upper_bright_green)

    # 3. Define strict boundaries for BRIGHT BLUE
    # Blue hue usually sits between 100 and 130
    lower_bright_blue = np.array([100, 100, 200])
    upper_bright_blue = np.array([130, 255, 255])
    blue_mask = cv2.inRange(hsv, lower_bright_blue, upper_bright_blue)

    # 4. Combine both masks using bitwise OR (detects green OR blue pixels)
    combined_mask = cv2.bitwise_or(green_mask, blue_mask)
    
    # 5. Clean up small background noise
    kernel = np.ones((5, 5), np.uint8)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)

    # 6. Find contours on the combined map
    contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    green_led_on = False
    blue_led_on = False

    for contour in contours:
        if cv2.contourArea(contour) > 50:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Figure out WHICH LED was found by checking the pixel color in the center of the box
            # We look at the original 'hsv' frame at the center coordinate of this bounding box
            center_x = x + (w // 2)
            center_y = y + (h // 2)
            
            # Grab the Hue value of that center pixel
            # hsv[y, x] format because images are stored as rows (y) then columns (x)
            pixel_hue = hsv[center_y, center_x][0]

            # Identify if the hue belongs to Green (35-85) or Blue (100-130)
            if 35 <= pixel_hue <= 85:
                green_led_on = True
                # Draw a Green box (0, 255, 0)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, "GREEN LED", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
            elif 100 <= pixel_hue <= 130:
                blue_led_on = True
                # Draw a Blue box (255, 0, 0)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(frame, "BLUE LED", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    # 7. Draw an on-screen dashboard showing the real-time status of both
    # Green status
    g_text, g_color = ("GREEN: ON", (0, 255, 0)) if green_led_on else ("GREEN: OFF", (0, 0, 180))
    cv2.putText(frame, g_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, g_color, 2)
    
    # Blue status
    b_text, b_color = ("BLUE: ON", (255, 0, 0)) if blue_led_on else ("BLUE: OFF", (0, 0, 180))
    cv2.putText(frame, b_text, (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, b_color, 2)

    # Show the windows
    cv2.imshow("Dual LED Detector", frame)
    cv2.imshow("Combined Mask (What OpenCV Sees)", combined_mask)

    if cv2.waitKey(1) & 0xFF == ord('q'):
    if key == ord('q'):
        break
    # Exit if either window is closed via the X button
    if (cv2.getWindowProperty("Dual LED Detector", cv2.WND_PROP_VISIBLE) < 1 or
            cv2.getWindowProperty("Combined Mask (What OpenCV Sees)", cv2.WND_PROP_VISIBLE) < 1):
        break

cap.release()
cv2.destroyAllWindows()