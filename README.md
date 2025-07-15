# 🎯 Taskmaster - Système de Gestion de Processus

## 📋 Description

Taskmaster est un système de gestion de processus similaire à supervisord, qui permet de lancer et superviser des processus en arrière-plan depuis des fichiers de configuration `.ini` ou `.conf`.

## 🚀 Fonctionnalités

### ✅ Gestion des processus
- **Lancement en arrière-plan** : Utilise `subprocess.Popen` avec `preexec_fn=os.setsid`
- **Surveillance continue** : Thread dédié pour chaque processus
- **Redémarrage automatique** : Selon les paramètres `autorestart` et `startretries`
- **Gestion des signaux** : Arrêt propre avec `SIGTERM`, `SIGUSR1`, etc.
- **Plusieurs instances** : Support de `numprocs` pour lancer plusieurs instances

### ⚙️ Configuration
- **Fichiers .ini/.conf** : Configuration simple et lisible
- **Variables d'environnement** : Support des variables personnalisées
- **Redirection des sorties** : `stdout` et `stderr` vers des fichiers
- **Codes de sortie** : Gestion des codes de sortie attendus

### 🎮 Interfaces
- **Mode daemon** : Processus en arrière-plan permanent
- **Mode interactif** : Interface en ligne de commande
- **Contrôle en temps réel** : Start, stop, restart, status

## 📁 Structure du projet

```
taskmaster/
├── models.py           # Modèles de données (ProgramConfig)
├── process_manager.py  # Gestionnaire de processus principal
├── taskmasterd.py      # Daemon principal
└── taskmasterctl.py    # Interface de contrôle

example.conf            # Configuration d'exemple
foo.conf               # Configuration existante
demo.py                # Script de démonstration
```

## 🔧 Installation et utilisation

### 1. Prérequis
```bash
pip install pydantic
```

### 2. Configuration

Créez un fichier `.conf` avec vos processus :

```ini
[mon_processus]
cmd = python3 mon_script.py
numprocs = 2
umask = 022
workingdir = /tmp
autostart = true
autorestart = unexpected
exitcodes = 0,1
startretries = 3
starttime = 5
stopsignal = TERM
stoptime = 10
stdout = /tmp/mon_processus.stdout
stderr = /tmp/mon_processus.stderr
env = VAR1=value1,VAR2=value2
```

### 3. Lancement

#### Mode daemon (arrière-plan)
```bash
python3 taskmaster/taskmasterd.py -c example.conf
```

#### Mode interactif
```bash
python3 taskmaster/taskmasterctl.py -c example.conf
```

#### Démonstration
```bash
python3 demo.py
```

## 📖 Configuration détaillée

### Paramètres disponibles

| Paramètre | Type | Description | Défaut |
|-----------|------|-------------|--------|
| `cmd` | string | Commande à exécuter | **Requis** |
| `numprocs` | int | Nombre d'instances | 1 |
| `umask` | string | Masque de permissions | "022" |
| `workingdir` | string | Répertoire de travail | **Requis** |
| `autostart` | boolean | Démarrage automatique | true |
| `autorestart` | string | Redémarrage auto (true/false/unexpected) | "unexpected" |
| `exitcodes` | int/list | Codes de sortie acceptés | 0 |
| `startretries` | int | Tentatives de redémarrage | 3 |
| `starttime` | int | Délai avant redémarrage (sec) | 5 |
| `stopsignal` | string | Signal d'arrêt (TERM/USR1/etc) | "TERM" |
| `stoptime` | int | Délai d'arrêt forcé (sec) | 10 |
| `stdout` | string | Fichier de sortie standard | None |
| `stderr` | string | Fichier de sortie d'erreur | None |
| `env` | string | Variables d'environnement | None |

### Exemples de configuration

#### Processus simple
```ini
[test_script]
cmd = python3 test.py
numprocs = 1
workingdir = /tmp
autostart = true
autorestart = true
```

#### Processus avec plusieurs instances
```ini
[worker]
cmd = python3 worker.py
numprocs = 4
workingdir = /app
autostart = true
autorestart = unexpected
stdout = /var/log/worker.stdout
stderr = /var/log/worker.stderr
env = WORKER_ID=%(process_num)s
```

#### Processus avec gestion d'erreur
```ini
[fragile_service]
cmd = ./fragile_service.sh
numprocs = 1
workingdir = /opt/service
autostart = true
autorestart = true
exitcodes = 0,1,2
startretries = 5
starttime = 3
stopsignal = USR1
stoptime = 15
```

