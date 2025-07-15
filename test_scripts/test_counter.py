#!/usr/bin/env python3
import time
import sys

counter = 0
while True:
    counter += 1
    print(f"Counter: {counter}")
    sys.stdout.flush()
    time.sleep(2)
