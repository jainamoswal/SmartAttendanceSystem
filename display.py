#! /usr/bin/env python
import re 
import random 
import string
import drivers
from time import sleep

display = drivers.Lcd()
file_name = "/etc/hostapd/hostapd.conf"

def get_random(k=8):
    digits = string.digits
    random_digits = random.choices(digits, k=k)
    random_number = ''.join(random_digits)
    return random_number


if __name__ == "__main__":
    new_password = get_random()
    print("new passwsord: ", new_password)
    with open(file_name, "r+") as f:
        data = f.read()
    password = re.findall(r'wpa_passphrase=(.*)', data)[0]

    data = data.replace(password, new_password)
    with open(file_name, "w") as f:
        f.write(data)

    try:
        while True:
            display.lcd_display_string(f"Key : {password}", 1)
            sleep(10)
                                            
    except KeyboardInterrupt:
        print("Cleaning up!")
        display.lcd_clear()
