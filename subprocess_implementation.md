# 🚀 Implémentation des Subprocess pour Processus en Background

## 📋 Résumé

Ce document explique comment implémenter des subprocess pour lancer des processus en background depuis des fichiers .ini, avec un système de supervision complet.

## 🎯 Objectif

Créer un système de gestion de processus similaire à supervisord qui :
- Lance des processus en arrière-plan depuis des fichiers .ini
- Surveille et redémarre automatiquement les processus
- Gère plusieurs instances par processus
- Offre une interface de contrôle

## 🔧 Implémentation Technique

### 1. Structure des Données

```python
# models.py
from pydantic import BaseModel
from typing import Dict, List, Union, Optional

class ProgramConfig(BaseModel):
    cmd: str                                    # Commande à exécuter
    numprocs: int = 1                          # Nombre d'instances
    workingdir: str                            # Répertoire de travail
    autostart: bool = True                     # Démarrage automatique
    autorestart: str = "unexpected"            # Redémarrage (true/false/unexpected)
    exitcodes: Union[int, List[int]] = 0       # Codes de sortie acceptés
    startretries: int = 3                      # Tentatives de redémarrage
    starttime: int = 5                         # Délai avant redémarrage
    stopsignal: str = "TERM"                   # Signal d'arrêt
    stoptime: int = 10                         # Timeout pour arrêt
    stdout: Optional[str] = None               # Fichier de sortie
    stderr: Optional[str] = None               # Fichier d'erreur
    env: Optional[Dict[str, str]] = None       # Variables d'environnement
```

### 2. Lancement des Processus

```python
def _start_single_process(self, instance_id: int) -> Optional[subprocess.Popen]:
    """Lance une instance du processus en arrière-plan"""
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
            preexec_fn=os.setsid  # ⚠️ IMPORTANT : Nouveau groupe de processus
        )
        
        return process
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du processus: {e}")
        return None
```

### 3. Surveillance en Background

```python
def _monitor_processes(self):
    """Thread de surveillance des processus"""
    while not self.should_stop and self.state == ProcessState.RUNNING:
        active_processes = []
        
        for i, process in enumerate(self.processes):
            if process.poll() is None:
                # Processus toujours actif
                active_processes.append(process)
            else:
                # Processus terminé
                exit_code = process.returncode
                
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
        time.sleep(1)  # Vérification toutes les secondes
```

### 4. Arrêt Propre des Processus

```python
def stop(self):
    """Arrête tous les processus proprement"""
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
                
                # Attendre l'arrêt avec timeout
                try:
                    process.wait(timeout=self.config.stoptime)
                    print(f"✅ Processus {self.name}[{i}] arrêté proprement")
                except subprocess.TimeoutExpired:
                    # Forcer l'arrêt
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    print(f"🔥 Processus {self.name}[{i}] forcé à s'arrêter")
                    
            except Exception as e:
                print(f"❌ Erreur lors de l'arrêt: {e}")
    
    self.processes = []
    self.state = ProcessState.STOPPED
```

## 🔑 Points Clés de l'Implémentation

### 1. Groupes de Processus
```python
preexec_fn=os.setsid  # Crée un nouveau groupe de processus
```
- **Pourquoi** : Isole le processus du processus parent
- **Avantage** : Permet d'arrêter le processus et tous ses enfants

### 2. Threading pour la Surveillance
```python
self.monitor_thread = threading.Thread(target=self._monitor_processes, daemon=True)
self.monitor_thread.start()
```
- **Pourquoi** : Surveillance non-bloquante
- **Avantage** : Chaque processus a son propre thread de surveillance

### 3. Gestion des Signaux
```python
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```
- **Pourquoi** : Arrêt propre du daemon
- **Avantage** : Tous les processus sont arrêtés proprement

### 4. Redirection des Sorties
```python
stdout=stdout_file or subprocess.PIPE,
stderr=stderr_file or subprocess.PIPE,
```
- **Pourquoi** : Éviter le blocage des processus
- **Avantage** : Logs persistants et rotation possible

