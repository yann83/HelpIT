# Gestionnaire de Services - Documentation en Français

## Vue d'Ensemble

Le module `service.py` fournit une interface graphique complète pour afficher et gérer les services Windows sur des machines distantes via PsExec.

## 📋 Caractéristiques Principales

### Affichage
- **3 colonnes** : ID, Nom, État du service
- **Liste déroulante** : Support de centaines de services
- **Statuts colorés** : Identification visuelle rapide
- **Molette de souris** : Navigation fluide

### Contrôle des Services
- **Bouton Stop (Rouge)** : Arrête un service en cours d'exécution
- **Bouton Run (Vert)** : Démarre un service arrêté
- **Bouton Restart (Bleu)** : Redémarre un service (arrêt puis démarrage)

### Fonctionnalités Avancées
- **Mise à jour automatique** : L'état se rafraîchit après chaque action
- **Confirmation** : Demande de confirmation avant chaque action
- **Logging complet** : Toutes les opérations sont loguées
- **Gestion d'erreurs** : Messages clairs en cas de problème

## 🏗️ Architecture

### Classe ServiceManager

```python
class ServiceManager:
    """
    Gestionnaire de services avec interface graphique Tkinter
    """
    
    # Attributs principaux
    - csv_filename: Path          # Fichier CSV des services
    - psexec_manager: PsExecManager  # Gestionnaire PsExec
    - current_ip: str             # IP de la machine distante
    - current_hostname: str       # Nom de la machine
    - service_widgets: dict       # Références aux widgets
    - state_colors: dict          # Couleurs par état
```

### Méthodes Principales

| Méthode | Description | Retour |
|---------|-------------|--------|
| `__init__(...)` | Initialise le gestionnaire | None |
| `_create_widgets()` | Crée l'interface graphique | None |
| `_load_services()` | Charge les services du CSV | None |
| `_update_service_status(id)` | Met à jour l'affichage | None |
| `_stop_service(id)` | Arrête un service | None |
| `_start_service(id)` | Démarre un service | None |
| `_restart_service(id)` | Redémarre un service | None |
| `_refresh_service_list()` | Rafraîchit la liste | None |

## 📄 Format du Fichier CSV

Le CSV utilise le **point-virgule (`;`)** comme séparateur :

```csv
id;name;etat
AdobeARMservice;Adobe Acrobat Update Service;STOPPED
Audiosrv;Audio Windows;RUNNING
BFE;Moteur de filtrage de base;RUNNING
BITS;Service de transfert intelligent en arrière-plan;RUNNING
```

### Colonnes

1. **id** : Identifiant court du service (utilisé pour les commandes)
2. **name** : Nom complet d'affichage du service
3. **etat** : État actuel (RUNNING, STOPPED, etc.)

## 🎨 États et Couleurs

Le module reconnaît 7 états de service avec code couleur :

| État | Code | Couleur | Hexadécimal | Signification |
|------|------|---------|-------------|---------------|
| RUNNING | 4 | Vert | #4CAF50 | Service en cours d'exécution |
| STOPPED | 1 | Rouge | #F44336 | Service arrêté |
| START_PENDING | 2 | Orange | #FF9800 | Service en cours de démarrage |
| STOP_PENDING | 3 | Orange | #FF9800 | Service en cours d'arrêt |
| CONTINUE_PENDING | 5 | Orange | #FF9800 | Service en cours de reprise |
| PAUSE_PENDING | 6 | Orange | #FF9800 | Service en cours de pause |
| PAUSED | 7 | Ambre | #FFC107 | Service en pause |

## 🔧 Intégration dans main.py

### Modifications Apportées

```python
# 1. Import du module
from service import ServiceManager

# 2. Fonction open_services() modifiée
def open_services(self):
    """
    Display service manager window for the remote machine
    """
    if not self.current_ip:
        messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
        return

    try:
        if sys.platform == 'win32':
            # Génération du CSV
            self.psexec.get_services_to_csv()
            csv_filename = Path(LOG_PATH / f"{self.current_hostname}_services.csv")
            
            if csv_filename.exists():
                # Création du ServiceManager
                service_manager = ServiceManager(
                    csv_filename=csv_filename,
                    psexec_manager=self.psexec,
                    current_ip=self.current_ip,
                    current_hostname=self.current_hostname,
                    psexec_path=self.psexec_path,
                    log_path=str(LOG_PATH)
                )
```

## 🎮 Utilisation

### Depuis l'Application HelpIT

1. **Lancez HelpIT** et connectez-vous
2. **Validez une cible** (entrez IP ou nom de machine)
3. **Cliquez sur "Services"**
4. **La fenêtre ServiceManager s'ouvre** avec la liste des services

### Actions Disponibles