## 🎮 Commandes du contrôleur

### Contrôle des processus
```bash
taskmaster> start <nom>          # Démarrer un processus
taskmaster> stop <nom>           # Arrêter un processus  
taskmaster> restart <nom>        # Redémarrer un processus
taskmaster> start all            # Démarrer tous les processus
taskmaster> stop all             # Arrêter tous les processus
taskmaster> restart all          # Redémarrer tous les processus
```

### Monitoring
```bash
taskmaster> status               # Statut de tous les processus
taskmaster> status <nom>         # Statut d'un processus spécifique
taskmaster> list                 # Liste des programmes configurés
```

### Configuration
```bash
taskmaster> reload               # Recharger la configuration
taskmaster> help                 # Aide
taskmaster> quit                 # Quitter
```

## 🔄 Implémentation des subprocess

### Lancement des processus
```python
process = subprocess.Popen(
    config.cmd,
    shell=True,
    cwd=config.workingdir,
    env=env,
    stdout=stdout_file or subprocess.PIPE,
    stderr=stderr_file or subprocess.PIPE,
    preexec_fn=os.setsid  # Nouveau groupe de processus
)
```

### Surveillance en arrière-plan
```python
def _monitor_processes(self):
    """Thread de monitoring des processus"""
    while not self.should_stop and self.state == ProcessState.RUNNING:
        for i, process in enumerate(self.processes):
            if process.poll() is None:
                # Processus actif
                active_processes.append(process)
            else:
                # Processus terminé - redémarrer si nécessaire
                self._handle_process_exit(process, i)
        time.sleep(1)
```

### Arrêt propre
```python
def stop(self):
    """Arrête tous les processus"""
    for process in self.processes:
        if process.poll() is None:
            # Envoyer le signal d'arrêt
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            
            # Attendre l'arrêt avec timeout
            try:
                process.wait(timeout=self.config.stoptime)
            except subprocess.TimeoutExpired:
                # Forcer l'arrêt
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
```

## 🔍 États des processus

- **STARTING** : Processus en cours de démarrage
- **RUNNING** : Processus actif et surveillé
- **STOPPING** : Processus en cours d'arrêt
- **STOPPED** : Processus arrêté
- **FATAL** : Processus en échec après épuisement des tentatives
- **BACKOFF** : Processus en attente avant redémarrage

## 🧪 Tests et exemples

### Lancer la démonstration
```bash
python3 demo.py
```

### Tester avec les fichiers d'exemple
```bash
# Mode daemon
python3 taskmaster/taskmasterd.py -c example.conf

# Mode interactif
python3 taskmaster/taskmasterctl.py -c example.conf
```

### Créer des processus de test
La démonstration crée automatiquement des scripts de test dans `test_scripts/`:
- `test_counter.py` : Compteur simple
- `test_memory.py` : Moniteur de mémoire
- `test_failing.py` : Processus qui échoue parfois

## 🛠️ Développement et extension

### Ajout de nouvelles fonctionnalités
1. Modifier `models.py` pour de nouveaux paramètres
2. Étendre `ProcessManager` pour la logique
3. Ajouter des commandes dans `TaskmasterController`

### Gestion des erreurs
- Validation des configurations avec Pydantic
- Gestion des exceptions dans les threads
- Logging détaillé des états des processus

## 📚 Points techniques clés

- **Threading** : Un thread par processus pour la surveillance
- **Signaux** : Gestion propre de SIGTERM, SIGINT, etc.
- **Groupes de processus** : `os.setsid()` pour isoler les processus
- **Fichiers de sortie** : Redirection vers des fichiers avec rotation
- **Variables d'environnement** : Héritage et personnalisation
- **Codes de sortie** : Gestion des codes attendus vs inattendus

## 🚨 Gestion des erreurs

Le système gère automatiquement :
- Processus qui ne démarrent pas
- Processus qui s'arrêtent inopinément
- Épuisement des tentatives de redémarrage
- Signaux d'arrêt non respectés (SIGKILL en dernier recours)
- Fichiers de configuration invalides

## 🎉 Conclusion

Ce système offre une implémentation complète de gestion de processus en arrière-plan, avec toutes les fonctionnalités nécessaires pour une utilisation en production :

- **Robustesse** : Gestion d'erreurs et redémarrage automatique
- **Flexibilité** : Configuration détaillée et personnalisable
- **Monitoring** : Surveillance en temps réel et statuts détaillés
- **Contrôle** : Interface interactive et mode daemon
- **Extensibilité** : Architecture modulaire et extensible