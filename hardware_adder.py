# hardware_adder.py
import time
from pymata4 import pymata4

PIN_A, PIN_B, PIN_CIN = 13, 12, 11
PIN_SUM, PIN_COUT = 10, 9

board = pymata4.Pymata4(com_port="YOUR_COM_PORT")  # Adjust the COM port as necessary

board.set_pin_mode_digital_output(PIN_A)
board.set_pin_mode_digital_output(PIN_B)
board.set_pin_mode_digital_output(PIN_CIN)
board.set_pin_mode_digital_input(PIN_SUM)
board.set_pin_mode_digital_input(PIN_COUT)


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
    """
    Adds two binary strings using the physical ripple_carry_adder.
    """
    max_len = max(len(bin_a), len(bin_b))
    bin_a = bin_a.zfill(max_len)
    bin_b = bin_b.zfill(max_len)
    
    carry = "0"
    result = ""
    
    for i in range(max_len - 1, -1, -1): # Iterate from the least significant bit to the most significant bit
        response = add_1_bit(bin_a[i], bin_b[i], carry)
        carry = response[0]
        result = response[1] + result
        
    return carry + result

def multiply_bin(bin_a, bin_b):
    """
    Multiplies two binary strings using the shift-and-add method
    and the physical ripple_carry_adder.
    """
    # Keep track of the running total (partial sum)
    partial_sum = "0"
    
    # We look at bin_b (the multiplier) from right to left
    # to figure out how much to shift bin_a (the multiplicand)
    for i in range(len(bin_b) - 1, -1, -1):
        multiplier_bit = bin_b[i]
        
        if multiplier_bit == "1":
            # Shift bin_a to the left by appending '0's based on its position
            shift_amount = (len(bin_b) - 1) - i
            shifted_a = bin_a + ("0" * shift_amount)
            
            # Add this shifted value to our running partial sum
            print(f"Multiplying by 1: Adding {shifted_a} to current sum {partial_sum}")
            partial_sum = ripple_carry_adder(partial_sum, shifted_a)
        else:
            # If the bit is 0, adding 0 changes nothing, so we just skip the addition
            print(f"Multiplying by 0: Skipping bit position")
            
    # Clean up any unnecessary leading zeros that the ripple adder might have padded
    # but ensure we keep a "0" if the final answer is actually zero.
    cleaned_result = partial_sum.lstrip("0")
    return cleaned_result if cleaned_result else "0"

# use board.shutdown() or unplug and replug the Arduino to reset