#### Arrêter un Service
1. Cliquez sur le bouton rouge **[Stop]**
2. Confirmez l'action dans la boîte de dialogue
3. Le statut se met à jour automatiquement (vert → rouge)
4. Un message de succès s'affiche

#### Démarrer un Service
1. Cliquez sur le bouton vert **[Run]**
2. Confirmez l'action
3. Le statut se met à jour (rouge → vert)
4. Message de confirmation

#### Redémarrer un Service
1. Cliquez sur le bouton bleu **[Restart]**
2. Confirmez l'action
3. Le service s'arrête puis redémarre
4. Le statut final s'affiche

#### Rafraîchir la Liste
1. Cliquez sur **[Refresh List]** en bas
2. Le CSV est régénéré
3. La liste est rechargée
4. Tous les états sont à jour

## 🔌 Méthodes PsExec Utilisées

Le ServiceManager utilise 4 méthodes de la classe PsExecManager :

### 1. get_service_status(service_id)

```python
# Vérifie l'état d'un service
# Retourne : 1 si RUNNING, 0 sinon

status = self.psexec_manager.get_service_status("Audiosrv")
if status == 1:
    print("Le service Audio est en cours d'exécution")
else:
    print("Le service Audio est arrêté")
```

### 2. stop_service(service_id)

```python
# Arrête un service
# Retourne : True si succès, False sinon

result = self.psexec_manager.stop_service("Audiosrv")
if result:
    print("Service arrêté avec succès")
```

### 3. start_service(service_id)

```python
# Démarre un service
# Retourne : True si succès, False sinon

result = self.psexec_manager.start_service("Audiosrv")
if result:
    print("Service démarré avec succès")
```

### 4. restart_service(service_id)

```python
# Redémarre un service (stop + start)
# Retourne : True si succès, False sinon

result = self.psexec_manager.restart_service("Audiosrv")
if result:
    print("Service redémarré avec succès")
```

## 💡 Détails Techniques

### Flux d'Exécution d'une Action

```
┌─────────────────────────────────────────────────────────┐
│ 1. Utilisateur clique sur [Stop/Run/Restart]           │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Boîte de confirmation affichée                       │
│    "Êtes-vous sûr de vouloir arrêter le service ?"     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼ (Si Oui)
┌─────────────────────────────────────────────────────────┐
│ 3. Appel de la méthode PsExec appropriée               │
│    - stop_service(id)                                   │
│    - start_service(id)                                  │
│    - restart_service(id)                                │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Exécution de la commande PsExec distante            │
│    PsExec \\IP sc stop/start ServiceName               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ 5. Si succès : Appel de _update_service_status()       │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ 6. Vérification de l'état avec get_service_status()    │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ 7. Mise à jour du label de statut                      │
│    - Texte : RUNNING/STOPPED                            │
│    - Couleur : Vert/Rouge                               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│ 8. Message de confirmation à l'utilisateur              │
└─────────────────────────────────────────────────────────┘
```

### Stockage des Widgets

Les widgets sont stockés dans un dictionnaire pour faciliter les mises à jour :

```python
self.service_widgets = {
    'Audiosrv': {
        'status_label': <Label widget>,
        'stop_btn': <Button widget>,
        'run_btn': <Button widget>,
        'restart_btn': <Button widget>
    },
    'BFE': {
        'status_label': <Label widget>,
        # ...
    }
}
```

### Pourquoi Utiliser l'ID et pas le Nom ?

⚠️ **IMPORTANT** : Les commandes Windows utilisent l'ID court, pas le nom complet !

```python
# ✅ CORRECT
psexec.stop_service("Audiosrv")

# ❌ INCORRECT (ne fonctionnera pas)
psexec.stop_service("Audio Windows")
```

C'est pourquoi le CSV contient les deux :
- **id** : Pour les commandes (ex: "Audiosrv")
- **name** : Pour l'affichage (ex: "Audio Windows")

## 🎯 Différences avec ProcessManager

| Caractéristique | ProcessManager | ServiceManager |
|-----------------|----------------|----------------|
| **Colonnes CSV** | 1 (name) | 3 (id, name, etat) |
| **Séparateur CSV** | Virgule `,` | Point-virgule `;` |
| **Boutons par ligne** | 1 (Kill) | 3 (Stop, Run, Restart) |
| **Comportement bouton** | Désactivé après succès | Toujours actifs |
| **Mise à jour état** | N/A | Automatique après action |
| **Couleurs** | Bouton uniquement | Label de statut |
| **Largeur fenêtre** | 600px | 900px (plus large) |

## 🔍 Tests Recommandés

### Test 1 : Affichage Initial
```
1. Lancer HelpIT
2. Valider une cible
3. Cliquer sur "Services"
✓ La fenêtre s'ouvre
✓ Tous les services sont affichés
✓ Les états sont colorés correctement
```

