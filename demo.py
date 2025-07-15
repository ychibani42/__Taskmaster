#!/usr/bin/env python3
"""
Script de démonstration pour Taskmaster
Montre comment utiliser le système de gestion de processus en background
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

# Ajouter le dossier taskmaster au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'taskmaster'))

def run_demo():
    """Démonstration du système Taskmaster"""
    print("🚀 DÉMONSTRATION TASKMASTER")
    print("="*50)
    
    # Vérifier que les fichiers existent
    config_files = ['example.conf', 'foo.conf']
    available_config = None
    
    for config_file in config_files:
        if os.path.exists(config_file):
            available_config = config_file
            break
    
    if not available_config:
        print("❌ Aucun fichier de configuration trouvé")
        print("   Créez un fichier example.conf ou foo.conf")
        return
    
    print(f"📋 Utilisation du fichier de configuration: {available_config}")
    
    # Démonstration 1: Lancer le daemon en mode background
    print("\n1️⃣  DÉMONSTRATION: Lancement du daemon en arrière-plan")
    print("-" * 50)
    
    try:
        # Importer et créer le gestionnaire de processus
        from process_manager import ProcessManager
        
        manager = ProcessManager()
        manager.load_config(available_config)
        
        print("✅ Gestionnaire de processus créé")
        
        # Démarrer tous les processus
        print("🚀 Démarrage de tous les processus...")
        manager.start_all()
        
        # Attendre un peu pour voir les processus démarrer
        time.sleep(3)
        
        # Afficher le statut
        print("\n📊 Statut des processus:")
        status_list = manager.get_status()
        for status in status_list:
            state_icon = "🟢" if status['state'] == "RUNNING" else "🔴"
            print(f"   {state_icon} {status['name']}: {status['state']} ({status['num_processes']} instances)")
        
        # Laisser tourner quelques secondes
        print("\n⏳ Processus en cours d'exécution... (10 secondes)")
        time.sleep(10)
        
        # Arrêter tous les processus
        print("\n🛑 Arrêt de tous les processus...")
        manager.stop_all()
        
        print("✅ Démonstration terminée")
        
    except Exception as e:
        print(f"❌ Erreur lors de la démonstration: {e}")
        import traceback
        traceback.print_exc()


def demo_interactive():
    """Démonstration du mode interactif"""
    print("\n2️⃣  DÉMONSTRATION: Mode interactif")
    print("-" * 50)
    print("💡 Pour tester le mode interactif, lancez:")
    print("   python3 taskmaster/taskmasterctl.py -c example.conf")
    print("\n📝 Commandes disponibles:")
    print("   - status          : Voir le statut des processus")
    print("   - start <nom>     : Démarrer un processus")
    print("   - stop <nom>      : Arrêter un processus")
    print("   - restart <nom>   : Redémarrer un processus")
    print("   - list            : Lister tous les programmes")
    print("   - help            : Aide")
    print("   - quit            : Quitter")


def demo_daemon():
    """Démonstration du mode daemon"""
    print("\n3️⃣  DÉMONSTRATION: Mode daemon")
    print("-" * 50)
    print("💡 Pour tester le mode daemon, lancez:")
    print("   python3 taskmaster/taskmasterd.py -c example.conf")
    print("\n📝 Le daemon va:")
    print("   - Charger la configuration")
    print("   - Démarrer tous les processus avec autostart=true")
    print("   - Surveiller et redémarrer les processus si nécessaire")
    print("   - Continuer à tourner jusqu'à réception d'un signal")


def create_test_processes():
    """Créer des processus de test simples"""
    print("\n4️⃣  CRÉATION DE PROCESSUS DE TEST")
    print("-" * 50)
    
    # Créer des scripts de test
    test_scripts = {
        'test_counter.py': '''#!/usr/bin/env python3
import time
import sys

counter = 0
while True:
    counter += 1
    print(f"Counter: {counter}")
    sys.stdout.flush()
    time.sleep(2)
''',
        'test_memory.py': '''#!/usr/bin/env python3
import time
import psutil
import os

while True:
    process = psutil.Process(os.getpid())
    memory = process.memory_info().rss / 1024 / 1024  # MB
    cpu = process.cpu_percent()
    print(f"PID: {os.getpid()}, Memory: {memory:.2f} MB, CPU: {cpu:.2f}%")
    time.sleep(5)
''',
        'test_failing.py': '''#!/usr/bin/env python3
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
'''
    }
    
    scripts_dir = Path("test_scripts")
    scripts_dir.mkdir(exist_ok=True)
    
    for filename, content in test_scripts.items():
        script_path = scripts_dir / filename
        script_path.write_text(content)
        script_path.chmod(0o755)
        print(f"✅ Créé: {script_path}")
    
    # Créer un fichier de configuration pour ces tests
    test_config = f"""# Configuration de test pour les processus de démonstration

[test_counter]
cmd = python3 {scripts_dir}/test_counter.py
numprocs = 2
umask = 022
workingdir = /tmp
autostart = true
autorestart = true
exitcodes = 0
startretries = 3
starttime = 2
stopsignal = TERM
stoptime = 5
stdout = /tmp/test_counter.stdout
stderr = /tmp/test_counter.stderr

[test_memory]
cmd = python3 {scripts_dir}/test_memory.py
numprocs = 1
umask = 022
workingdir = /tmp
autostart = true
autorestart = unexpected
exitcodes = 0
startretries = 2
starttime = 1
stopsignal = TERM
stoptime = 3
stdout = /tmp/test_memory.stdout
stderr = /tmp/test_memory.stderr

[test_failing]
cmd = python3 {scripts_dir}/test_failing.py
numprocs = 1
umask = 022
workingdir = /tmp
autostart = false
autorestart = true
exitcodes = 0
startretries = 5
starttime = 3
stopsignal = TERM
stoptime = 5
stdout = /tmp/test_failing.stdout
stderr = /tmp/test_failing.stderr
"""
    
    config_path = Path("test_processes.conf")
    config_path.write_text(test_config)
    print(f"✅ Configuration créée: {config_path}")
    
    print("\n💡 Pour tester ces processus:")
    print(f"   python3 taskmaster/taskmasterd.py -c {config_path}")


def main():
    """Fonction principale de démonstration"""
    print("🎯 TASKMASTER - SYSTÈME DE GESTION DE PROCESSUS")
    print("=" * 60)
    print("Ce système permet de lancer et gérer des processus en arrière-plan")
    print("depuis des fichiers de configuration .ini/.conf\n")
    
    try:
        # Vérifier les prérequis
        if not os.path.exists("taskmaster"):
            print("❌ Dossier 'taskmaster' non trouvé")
            print("   Assurez-vous d'être dans le bon répertoire")
            return
        
        # Lancer les démonstrations
        create_test_processes()
        run_demo()
        demo_interactive()
        demo_daemon()
        
        print("\n🎉 DÉMONSTRATION TERMINÉE")
        print("=" * 60)
        print("📚 Points clés:")
        print("   • Les processus sont lancés en arrière-plan via subprocess")
        print("   • Chaque processus est surveillé par un thread dédié")
        print("   • Les processus peuvent être redémarrés automatiquement")
        print("   • La configuration supporte plusieurs instances (numprocs)")
        print("   • Les signaux sont gérés proprement pour l'arrêt")
        
    except KeyboardInterrupt:
        print("\n🛑 Démonstration interrompue par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur durant la démonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()