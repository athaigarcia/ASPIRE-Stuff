import cv2
import numpy as np

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 1. Pre-process the image to find clean edges
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # Canny Edge Detection highlights the sharp borders of shapes
    edges = cv2.Canny(blurred, 50, 150)

    # 2. Find the contours (outlines) of those edges
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        # Ignore tiny specks of background noise
        if cv2.contourArea(contour) < 500:
            continue

        # 3. Contour Approximation: Simplify the curve to find the corners
        # epsilon calculates how strictly the line should fit the original contour
        epsilon = 0.04 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # 4. Count the vertices (corners) to identify the shape
        num_corners = len(approx)
        x, y, w, h = cv2.boundingRect(approx)
        
        shape_name = "Unknown"

        if num_corners == 3:
            shape_name = "Triangle"
            color = (0, 255, 255) # Yellow
            
        elif num_corners == 4:
            # A 4-sided shape could be a square or a rectangle. 
            # We check the aspect ratio (width / height) to find out.
            aspect_ratio = float(w) / h
            if 0.95 <= aspect_ratio <= 1.05: # If sides are almost perfectly equal
                shape_name = "Square"
            else:
                shape_name = "Rectangle"
            color = (0, 255, 0) # Green
            
        elif num_corners == 5:
            shape_name = "Pentagon"
            color = (255, 255, 0) # Cyan
            
        elif num_corners > 5:
            # If it has a high number of vertices, it's approximating a smooth curve
            shape_name = "Circle"
            color = (0, 0, 255) # Red

        # 5. Draw the results on the screen
        cv2.drawContours(frame, [approx], 0, color, 3)
        cv2.putText(frame, shape_name, (x, y - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    cv2.imshow("Shape Detector", frame)
    cv2.imshow("Edges (Canny)", edges)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()