### Test 2 : Arrêt d'un Service
```
1. Trouver un service en RUNNING (ex: "Print Spooler")
2. Cliquer sur [Stop]
3. Confirmer
✓ Le statut passe de vert (RUNNING) à rouge (STOPPED)
✓ Message de succès affiché
✓ Le service est effectivement arrêté sur la machine
```

### Test 3 : Démarrage d'un Service
```
1. Trouver un service en STOPPED
2. Cliquer sur [Run]
3. Confirmer
✓ Le statut passe de rouge (STOPPED) à vert (RUNNING)
✓ Message de succès affiché
✓ Le service démarre sur la machine distante
```

### Test 4 : Redémarrage
```
1. Trouver un service en RUNNING
2. Cliquer sur [Restart]
3. Confirmer
✓ Le service redémarre
✓ Le statut final est RUNNING (vert)
✓ Message de succès
```

### Test 5 : Rafraîchissement
```
1. Noter l'état de plusieurs services
2. Modifier manuellement un service sur la machine distante
3. Cliquer sur [Refresh List]
✓ La liste se recharge
✓ Les nouveaux états s'affichent
✓ Aucune erreur
```

## 🐛 Dépannage

### Problème : "Accès refusé"

**Cause** : Droits insuffisants sur la machine distante

**Solution** :
1. Lancer HelpIT en administrateur
2. Vérifier que le compte a les droits admin sur la machine distante
3. S'assurer que le service "Remote Registry" est actif

### Problème : Le service ne démarre pas

**Cause** : Service désactivé ou dépendances manquantes

**Solution** :
1. Vérifier le type de démarrage (services.msc)
2. Vérifier les dépendances du service
3. Consulter les logs Windows sur la machine distante

### Problème : L'état ne se met pas à jour

**Cause** : Problème de communication PsExec

**Solution** :
1. Vérifier la connexion réseau
2. Tester PsExec manuellement
3. Vérifier les règles de pare-feu

### Problème : CSV introuvable

**Cause** : Génération du CSV échouée

**Solution** :
1. Vérifier que PsExec64.exe existe dans `bin/`
2. Consulter `HelpIT.log` pour les erreurs
3. Vérifier que le dossier `tmp/` existe

## 📊 Interface Graphique

### Disposition des Éléments

```
┌──────────────────────────────────────────────────────────────────┐
│                Services on HOSTNAME (IP)                          │
│                     [Titre centré]                                │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ [Stop] [Run] [Restart]  id: Display Name       [STATUS]   │  │
│  │ [Stop] [Run] [Restart]  id: Display Name       [STATUS]   │  │
│  │ [Stop] [Run] [Restart]  id: Display Name       [STATUS]   │  │
│  │ ...                                                        │  │
│  │ (liste déroulante)                                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│              [Refresh List]      [Close]                          │
│                   [Boutons bas de fenêtre]                        │
└──────────────────────────────────────────────────────────────────┘
```

### Dimensions

- **Largeur fenêtre** : 900px (plus large que ProcessManager)
- **Hauteur fenêtre** : 600px
- **Largeur boutons** : 8 caractères
- **Largeur label statut** : 15 caractères

## 📚 Commentaires dans le Code

Tous les commentaires sont en **anglais** comme demandé :

```python
# Create Stop button
stop_btn = tk.Button(...)

# Update the status label with new state and color
status_label.config(text=status_text, bg=color)

# Call the stop_service method from PsExecManager
result = self.psexec_manager.stop_service(service_id)
```

## ✨ Points Forts

✅ **Interface intuitive** : 3 boutons colorés par fonction  
✅ **Feedback visuel** : États colorés et messages clairs  
✅ **Robuste** : Gestion complète des erreurs  
✅ **Performant** : Supporte des centaines de services  
✅ **Bien documenté** : Commentaires anglais, docstrings complètes  
✅ **Intégré** : S'intègre parfaitement dans HelpIT  

## 🚀 Installation

1. **Copiez `service.py`** dans votre projet HelpIT
2. **Remplacez `main.py`** par la version modifiée
3. **Testez** : Validez une cible et cliquez sur "Services"

## 📝 Checklist

- [ ] Fichier `service.py` copié
- [ ] Fichier `main.py` mis à jour
- [ ] Import ajouté dans main.py
- [ ] PsExec64.exe présent dans `bin/`
- [ ] Premier test effectué
- [ ] Service arrêté avec succès
- [ ] Service démarré avec succès
- [ ] Rafraîchissement testé

---

**Développé pour HelpIT avec ❤️**  
*Module compatible Windows 11, Python 3.6+, PyCharm Community*
