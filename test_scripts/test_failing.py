#!/usr/bin/env python3
import time
import random
import sys

# Processus qui échoue parfois pour tester le redémarrage
for i in range(10):
    print(f"Iteration {i}")
    time.sleep(2)
    if random.random() < 0.3:  # 30% de chance d'échouer
        print("Simulating failure!")
        sys.exit(1)

print("Process completed successfully")
