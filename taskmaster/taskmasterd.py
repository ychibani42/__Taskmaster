#!/usr/bin/env python3

import sys
import os
import argparse
import signal
import configparser
from typing import Dict, List
from pydantic import ValidationError

from models import ProgramConfig
from process_manager import ProcessManager


def parse_exitcodes(value: str) -> List[int]:
    """Parse les codes de sortie depuis une chaîne"""
    if ',' in value:
        return [int(x.strip()) for x in value.split(',')]
    else:
        return [int(value.strip())]


def parse_env(value: str) -> Dict[str, str]:
    """Parse les variables d'environnement depuis une chaîne"""
    env_dict = {}
    for pair in value.split(','):
        if '=' in pair:
            key, k_value = pair.split("=", 1)
            env_dict[key.strip()] = k_value.strip()
    return env_dict if env_dict else None


def load_program_configs(path: str) -> Dict[str, ProgramConfig]:
    """Charge les configurations des programmes depuis un fichier .ini/.conf"""
    if not os.path.exists(path):
        print(f"❌ Fichier de configuration non trouvé: {path}")
        return {}
    
    config = configparser.ConfigParser()
    config.read(path)
    programs = {}
    
    for section in config.sections():
        try:
            data = dict(config.items(section))
            
            # Parser les champs spéciaux
            if 'exitcodes' in data:
                data["exitcodes"] = parse_exitcodes(data["exitcodes"])
            if 'env' in data:
                data['env'] = parse_env(data['env'])
            
            # Convertir les types
            for bool_field in ['autostart']:
                if bool_field in data:
                    data[bool_field] = data[bool_field].lower() == 'true'
            
            for int_field in ['numprocs', 'startretries', 'starttime', 'stoptime']:
                if int_field in data:
                    data[int_field] = int(data[int_field])
            
            programs[section] = ProgramConfig(**data)
            print(f"✅ Configuration chargée pour le programme: {section}")
            
        except ValidationError as exc:
            print(f"❌ Erreur de validation pour le programme {section}: {exc}")
        except Exception as e:
            print(f"❌ Erreur lors du chargement du programme {section}: {e}")
    
    return programs


class TaskmasterDaemon:
    def __init__(self, config_file: str = "foo.conf"):
        self.config_file = config_file
        self.process_manager = ProcessManager()
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Configure les gestionnaires de signaux"""
        def signal_handler(signum, frame):
            print(f"\n🛑 Signal {signum} reçu, arrêt du daemon...")
            self.shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start(self):
        """Démarre le daemon"""
        print("🚀 Démarrage du daemon Taskmaster...")
        
        # Charger la configuration
        self.process_manager.load_config(self.config_file)
        
        # Démarrer tous les processus avec autostart=True
        self.process_manager.start_all()
        
        print("✅ Daemon démarré avec succès")
        print("📊 Statut initial des processus:")
        self.print_status()
        
        # Attendre la fermeture
        self.process_manager.wait_for_shutdown()
    
    def shutdown(self):
        """Arrête le daemon proprement"""
        print("🛑 Arrêt du daemon...")
        self.process_manager.stop_all()
        print("✅ Daemon arrêté")
        sys.exit(0)
    
    def print_status(self):
        """Affiche le statut de tous les processus"""
        status_list = self.process_manager.get_status()
        
        print("\n" + "="*60)
        print("📊 STATUT DES PROCESSUS")
        print("="*60)
        
        for status in status_list:
            print(f"🔹 {status['name']:<15} | {status['state']:<10} | Instances: {status['num_processes']}")
            if status['start_time']:
                import datetime
                start_time = datetime.datetime.fromtimestamp(status['start_time']).strftime("%H:%M:%S")
                print(f"   └─ Démarré à: {start_time}")
            if status['retry_count'] > 0:
                print(f"   └─ Tentatives de redémarrage: {status['retry_count']}")
        
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Taskmaster - Gestionnaire de processus")
    parser.add_argument(
        "-c", "--config", 
        default="foo.conf",
        help="Fichier de configuration (défaut: foo.conf)"
    )
    parser.add_argument(
        "-d", "--daemon", 
        action="store_true",
        help="Exécuter en mode daemon"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true",
        help="Mode verbose"
    )
    
    args = parser.parse_args()
    
    # Créer et démarrer le daemon
    daemon = TaskmasterDaemon(args.config)
    
    try:
        daemon.start()
    except KeyboardInterrupt:
        print("\n🛑 Interruption clavier détectée")
        daemon.shutdown()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        daemon.shutdown()


if __name__ == "__main__":
    main()
