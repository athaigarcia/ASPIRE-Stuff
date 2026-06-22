import cv2
import numpy as np

cap = cv2.VideoCapture(0)


def nothing(x):
    pass


# Sensitivity knobs — adjust live while the program runs, no code edits needed.
# OpenCV trackbar windows can't scroll, so size it tall enough up front to fit
# all sliders (it's still resizable by dragging if you add more later).
cv2.namedWindow("Controls", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Controls", 400, 450)

cv2.createTrackbar("Red On", "Controls", 1, 1, nothing)
cv2.createTrackbar("Red R Min", "Controls", 95, 255, nothing)
cv2.createTrackbar("Red GB Max", "Controls", 255, 255, nothing)

cv2.createTrackbar("White On", "Controls", 1, 1, nothing)
cv2.createTrackbar("White Min", "Controls", 28, 255, nothing)
cv2.createTrackbar("Red Size Min", "Controls", 9, 100, nothing)
cv2.createTrackbar("Red Size Max", "Controls", 250, 400, nothing)
cv2.createTrackbar("White Area Min", "Controls", 20, 200, nothing)
cv2.createTrackbar("White Area Max", "Controls", 200, 1000, nothing)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 1. Define boundaries for BRIGHT RED (frame is BGR, so B/G stay low, R goes high)
    red_on = cv2.getTrackbarPos("Red On", "Controls")
    red_r_min = cv2.getTrackbarPos("Red R Min", "Controls")
    red_gb_max = cv2.getTrackbarPos("Red GB Max", "Controls")
    lower_bright_red = np.array([0, 0, red_r_min])
    upper_bright_red = np.array([red_gb_max, red_gb_max, 255])
    red_mask = cv2.inRange(frame, lower_bright_red, upper_bright_red) if red_on else np.zeros(frame.shape[:2], dtype=np.uint8)

    # 3. White/overexposed core mask — catches the blown-out center of a bright LED.
    # Uses overall brightness rather than requiring every B/G/R channel to
    # individually saturate, since a clipped red channel can outpace green/blue.
    white_on = cv2.getTrackbarPos("White On", "Controls")
    white_min = cv2.getTrackbarPos("White Min", "Controls")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    white_mask = cv2.inRange(gray, white_min, 255) if white_on else np.zeros(frame.shape[:2], dtype=np.uint8)
    redsize_min = cv2.getTrackbarPos("Red Size Min", "Controls")
    redsize_max = cv2.getTrackbarPos("Red Size Max", "Controls")
    white_area_min = cv2.getTrackbarPos("White Area Min", "Controls")
    white_area_max = cv2.getTrackbarPos("White Area Max", "Controls")

    # 4. Clean up small background noise
    kernel = np.ones((5, 5), np.uint8)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)

    # 4b. Build a color-coded visualization so red glare and white core are
    # visually distinguishable in the mask window (red mask -> red, white mask -> cyan)
    mask_vis = np.zeros((red_mask.shape[0], red_mask.shape[1], 3), dtype=np.uint8)
    mask_vis[white_mask > 0] = (255, 255, 0)
    mask_vis[red_mask > 0] = (0, 0, 255)

    # 5. Find candidate blobs using ONLY red_mask — white_mask is too loose on its
    # own (catches bright background) so it's just used below to confirm a hit
    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    red_led_on = False

    for contour in contours:
        if cv2.contourArea(contour) > redsize_min and cv2.contourArea(contour) < redsize_max:
            x, y, w, h = cv2.boundingRect(contour)

            # Fill the contour's bounding rectangle (not just its exact silhouette)
            # into its own mask, then intersect with white_mask — the white core
            # often sits just outside the red blob's silhouette but still within
            # its bounding box
            contour_mask = np.zeros(red_mask.shape, dtype=np.uint8)
            cv2.rectangle(contour_mask, (x, y), (x + w, y + h), 255, -1)
            white_inside_red = cv2.bitwise_and(white_mask, contour_mask)
            white_pixels = cv2.countNonZero(white_inside_red)

            if white_area_min < white_pixels < white_area_max:
                red_led_on = True
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, "RED LASER", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    # 6. Draw an on-screen dashboard showing the real-time laser status
    r_text, r_color = ("RED LASER: ON", (0, 0, 255)) if red_led_on else ("RED LASER: OFF", (0, 0, 180))
    cv2.putText(frame, r_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, r_color, 2)

    # Show the windows
    cv2.imshow("Dual LED Detector", frame)
    cv2.imshow("Combined Mask (What OpenCV Sees)", mask_vis)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    # Exit if either window is closed via the X button
    if (cv2.getWindowProperty("Dual LED Detector", cv2.WND_PROP_VISIBLE) < 1 or
            cv2.getWindowProperty("Combined Mask (What OpenCV Sees)", cv2.WND_PROP_VISIBLE) < 1):
        break

cap.release()
cv2.destroyAllWindows()