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

    # 3b. White/overexposed core mask — catches the blown-out center of a bright LED
    # (very high value, near-zero saturation means the color washed out to white)
    lower_white = np.array([0, 0, 220])
    upper_white = np.array([180, 40, 255])
    white_mask = cv2.inRange(hsv, lower_white, upper_white)

    # 4. Combine all three masks — colored glare OR white core both count
    combined_mask = cv2.bitwise_or(green_mask, blue_mask)
    combined_mask = cv2.bitwise_or(combined_mask, white_mask)
    
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
            
            # Count colored pixels in the bounding box region from each color mask.
            # This works even when the center is blown-out white — the glare ring
            # around it still carries the original color.
            roi_green = green_mask[y:y + h, x:x + w]
            roi_blue = blue_mask[y:y + h, x:x + w]
            green_pixels = cv2.countNonZero(roi_green)
            blue_pixels = cv2.countNonZero(roi_blue)

            if green_pixels > blue_pixels and green_pixels > 0:
                green_led_on = True
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, "GREEN LED", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            elif blue_pixels > green_pixels and blue_pixels > 0:
                blue_led_on = True
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

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    # Exit if either window is closed via the X button
    if (cv2.getWindowProperty("Dual LED Detector", cv2.WND_PROP_VISIBLE) < 1 or
            cv2.getWindowProperty("Combined Mask (What OpenCV Sees)", cv2.WND_PROP_VISIBLE) < 1):
        break

cap.release()
cv2.destroyAllWindows()