## 📝 Configuration des Processus

### Fichier .ini d'Exemple
```ini
[worker_process]
cmd = python3 worker.py
numprocs = 4                    # 4 instances en parallèle
umask = 022
workingdir = /app
autostart = true                # Démarrage automatique
autorestart = unexpected        # Redémarrage si crash
exitcodes = 0,1                 # Codes de sortie acceptés
startretries = 3                # 3 tentatives max
starttime = 5                   # Attendre 5s avant redémarrage
stopsignal = TERM               # Signal d'arrêt
stoptime = 10                   # Timeout 10s
stdout = /var/log/worker.stdout # Fichier de sortie
stderr = /var/log/worker.stderr # Fichier d'erreur
env = WORKER_ENV=production     # Variables d'environnement
```

## 🎮 Utilisation

### 1. Mode Daemon
```bash
python3 taskmaster/taskmasterd.py -c config.conf
```
- Lance tous les processus avec `autostart=true`
- Surveille et redémarre automatiquement
- Fonctionne en arrière-plan

### 2. Mode Interactif
```bash
python3 taskmaster/taskmasterctl.py -c config.conf
```
Commandes disponibles :
- `status` : Statut des processus
- `start <nom>` : Démarrer un processus
- `stop <nom>` : Arrêter un processus
- `restart <nom>` : Redémarrer un processus
- `list` : Lister tous les programmes

### 3. Exemple d'Utilisation
```bash
taskmaster> status
🟢 worker_process    | RUNNING    | Instances: 4
🟢 web_server       | RUNNING    | Instances: 2
🔴 batch_job        | STOPPED    | Instances: 0

taskmaster> start batch_job
🚀 Démarrage du processus 'batch_job'...
✅ Processus batch_job démarré avec 1 instances

taskmaster> stop web_server
🛑 Arrêt du processus 'web_server'...
✅ Processus web_server[0] arrêté proprement
✅ Processus web_server[1] arrêté proprement
⏹️  Processus web_server arrêté
```

## 🔄 États des Processus

| État | Description |
|------|-------------|
| **STARTING** | Processus en cours de démarrage |
| **RUNNING** | Processus actif et surveillé |
| **STOPPING** | Processus en cours d'arrêt |
| **STOPPED** | Processus arrêté |
| **FATAL** | Processus en échec définitif |
| **BACKOFF** | Processus en attente de redémarrage |

## 🚨 Gestion des Erreurs

### Redémarrage Automatique
1. **Détection** : Thread de surveillance détecte l'arrêt
2. **Analyse** : Vérification du code de sortie
3. **Décision** : Redémarrage selon `autorestart`
4. **Limite** : Respect de `startretries`

### Arrêt Forcé
1. **Signal gracieux** : `SIGTERM` ou signal configuré
2. **Timeout** : Attente selon `stoptime`
3. **Force** : `SIGKILL` si nécessaire

## 🎯 Avantages de cette Implémentation

✅ **Robustesse** : Gestion complète des erreurs et redémarrages
✅ **Flexibilité** : Configuration détaillée par processus
✅ **Monitoring** : Surveillance en temps réel
✅ **Scalabilité** : Support de multiples instances
✅ **Intégration** : Interface compatible supervisord
✅ **Debugging** : Logs détaillés et statuts précis

## 🎉 Conclusion

Cette implémentation offre une solution complète pour gérer des processus en arrière-plan depuis des fichiers .ini, avec toutes les fonctionnalités nécessaires pour un usage professionnel :

- **Processus en background** via `subprocess.Popen`
- **Surveillance continue** avec threads dédiés
- **Redémarrage automatique** intelligent
- **Gestion des signaux** propre
- **Interface de contrôle** complète
- **Configuration flexible** et extensible

Le système est prêt pour une utilisation en production et peut être facilement étendu selon les besoins spécifiques.