#Instructions: left-click anywhere in the video (not mask) panel to point
#the laser turret at that location. Right-click and drag to draw a region
#of interest that detection is restricted to. Once a region is drawn, drag
#the "Calibrate (1=go)" slider in the Controls window to 1 to have the
#turret self-calibrate to that region by sweeping the servos and watching
#where the laser lands.

import cv2
import numpy as np
import time
from pymata4 import pymata4

# Servo pins (swapped from servotest.py's wiring assumption - on this rig pin 9
# physically drives tilt and pin 10 physically drives pan)
SERVO_PAN_PIN = 10   # X axis
SERVO_TILT_PIN = 9   # Y axis

# Calibrated pulse limits for MS18 servos
MIN_PULSE = 544
MAX_PULSE = 2400

# Calibration sweep settings
CALIBRATION_GRID_SIZE = 10      # points per axis (5x5 = 25 servo positions)
CALIBRATION_SETTLE_TIME = 0.3  # seconds to let the servo/laser settle before reading a frame
CALIBRATION_MIN_SAMPLES = 3    # minimum in-box hits needed to fit a mapping

# Initialize Arduino (StandardFirmata) and center both servos
board = pymata4.Pymata4()
board.set_pin_mode_servo(SERVO_PAN_PIN, min_pulse=MIN_PULSE, max_pulse=MAX_PULSE)
board.set_pin_mode_servo(SERVO_TILT_PIN, min_pulse=MIN_PULSE, max_pulse=MAX_PULSE)
time.sleep(1)
board.servo_write(SERVO_PAN_PIN, 90)
board.servo_write(SERVO_TILT_PIN, 90)

cap = cv2.VideoCapture(0)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))


def nothing(x):
    pass


# Sensitivity knobs â adjust live while the program runs, no code edits needed.
# OpenCV trackbar windows can't scroll, so size it tall enough up front to fit
# all sliders (it's still resizable by dragging if you add more later).
cv2.namedWindow("Controls", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Controls", 400, 450)

cv2.createTrackbar("Red On", "Controls", 1, 1, nothing)
cv2.createTrackbar("Red R Min", "Controls", 225, 255, nothing)
cv2.createTrackbar("Red GB Max", "Controls", 255, 255, nothing)

cv2.createTrackbar("White On", "Controls", 1, 1, nothing)
cv2.createTrackbar("White Min", "Controls", 175, 255, nothing)

# Standard OpenCV builds don't reliably support real buttons (cv2.createButton
# needs a Qt backend), so this trackbar doubles as one: drag it to 1 to fire
# calibration once, and the main loop resets it back to 0 afterward.
cv2.createTrackbar("Calibrate (1=go)", "Controls", 0, 1, nothing)


def get_masks(frame):
    red_on = cv2.getTrackbarPos("Red On", "Controls")
    red_r_min = cv2.getTrackbarPos("Red R Min", "Controls")
    red_gb_max = cv2.getTrackbarPos("Red GB Max", "Controls")
    lower_bright_red = np.array([0, 0, red_r_min])
    upper_bright_red = np.array([red_gb_max, red_gb_max, 255])
    red_mask = cv2.inRange(frame, lower_bright_red, upper_bright_red) if red_on else np.zeros(frame.shape[:2], dtype=np.uint8)

    # White/overexposed core mask â catches the blown-out center of a bright LED.
    # Uses overall brightness rather than requiring every B/G/R channel to
    # individually saturate, since a clipped red channel can outpace green/blue.
    white_on = cv2.getTrackbarPos("White On", "Controls")
    white_min = cv2.getTrackbarPos("White Min", "Controls")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    white_mask = cv2.inRange(gray, white_min, 255) if white_on else np.zeros(frame.shape[:2], dtype=np.uint8)

    kernel = np.ones((5, 5), np.uint8)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
    white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)
    return red_mask, white_mask


def find_confirmed_blobs(red_mask, white_mask):
    # Find candidate blobs using ONLY red_mask â white_mask is too loose on its
    # own (catches bright background) so it's just used below to confirm a hit
    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    blobs = []
    for contour in contours:
        if cv2.contourArea(contour) > 0:
            x, y, w, h = cv2.boundingRect(contour)

            # Fill the contour's bounding rectangle (not just its exact silhouette)
            # into its own mask, then intersect with white_mask â the white core
            # often sits just outside the red blob's silhouette but still within
            # its bounding box
            contour_mask = np.zeros(red_mask.shape, dtype=np.uint8)
            cv2.rectangle(contour_mask, (x, y), (x + w, y + h), 255, -1)
            white_inside_red = cv2.bitwise_and(white_mask, contour_mask)
            if cv2.countNonZero(white_inside_red) > 0:
                blobs.append((x, y, w, h))
    return blobs


# Right-click-and-drag region selector â detection is restricted to inside this
# rectangle once one is drawn, and it's also the target region for self-calibration.
roi = None
drawing = False
ix, iy = -1, -1

# Pixel-to-angle mapping learned by calibrate_to_roi(). None until a successful
# calibration has run, in which case aim_turret falls back to a naive linear
# guess across the full frame.
calibration = None


