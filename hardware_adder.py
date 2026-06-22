# hardware_adder.py
import time
from pymata4 import pymata4

PIN_A, PIN_B, PIN_CIN = 13, 12, 11
PIN_SUM, PIN_COUT = 10, 9

serial_port = "PORT NAME"  # Replace with your Arduino's serial port name
board = pymata4.Pymata4(com_port=serial_port)

board.set_pin_mode_digital_output(PIN_A)
board.set_pin_mode_digital_output(PIN_B)
board.set_pin_mode_digital_output(PIN_CIN)
board.set_pin_mode_digital_input(PIN_SUM)
board.set_pin_mode_digital_input(PIN_COUT)
time.sleep(0.5)

def add_1_bit(bit_a, bit_b, carry_in):
    time.sleep(0.5)

    board.digital_write(PIN_A, int(bit_a))
    board.digital_write(PIN_B, int(bit_b))
    board.digital_write(PIN_CIN, int(carry_in))
    
    time.sleep(0.5) # The 0.5s delay to protect the USB cache
    
    sum_out, _ = board.digital_read(PIN_SUM)
    cout_out, _ = board.digital_read(PIN_COUT)

    return str(cout_out) + str(sum_out)

def ripple_carry_adder(bin_a, bin_b):
    max_len = max(len(bin_a), len(bin_b))
    bin_a = bin_a.zfill(max_len)
    bin_b = bin_b.zfill(max_len)
    
    carry = "0"
    result = ""
    
    for i in range(max_len - 1, -1, -1):
        response = add_1_bit(bin_a[i], bin_b[i], carry)
        carry = response[0]
        result = response[1] + result
        
    return carry + result

def shutdown_board():
    board.shutdown()