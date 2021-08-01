import random
from typing import Dict

class Color:
    NC = '\033[0m' # no colour
    WB = '\033[1m' # White bold
    R  = '\033[31m' # red
    G  = '\033[32m' # green
    O  = '\033[33m' # orange
    B  = '\033[96m' # cyan blue
    W  = '\033[97m' # white
    P  = '\033[35m' # purple

def get_random_string(length):
    random_string = ''
    for _ in range(10):
        random_string += (chr(random.randint(97, 97 + 26 - 1)))
    return random_string

def success(msg, newline=False):
    if newline:
        print()
    print(f"{Color.G}[+] {msg}{Color.NC}", flush=True)

def failure(msg):
    print(f"{Color.R}[-] {msg}{Color.NC}", flush=True)

def printinfo(msg):
    print(f"{Color.B}[*] {msg}{Color.NC}", flush=True)