import cv2

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 1. Convert the frame to grayscale (makes it easier to measure brightness)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 2. Smooth the image to reduce background noise/static
    blurred = cv2.GaussianBlur(gray, (11, 11), 0)

    # 3. Thresholding: Turn everything below a certain brightness completely black, 
    # and everything above it completely white (255).
    # You can tweak '200' depending on how bright your room is.
    _, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)

    # 4. Find the outlines (contours) of the white shapes in the thresholded image
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 5. If we found at least one bright shape, track the largest one
    if len(contours) > 0:
        # Find the largest contour by area (assumed to be our main bright object)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Get the coordinates of a bounding box around that object
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Draw a green rectangle around the brightest object on the original frame
        # (x, y) is top-left, (x+w, y+h) is bottom-right. (0, 255, 0) is Green. 2 is thickness.
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Optional: Put a text label on the box
        cv2.putText(frame, "Brightest Spot", (x, y - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Show both the live tracking and what the "computer sees" via thresholding
    cv2.imshow("Tracking Feed", frame)
    cv2.imshow("What the Computer Sees (Threshold)", thresh)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()