def aim_turret(x, y):
    if calibration is not None:
        coeffs_pan, coeffs_tilt = calibration
        point = np.array([x, y, 1.0])
        pan_angle = int(np.clip(point @ coeffs_pan, 0, 180))
        tilt_angle = int(np.clip(point @ coeffs_tilt, 0, 180))
    else:
        pan_angle = int(np.clip(180 - x / frame_width * 180, 0, 180))
        tilt_angle = int(np.clip(180 - y / frame_height * 180, 0, 180))
    board.servo_write(SERVO_PAN_PIN, pan_angle)
    board.servo_write(SERVO_TILT_PIN, tilt_angle)


def handle_mouse(event, x, y, flags, param):
    global roi, drawing, ix, iy
    if event == cv2.EVENT_LBUTTONDOWN:
        aim_turret(x, y)
    elif event == cv2.EVENT_RBUTTONDOWN:
        drawing = True
        ix, iy = x, y
        roi = None
    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        roi = (min(ix, x), min(iy, y), max(ix, x), max(iy, y))
    elif event == cv2.EVENT_MOUSEMOVE and flags & cv2.EVENT_FLAG_LBUTTON:
        aim_turret(x, y)
    elif event == cv2.EVENT_RBUTTONUP:
        drawing = False
        roi = (min(ix, x), min(iy, y), max(ix, x), max(iy, y))


def calibrate_to_roi(roi):
    """Sweep the servos over their full range, and for every grid point where
    the laser is detected inside the drawn box, record (pixel, angle). Fit a
    pixel -> angle mapping from those samples so later clicks in this region
    aim accurately instead of relying on the naive frame-wide linear guess."""
    global calibration

    rx0, ry0, rx1, ry1 = roi
    if rx1 - rx0 < 10 or ry1 - ry0 < 10:
        return

    print("Calibrating turret to drawn region...")
    samples = []
    for tilt in np.linspace(0, 180, CALIBRATION_GRID_SIZE):
        for pan in np.linspace(0, 180, CALIBRATION_GRID_SIZE):
            board.servo_write(SERVO_PAN_PIN, int(pan))
            board.servo_write(SERVO_TILT_PIN, int(tilt))
            time.sleep(CALIBRATION_SETTLE_TIME)

            ret, frame = cap.read()
            if not ret:
                continue

            red_mask, white_mask = get_masks(frame)
            blobs = find_confirmed_blobs(red_mask, white_mask)
            if not blobs:
                continue

            x, y, w, h = blobs[0]
            cx, cy = x + w / 2, y + h / 2
            if rx0 <= cx <= rx1 and ry0 <= cy <= ry1:
                samples.append((cx, cy, pan, tilt))

    if len(samples) < CALIBRATION_MIN_SAMPLES:
        print(f"Calibration failed: laser only landed inside the box {len(samples)} time(s) "
              f"(need >= {CALIBRATION_MIN_SAMPLES}). Keeping previous mapping.")
        return

    a = np.array([[px, py, 1.0] for px, py, _, _ in samples])
    pan_targets = np.array([pan for _, _, pan, _ in samples])
    tilt_targets = np.array([tilt for _, _, _, tilt in samples])
    coeffs_pan, _, _, _ = np.linalg.lstsq(a, pan_targets, rcond=None)
    coeffs_tilt, _, _, _ = np.linalg.lstsq(a, tilt_targets, rcond=None)
    calibration = (coeffs_pan, coeffs_tilt)
    print(f"Calibration complete using {len(samples)} sample(s).")


cv2.namedWindow("Dual LED Detector")
cv2.setMouseCallback("Dual LED Detector", handle_mouse)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if cv2.getTrackbarPos("Calibrate (1=go)", "Controls") == 1:
            if roi is None:
                print("Draw a region with right-click-drag before calibrating.")
            else:
                calibrate_to_roi(roi)
                board.servo_write(SERVO_PAN_PIN, 90)
                board.servo_write(SERVO_TILT_PIN, 90)
            cv2.setTrackbarPos("Calibrate (1=go)", "Controls", 0)

        red_mask, white_mask = get_masks(frame)

        # Restrict detection to the right-click-dragged region, if one has been drawn
        if roi is not None:
            roi_mask = np.zeros(red_mask.shape, dtype=np.uint8)
            rx0, ry0, rx1, ry1 = roi
            cv2.rectangle(roi_mask, (rx0, ry0), (rx1, ry1), 255, -1)
            red_mask = cv2.bitwise_and(red_mask, roi_mask)
            white_mask = cv2.bitwise_and(white_mask, roi_mask)

        # Build a color-coded visualization so red glare and white core are
        # visually distinguishable in the mask window (red mask -> red, white mask -> cyan)
        mask_vis = np.zeros((red_mask.shape[0], red_mask.shape[1], 3), dtype=np.uint8)
        mask_vis[white_mask > 0] = (255, 255, 0)
        mask_vis[red_mask > 0] = (0, 0, 255)

        blobs = find_confirmed_blobs(red_mask, white_mask)
        for x, y, w, h in blobs:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, "RED LASER", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # Draw an on-screen dashboard showing the real-time laser status
        red_led_on = len(blobs) > 0
        r_text, r_color = ("RED LASER: ON", (0, 0, 255)) if red_led_on else ("RED LASER: OFF", (0, 0, 180))
        cv2.putText(frame, r_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, r_color, 2)

        # Draw the selected region (yellow) for visual feedback
        if roi is not None:
            rx0, ry0, rx1, ry1 = roi
            cv2.rectangle(frame, (rx0, ry0), (rx1, ry1), (0, 255, 255), 1)

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
finally:
    cap.release()
    cv2.destroyAllWindows()
    board.shutdown()
