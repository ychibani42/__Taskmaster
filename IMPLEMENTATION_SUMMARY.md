# 🎯 Résumé de l'Implémentation - Subprocess en Background

## 📋 Réponse à la Question

**Question :** Comment implémenter les subprocess de manière à lancer les processus dans mes fichiers .ini en background ?

**Réponse :** J'ai créé une implémentation complète d'un système de gestion de processus qui utilise `subprocess.Popen` pour lancer des processus en arrière-plan depuis des fichiers .ini/.conf.

## 🔧 Implémentation Technique

### 1. **Lancement des Processus en Background**

```python
process = subprocess.Popen(
    self.config.cmd,
    shell=True,
    cwd=self.config.workingdir,
    env=env,
    stdout=stdout_file or subprocess.PIPE,
    stderr=stderr_file or subprocess.PIPE,
    preexec_fn=os.setsid  # ⚠️ CLÉ : Nouveau groupe de processus
)
```

**Points clés :**
- `preexec_fn=os.setsid` : Crée un nouveau groupe de processus pour isoler le processus
- `shell=True` : Permet d'exécuter des commandes shell complexes
- Redirection des sorties vers des fichiers pour éviter le blocage
- Variables d'environnement personnalisées

### 2. **Surveillance en Background**

```python
def _monitor_processes(self):
    """Thread de surveillance des processus"""
    while not self.should_stop and self.state == ProcessState.RUNNING:
        for i, process in enumerate(self.processes):
            if process.poll() is None:
                # Processus actif
                active_processes.append(process)
            else:
                # Processus terminé - gérer redémarrage
                self._handle_process_exit(process, i)
        time.sleep(1)  # Vérification toutes les secondes
```

**Points clés :**
- Thread dédié par groupe de processus
- Vérification continue avec `process.poll()`
- Redémarrage automatique selon la configuration
- Gestion des codes de sortie

### 3. **Arrêt Propre**

```python
def stop(self):
    """Arrête tous les processus proprement"""
    for process in self.processes:
        if process.poll() is None:
            # Signal gracieux
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            
            # Attendre avec timeout
            try:
                process.wait(timeout=self.config.stoptime)
            except subprocess.TimeoutExpired:
                # Forcer l'arrêt
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
```

**Points clés :**
- Utilisation de `os.killpg()` pour arrêter le groupe de processus
- Arrêt gracieux avec `SIGTERM` puis forcé avec `SIGKILL`
- Timeout configurable pour chaque processus

## 📁 Structure du Projet

```
taskmaster/
├── models.py           # Configuration des processus (Pydantic)
├── process_manager.py  # Gestionnaire principal des processus
├── taskmasterd.py      # Daemon principal
└── taskmasterctl.py    # Interface de contrôle

example.conf            # Configuration d'exemple
test_processes.conf     # Configuration de test
demo.py                 # Script de démonstration
README.md              # Documentation complète
```

## 🎮 Utilisation

### 1. **Mode Daemon (Background)**
```bash
python3 taskmaster/taskmasterd.py -c example.conf
```

### 2. **Mode Interactif**
```bash
python3 taskmaster/taskmasterctl.py -c example.conf

# Commandes disponibles :
taskmaster> status                  # Statut des processus
taskmaster> start <nom>             # Démarrer un processus
taskmaster> stop <nom>              # Arrêter un processus
taskmaster> restart <nom>           # Redémarrer un processus
taskmaster> list                    # Lister les programmes
```

### 3. **Démonstration**
```bash
python3 demo.py
```

## 📝 Configuration des Processus

```ini
[mon_processus]
cmd = python3 mon_script.py        # Commande à exécuter
numprocs = 4                       # Nombre d'instances
workingdir = /app                  # Répertoire de travail
autostart = true                   # Démarrage automatique
autorestart = unexpected           # Redémarrage si crash
exitcodes = 0,1                    # Codes de sortie acceptés
startretries = 3                   # Tentatives de redémarrage
starttime = 5                      # Délai avant redémarrage
stopsignal = TERM                  # Signal d'arrêt
stoptime = 10                      # Timeout pour arrêt
stdout = /var/log/app.stdout       # Fichier de sortie
stderr = /var/log/app.stderr       # Fichier d'erreur
env = ENV=production,DEBUG=false   # Variables d'environnement
```

