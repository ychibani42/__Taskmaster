#!/usr/bin/env python3
import time
import psutil
import os

while True:
    process = psutil.Process(os.getpid())
    memory = process.memory_info().rss / 1024 / 1024  # MB
    cpu = process.cpu_percent()
    print(f"PID: {os.getpid()}, Memory: {memory:.2f} MB, CPU: {cpu:.2f}%")
    time.sleep(5)
