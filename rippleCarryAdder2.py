import time
import serial

# --- CONFIGURATION ---
SERIAL_PORT = '/dev/cu.usbmodem101'  # Double check the port by checking in Arduino IDE
BAUD_RATE = 9600                     # Matches the Arduino's Serial.begin(9600)

def main():
    print("Opening Serial Connection to Arduino...")
    try:
        # Initialize serial link with a longer timeout to match 9600 baud rate
        arduino = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=2)
        time.sleep(2)  # Wait for Arduino to reboot
        print("Connected successfully!\n")
    except Exception as e:
        print(f"Connection Error: {e}")
        return

    print("----Our ripple carry adder in action!!----")
    
    while True:
        try:
            num1 = input("Enter first number (or 'exit' to stop): ").strip()
            if num1.lower() == 'exit':
                break 
                
            num2 = input("Enter second number (or 'exit' to stop): ").strip()
            if num2.lower() == 'exit':
                break 

            val1 = int(num1)
            val2 = int(num2)
        except ValueError:
            print("Please enter valid integers.")
            continue

        bin1 = format(val1, '08b')
        bin2 = format(val2, '08b')
        
        print(f"\nProcessing {val1} + {val2} in 8-bit Binary:")
        print(f"  A: {bin1}")
        print(f"  B: {bin2}")
        print("------------------------------------------------")

        # Clear out any leftover data sitting in the serial lines
        arduino.reset_input_buffer()
        arduino.reset_output_buffer()

        final_binary_sum = ""
        current_carry = 0

        # Loop from rightmost bit down to leftmost bit
        for i in range(7, -1, -1):
            bit_a = bin1[i]
            bit_b = bin2[i]
            
            # Send exactly 3 characters down to Arduino
            payload = f"{bit_a}{bit_b}{current_carry}"
            arduino.write(payload.encode('utf-8'))
            
            # 9600 baud is slightly slower; give the Arduino time to process and print back
            time.sleep(0.08)
            
            # Read the 3 lines your Arduino prints out:
            # Line 1: "Inputs: A=X B=Y Cin=Z"
            line1 = arduino.readline().decode('utf-8').strip()
            # Line 2: "Outputs -> Carry Out: X | Sum: Y"
            line2 = arduino.readline().decode('utf-8').strip()
            # Line 3: "---------------------------------------"
            line3 = arduino.readline().decode('utf-8').strip()

            # Parse line 2 to find what the physical hardware pins read
            bit_sum = 0
            if "Sum: " in line2:
                # Extracts the last character of line 2 (which is the Sum 0 or 1)
                bit_sum = int(line2.split("Sum: ")[1].strip())
            
            if "Carry Out: " in line2:
                # Extracts the carry character by grabbing what sits between 'Carry Out: ' and ' |'
                current_carry = int(line2.split("Carry Out: ")[1].split(" |")[0].strip())

            final_binary_sum = str(bit_sum) + final_binary_sum
            print(f"  Bit {7-i}: {bit_a} + {bit_b} -> HW Read Sum: {bit_sum} | HW Read Cout: {current_carry}")

        # Finish up with final leftover carry bit
        final_binary_sum = str(current_carry) + final_binary_sum
        decimal_result = int(final_binary_sum, 2)

        print("------------------------------------------------")
        print(f"Final Hardware Binary Output: {final_binary_sum}")
        print(f"🏆 Mathematical Result: {decimal_result}")
        print("================================================")

    arduino.close()

if __name__ == "__main__":
    main()