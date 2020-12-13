import random
import string
#### from crypto.py
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import (
    Cipher, algorithms, modes
)
import os
import traceback
import time
####

def workload_gen(size):
    random_string = ''.join([random.choice(string.printable) for _ in range(size)])
    return random_string

def gen_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return (public_key, private_key)


def run_function_extended(function, *args):
    start_time = time.process_time()
    for _ in range(100):
        function(*args)
    end_time = time.process_time()
    elapsed = (end_time-start_time)/100
    return elapsed