## 🔄 Fonctionnalités Avancées

### **Gestion des Multiples Instances**
- Support de `numprocs` pour lancer plusieurs instances
- Fichiers de sortie numérotés automatiquement
- Surveillance individuelle de chaque instance

### **Redémarrage Automatique**
- `autorestart = true` : Redémarre toujours
- `autorestart = false` : Ne redémarre jamais
- `autorestart = unexpected` : Redémarre seulement si crash

### **Surveillance Continue**
- Thread de monitoring par groupe de processus
- Détection des crashes et redémarrage automatique
- Gestion des tentatives limitées (`startretries`)

### **Arrêt Gracieux**
- Signaux configurables (`SIGTERM`, `SIGUSR1`, etc.)
- Timeout configurable pour l'arrêt
- Arrêt forcé si nécessaire

## 🔍 États des Processus

| État | Description |
|------|-------------|
| **STARTING** | Processus en cours de démarrage |
| **RUNNING** | Processus actif et surveillé |
| **STOPPING** | Processus en cours d'arrêt |
| **STOPPED** | Processus arrêté |
| **FATAL** | Processus en échec définitif |
| **BACKOFF** | Processus en attente de redémarrage |

## 🎯 Avantages de cette Implémentation

✅ **Processus en Background** : Utilise `subprocess.Popen` avec `preexec_fn=os.setsid`
✅ **Configuration Flexible** : Fichiers .ini/.conf avec tous les paramètres
✅ **Surveillance Active** : Thread dédié pour chaque groupe de processus
✅ **Redémarrage Intelligent** : Selon les codes de sortie et configuration
✅ **Multiples Instances** : Support de `numprocs` pour la scalabilité
✅ **Interface Complète** : Mode daemon et mode interactif
✅ **Gestion des Erreurs** : Robuste avec gestion des timeouts et signaux
✅ **Logs Structurés** : Redirection des sorties vers des fichiers

## 🚀 Exemple d'Utilisation Complète

### 1. **Créer un fichier de configuration**
```ini
[web_server]
cmd = python3 -m http.server 8000
numprocs = 2
workingdir = /var/www
autostart = true
autorestart = unexpected
exitcodes = 0
startretries = 3
starttime = 5
stopsignal = TERM
stoptime = 10
stdout = /var/log/web_server.stdout
stderr = /var/log/web_server.stderr
env = PORT=8000
```

### 2. **Lancer le daemon**
```bash
python3 taskmaster/taskmasterd.py -c config.conf
```

### 3. **Contrôler les processus**
```bash
python3 taskmaster/taskmasterctl.py -c config.conf
taskmaster> status
🟢 web_server        | RUNNING    | Instances: 2
```

## 🔧 Points Techniques Importants

### **Groupes de Processus**
```python
preexec_fn=os.setsid  # Crée un nouveau groupe
os.killpg(os.getpgid(process.pid), signal.SIGTERM)  # Arrête le groupe
```

### **Threading Non-Bloquant**
```python
self.monitor_thread = threading.Thread(target=self._monitor_processes, daemon=True)
self.monitor_thread.start()
```

### **Gestion des Signaux**
```python
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

### **Redirection des Sorties**
```python
stdout_file = open(stdout_path, 'a')
stderr_file = open(stderr_path, 'a')
```

## 🎉 Conclusion

Cette implémentation fournit une solution complète et robuste pour lancer des processus en arrière-plan depuis des fichiers .ini, avec toutes les fonctionnalités d'un système de supervision professionnel :

- **Processus en background** avec isolation complète
- **Configuration flexible** via fichiers .ini
- **Surveillance continue** et redémarrage automatique
- **Interface de contrôle** intuitive
- **Gestion d'erreurs** robuste
- **Extensibilité** facile

Le système est prêt pour une utilisation en production et peut être facilement adapté selon les besoins spécifiques.

---

**Fichiers créés :**
- `taskmaster/models.py` : Modèles de configuration
- `taskmaster/process_manager.py` : Gestionnaire principal
- `taskmaster/taskmasterd.py` : Daemon
- `taskmaster/taskmasterctl.py` : Interface de contrôle
- `example.conf` : Configuration d'exemple
- `demo.py` : Script de démonstration
- `README.md` : Documentation complète
- `subprocess_implementation.md` : Guide technique détaillé