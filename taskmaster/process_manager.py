import subprocess
import threading
import time
import signal
import os
import sys
from typing import Dict, List, Optional
from models import ProgramConfig
from enum import Enum


class ProcessState(Enum):
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FATAL = "FATAL"
    BACKOFF = "BACKOFF"


class ManagedProcess:
    def __init__(self, name: str, config: ProgramConfig):
        self.name = name
        self.config = config
        self.processes: List[subprocess.Popen] = []
        self.state = ProcessState.STOPPED
        self.start_time = None
        self.stop_time = None
        self.retry_count = 0
        self.monitor_thread = None
        self.should_stop = False
        
    def start(self):
        """Démarre le processus selon la configuration numprocs"""
        if self.state == ProcessState.RUNNING:
            return
            
        self.state = ProcessState.STARTING
        self.processes = []
        
        for i in range(self.config.numprocs):
            process = self._start_single_process(i)
            if process:
                self.processes.append(process)
        
        if self.processes:
            self.state = ProcessState.RUNNING
            self.start_time = time.time()
            self.retry_count = 0
            
            # Démarrer le thread de monitoring
            self.monitor_thread = threading.Thread(target=self._monitor_processes, daemon=True)
            self.monitor_thread.start()
            
            print(f"✅ Processus {self.name} démarré avec {len(self.processes)} instances")
        else:
            self.state = ProcessState.FATAL
            print(f"❌ Échec du démarrage du processus {self.name}")
    
    def _start_single_process(self, instance_id: int) -> Optional[subprocess.Popen]:
        """Démarre une instance unique du processus"""
        try:
            # Préparer l'environnement
            env = os.environ.copy()
            if self.config.env:
                env.update(self.config.env)
            
            # Configurer les fichiers de sortie
            stdout_file = None
            stderr_file = None
            
            if self.config.stdout:
                stdout_path = f"{self.config.stdout}.{instance_id}" if self.config.numprocs > 1 else self.config.stdout
                stdout_file = open(stdout_path, 'a')
            
            if self.config.stderr:
                stderr_path = f"{self.config.stderr}.{instance_id}" if self.config.numprocs > 1 else self.config.stderr
                stderr_file = open(stderr_path, 'a')
            
            # Démarrer le processus
            process = subprocess.Popen(
                self.config.cmd,
                shell=True,
                cwd=self.config.workingdir,
                env=env,
                stdout=stdout_file or subprocess.PIPE,
                stderr=stderr_file or subprocess.PIPE,
                preexec_fn=os.setsid  # Créer un nouveau groupe de processus
            )
            
            return process
            
        except Exception as e:
            print(f"❌ Erreur lors du démarrage du processus {self.name}: {e}")
            return None
    
    def _monitor_processes(self):
        """Thread de monitoring des processus"""
        while not self.should_stop and self.state == ProcessState.RUNNING:
            active_processes = []
            
            for i, process in enumerate(self.processes):
                if process.poll() is None:
                    # Processus toujours actif
                    active_processes.append(process)
                else:
                    # Processus terminé
                    exit_code = process.returncode
                    print(f"⚠️  Processus {self.name}[{i}] terminé avec le code {exit_code}")
                    
                    # Vérifier si le code de sortie est attendu
                    expected_exits = self.config.exitcodes
                    if isinstance(expected_exits, int):
                        expected_exits = [expected_exits]
                    
                    if exit_code in expected_exits:
                        print(f"✅ Arrêt normal du processus {self.name}[{i}]")
                    else:
                        # Redémarrage nécessaire selon autorestart
                        if self.config.autorestart == "true" or (
                            self.config.autorestart == "unexpected" and exit_code not in expected_exits
                        ):
                            self._restart_process(i)
            
            self.processes = active_processes
            
            # Vérifier si tous les processus sont morts
            if not self.processes and self.state == ProcessState.RUNNING:
                if self.retry_count < self.config.startretries:
                    print(f"🔄 Redémarrage du processus {self.name} (tentative {self.retry_count + 1})")
                    self._restart_all()
                else:
                    print(f"💀 Processus {self.name} en état FATAL après {self.config.startretries} tentatives")
                    self.state = ProcessState.FATAL
            
            time.sleep(1)  # Vérification toutes les secondes
    
    def _restart_process(self, instance_id: int):
        """Redémarre une instance spécifique du processus"""
        if self.retry_count < self.config.startretries:
            self.retry_count += 1
            time.sleep(self.config.starttime)  # Attendre avant de redémarrer
            
            new_process = self._start_single_process(instance_id)
            if new_process:
                self.processes.append(new_process)
                print(f"🔄 Processus {self.name}[{instance_id}] redémarré")
            else:
                print(f"❌ Échec du redémarrage du processus {self.name}[{instance_id}]")
    
    def _restart_all(self):
        """Redémarre tous les processus"""
        self.retry_count += 1
        self.state = ProcessState.BACKOFF
        time.sleep(self.config.starttime)
        
        self.processes = []
        for i in range(self.config.numprocs):
            process = self._start_single_process(i)
            if process:
                self.processes.append(process)
        
        if self.processes:
            self.state = ProcessState.RUNNING
            print(f"🔄 Tous les processus {self.name} redémarrés")
        else:
            self.state = ProcessState.FATAL
    
    def stop(self):
        """Arrête tous les processus"""
        self.should_stop = True
        self.state = ProcessState.STOPPING
        
        for i, process in enumerate(self.processes):
            if process.poll() is None:
                try:
                    # Envoyer le signal d'arrêt
                    if self.config.stopsignal == "TERM":
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    elif self.config.stopsignal == "USR1":
                        os.killpg(os.getpgid(process.pid), signal.SIGUSR1)
                    else:
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    
                    # Attendre l'arrêt
                    try:
                        process.wait(timeout=self.config.stoptime)
                        print(f"✅ Processus {self.name}[{i}] arrêté proprement")
                    except subprocess.TimeoutExpired:
                        # Forcer l'arrêt
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                        print(f"🔥 Processus {self.name}[{i}] forcé à s'arrêter")
                        
                except Exception as e:
                    print(f"❌ Erreur lors de l'arrêt du processus {self.name}[{i}]: {e}")
        
        self.processes = []
        self.state = ProcessState.STOPPED
        self.stop_time = time.time()
        print(f"⏹️  Processus {self.name} arrêté")
    
    def get_status(self) -> Dict:
        """Retourne le statut du processus"""
        return {
            "name": self.name,
            "state": self.state.value,
            "num_processes": len(self.processes),
            "start_time": self.start_time,
            "stop_time": self.stop_time,
            "retry_count": self.retry_count
        }


