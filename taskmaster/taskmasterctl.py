#!/usr/bin/env python3

import signal
import sys
import os
import socket
import json
import threading
import time
from typing import Dict, List, Optional
from types import FrameType


class TaskmasterController:
    def __init__(self, config_file: str = "foo.conf"):
        self.config_file = config_file
        self.running = True
        self.process_manager = None
        self.setup_signal_handlers()
        
        # Importer ici pour éviter les imports circulaires
        from process_manager import ProcessManager
        self.process_manager = ProcessManager()
        self.process_manager.load_config(config_file)
    
    def setup_signal_handlers(self):
        """Configure les gestionnaires de signaux"""
        def signal_handler(signum: int, frame: FrameType):
            print(f"\n🛑 Signal {signum} reçu, arrêt du contrôleur...")
            self.running = False
            if self.process_manager:
                self.process_manager.stop_all()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def print_help(self):
        """Affiche l'aide des commandes disponibles"""
        help_text = """
🔧 COMMANDES DISPONIBLES:
═══════════════════════════════════════════════════════════

📊 STATUT:
   status               - Affiche le statut de tous les processus
   status <nom>         - Affiche le statut d'un processus spécifique

🚀 CONTRÔLE:
   start <nom>          - Démarre un processus
   stop <nom>           - Arrête un processus
   restart <nom>        - Redémarre un processus
   start all            - Démarre tous les processus
   stop all             - Arrête tous les processus
   restart all          - Redémarre tous les processus

🔧 CONFIGURATION:
   reload               - Recharge la configuration depuis le fichier
   list                 - Liste tous les programmes configurés

⚙️  SYSTÈME:
   help                 - Affiche cette aide
   quit / exit          - Quitte le contrôleur

═══════════════════════════════════════════════════════════
"""
        print(help_text)
    
    def cmd_status(self, args: List[str]):
        """Commande status - affiche le statut des processus"""
        if not self.process_manager:
            print("❌ Gestionnaire de processus non initialisé")
            return
        
        status_list = self.process_manager.get_status()
        
        if len(args) > 0:
            # Statut d'un processus spécifique
            program_name = args[0]
            found = False
            for status in status_list:
                if status['name'] == program_name:
                    self.print_process_status(status)
                    found = True
                    break
            if not found:
                print(f"❌ Processus '{program_name}' non trouvé")
        else:
            # Statut de tous les processus
            print("\n" + "="*70)
            print("📊 STATUT DES PROCESSUS")
            print("="*70)
            
            if not status_list:
                print("   Aucun processus configuré")
            else:
                for status in status_list:
                    self.print_process_status(status, compact=True)
            
            print("="*70)
    
    def print_process_status(self, status: Dict, compact: bool = False):
        """Affiche le statut d'un processus"""
        state_icons = {
            "RUNNING": "🟢",
            "STOPPED": "🔴",
            "STARTING": "🟡",
            "STOPPING": "🟠",
            "FATAL": "💀",
            "BACKOFF": "⚠️"
        }
        
        icon = state_icons.get(status['state'], "❓")
        
        if compact:
            print(f"{icon} {status['name']:<15} | {status['state']:<10} | Instances: {status['num_processes']}")
        else:
            print(f"\n{icon} Processus: {status['name']}")
            print(f"   État: {status['state']}")
            print(f"   Instances actives: {status['num_processes']}")
            
            if status['start_time']:
                import datetime
                start_time = datetime.datetime.fromtimestamp(status['start_time']).strftime("%Y-%m-%d %H:%M:%S")
                print(f"   Démarré à: {start_time}")
            
            if status['stop_time']:
                import datetime
                stop_time = datetime.datetime.fromtimestamp(status['stop_time']).strftime("%Y-%m-%d %H:%M:%S")
                print(f"   Arrêté à: {stop_time}")
            
            if status['retry_count'] > 0:
                print(f"   Tentatives de redémarrage: {status['retry_count']}")
    
    def cmd_start(self, args: List[str]):
        """Commande start - démarre un ou plusieurs processus"""
        if not args:
            print("❌ Usage: start <nom_processus> | start all")
            return
        
        if args[0] == "all":
            print("🚀 Démarrage de tous les processus...")
            self.process_manager.start_all()
        else:
            program_name = args[0]
            print(f"🚀 Démarrage du processus '{program_name}'...")
            self.process_manager.start_process(program_name)
    
    def cmd_stop(self, args: List[str]):
        """Commande stop - arrête un ou plusieurs processus"""
        if not args:
            print("❌ Usage: stop <nom_processus> | stop all")
            return
        
        if args[0] == "all":
            print("🛑 Arrêt de tous les processus...")
            self.process_manager.stop_all()
        else:
            program_name = args[0]
            print(f"🛑 Arrêt du processus '{program_name}'...")
            self.process_manager.stop_process(program_name)
    
    def cmd_restart(self, args: List[str]):
        """Commande restart - redémarre un ou plusieurs processus"""
        if not args:
            print("❌ Usage: restart <nom_processus> | restart all")
            return
        
        if args[0] == "all":
            print("🔄 Redémarrage de tous les processus...")
            self.process_manager.stop_all()
            time.sleep(2)
            self.process_manager.start_all()
        else:
            program_name = args[0]
            print(f"🔄 Redémarrage du processus '{program_name}'...")
            self.process_manager.restart_process(program_name)
    
    def cmd_reload(self, args: List[str]):
        """Commande reload - recharge la configuration"""
        print("🔄 Rechargement de la configuration...")
        self.process_manager.stop_all()
        time.sleep(1)
        self.process_manager.load_config(self.config_file)
        print("✅ Configuration rechargée")
    
    def cmd_list(self, args: List[str]):
        """Commande list - liste tous les programmes configurés"""
        if not self.process_manager.processes:
            print("❌ Aucun programme configuré")
            return
        
        print("\n📋 PROGRAMMES CONFIGURÉS:")
        print("="*50)
        
        for name, managed_process in self.process_manager.processes.items():
            config = managed_process.config
            print(f"🔹 {name}")
            print(f"   └─ Commande: {config.cmd}")
            print(f"   └─ Instances: {config.numprocs}")
            print(f"   └─ Répertoire: {config.workingdir}")
            print(f"   └─ Démarrage auto: {config.autostart}")
            print(f"   └─ Redémarrage auto: {config.autorestart}")
        
        print("="*50)
    
    def process_command(self, command_line: str):
        """Traite une ligne de commande"""
        if not command_line.strip():
            return
        
        parts = command_line.strip().split()
        command = parts[0].lower()
        args = parts[1:]
        
        commands = {
            'status': self.cmd_status,
            'start': self.cmd_start,
            'stop': self.cmd_stop,
            'restart': self.cmd_restart,
            'reload': self.cmd_reload,
            'list': self.cmd_list,
            'help': lambda _: self.print_help(),
            'quit': lambda _: self.quit(),
            'exit': lambda _: self.quit()
        }
        
        if command in commands:
            try:
                commands[command](args)
            except Exception as e:
                print(f"❌ Erreur lors de l'exécution de la commande: {e}")
        else:
            print(f"❌ Commande inconnue: {command}")
            print("   Tapez 'help' pour voir les commandes disponibles")
    
    def quit(self):
        """Quitte le contrôleur"""
        print("👋 Au revoir!")
        self.running = False
        if self.process_manager:
            self.process_manager.stop_all()
        sys.exit(0)
    
    def run_interactive(self):
        """Lance le mode interactif"""
        print("🎮 TASKMASTER CONTROLLER")
        print("="*50)
        print("Tapez 'help' pour voir les commandes disponibles")
        print("Tapez 'quit' ou 'exit' pour quitter")
        print("="*50)
        
        while self.running:
            try:
                command = input("taskmaster> ").strip()
                if command:
                    self.process_command(command)
            except KeyboardInterrupt:
                print("\n")
                self.quit()
            except EOFError:
                print("\n")
                self.quit()
            except Exception as e:
                print(f"❌ Erreur: {e}")
    
    def run_daemon_mode(self):
        """Lance le mode daemon avec processus en background"""
        print("🚀 Démarrage en mode daemon...")
        
        # Démarrer tous les processus configurés
        self.process_manager.start_all()
        
        # Attendre indéfiniment
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Arrêt demandé")
            self.quit()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Taskmaster Controller - Interface de contrôle")
    parser.add_argument(
        "-c", "--config", 
        default="foo.conf",
        help="Fichier de configuration (défaut: foo.conf)"
    )
    parser.add_argument(
        "-d", "--daemon", 
        action="store_true",
        help="Lancer en mode daemon (processus en background)"
    )
    parser.add_argument(
        "-i", "--interactive", 
        action="store_true",
        help="Mode interactif (défaut)"
    )
    
    args = parser.parse_args()
    
    # Créer le contrôleur
    controller = TaskmasterController(args.config)
    
    try:
        if args.daemon:
            controller.run_daemon_mode()
        else:
            controller.run_interactive()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        controller.quit()


if __name__ == "__main__":
    main()