class ProcessManager:
    def __init__(self):
        self.processes: Dict[str, ManagedProcess] = {}
        self.running = False
        
    def load_config(self, config_path: str):
        """Charge la configuration depuis un fichier .ini/.conf"""
        from taskmasterd import load_program_configs
        
        configs = load_program_configs(config_path)
        for name, config in configs.items():
            self.processes[name] = ManagedProcess(name, config)
        
        print(f"📋 Configuration chargée: {len(configs)} programmes")
    
    def start_all(self):
        """Démarre tous les processus avec autostart=True"""
        self.running = True
        
        for name, managed_process in self.processes.items():
            if managed_process.config.autostart:
                managed_process.start()
    
    def start_process(self, name: str):
        """Démarre un processus spécifique"""
        if name in self.processes:
            self.processes[name].start()
        else:
            print(f"❌ Processus {name} non trouvé")
    
    def stop_process(self, name: str):
        """Arrête un processus spécifique"""
        if name in self.processes:
            self.processes[name].stop()
        else:
            print(f"❌ Processus {name} non trouvé")
    
    def stop_all(self):
        """Arrête tous les processus"""
        self.running = False
        
        for managed_process in self.processes.values():
            managed_process.stop()
    
    def restart_process(self, name: str):
        """Redémarre un processus spécifique"""
        if name in self.processes:
            self.processes[name].stop()
            time.sleep(1)
            self.processes[name].start()
        else:
            print(f"❌ Processus {name} non trouvé")
    
    def get_status(self) -> List[Dict]:
        """Retourne le statut de tous les processus"""
        return [process.get_status() for process in self.processes.values()]
    
    def wait_for_shutdown(self):
        """Attend la fermeture de tous les processus"""
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Arrêt demandé par l'utilisateur")
            self.stop_all()