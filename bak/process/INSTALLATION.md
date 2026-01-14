# Guide d'Installation et Configuration

## Installation Rapide

### Étape 1 : Copier les Fichiers

1. **Copiez `process.py`** dans le répertoire de votre projet HelpIT (au même niveau que `main.py`)

2. **Remplacez `main.py`** par la version modifiée fournie

3. **Vérifiez la structure** :
   ```
   HelpIT/
   ├── main.py          ✓ (version modifiée)
   ├── process.py       ✓ (nouveau fichier)
   ├── psexec.py        ✓ (existant)
   ├── credential.py    ✓ (existant)
   └── bin/
       └── PsExec64.exe ✓
   ```

### Étape 2 : Vérifier les Dépendances

Toutes les dépendances devraient déjà être installées si votre application HelpIT fonctionne :

```python
# Bibliothèques requises (déjà présentes)
import tkinter as tk
from tkinter import ttk, messagebox
import csv
import logging
from pathlib import Path
```

### Étape 3 : Test de Base

1. Lancez `main.py` depuis PyCharm
2. Validez une cible (entrez un nom de machine ou IP)
3. Cliquez sur le bouton "Processus" ou "Show Processes"
4. La fenêtre ProcessManager devrait s'ouvrir

## Configuration dans PyCharm

### Création d'un Projet

Si vous partez de zéro dans PyCharm :

1. **Ouvrir PyCharm Community**
2. **File → New Project**
3. **Location** : Choisissez votre dossier HelpIT
4. **Python Interpreter** : Utilisez l'interpréteur Python installé
5. **Create**

### Ajouter les Fichiers

1. **Faites glisser** les fichiers dans l'explorateur de projet
2. Ou **Right-click → New → Python File** et copiez le contenu

### Configuration de l'Exécution

1. **Right-click sur `main.py` → Run 'main'**
2. Ou créez une configuration :
   - **Run → Edit Configurations**
   - **+ → Python**
   - **Script path** : Sélectionnez `main.py`
   - **Working directory** : Répertoire du projet
   - **OK**

## Configuration de PsExec

### Téléchargement

1. Téléchargez PsExec depuis Microsoft :
   https://docs.microsoft.com/en-us/sysinternals/downloads/psexec

2. Extrayez `PsExec64.exe` dans le dossier `bin/` de votre projet

### Permissions

Sur Windows 11 :
1. **Lancez l'application en tant qu'administrateur** (important !)
2. Acceptez la licence PsExec lors du premier lancement

## Structure des Dossiers

Créez les dossiers nécessaires s'ils n'existent pas :

```
HelpIT/
├── bin/              # Outils externes
│   └── PsExec64.exe
├── tmp/              # Fichiers temporaires (créé automatiquement)
│   ├── *.csv
│   └── *.log
└── *.py              # Fichiers Python
```

## Permissions et Sécurité

### Droits Administrateur

Pour que le gestionnaire de processus fonctionne :

1. **L'utilisateur** configuré dans `config.json` doit avoir :
   - Droits administrateur sur la machine distante
   - Accès au partage admin$ (`\\machine\admin$`)

2. **Pare-feu** : Autoriser :
   - Ports SMB (445)
   - Partages administratifs
   - Exécution de commandes distantes

### Credential Configuration

Vérifiez dans `config.json` :

```json
{
    "username": "votre_identifiant",
    "password": "chiffré",
    "domain": "VOTRE_DOMAINE"
}
```

## Dépannage

### Problème 1 : ImportError pour 'process'

**Erreur** :
```
ImportError: cannot import name 'ProcessManager' from 'process'
```

**Solution** :
- Vérifiez que `process.py` est dans le même dossier que `main.py`
- Assurez-vous qu'il n'y a pas de fichier `process.pyc` corrompu
- Redémarrez PyCharm

### Problème 2 : Fenêtre ne s'ouvre pas

**Erreur** : Aucune fenêtre ne s'affiche après clic sur "Processus"

**Solution** :
- Vérifiez que le CSV existe dans `tmp/`
- Consultez `HelpIT.log` pour les erreurs
- Vérifiez que `self.current_ip` est défini

### Problème 3 : PsExec introuvable

**Erreur** :
```
FileNotFoundError: PsExec64.exe introuvable
```

**Solution** :
- Téléchargez PsExec64.exe
- Placez-le dans le dossier `bin/`
- Vérifiez le chemin dans le code : `BIN_PATH / "PsExec64.exe"`

### Problème 4 : Accès refusé

**Erreur** : Les processus ne peuvent pas être tués

**Solution** :
- Lancez l'application en tant qu'administrateur
- Vérifiez les droits sur la machine distante
- Vérifiez que le pare-feu autorise PsExec

### Problème 5 : Encodage CSV

**Erreur** : Caractères bizarres dans les noms de processus

**Solution** :
- Le fichier utilise UTF-8
- Si problème : modifiez `encoding='utf-8'` dans `_load_processes()`

## Tests Recommandés

### Test 1 : Affichage de Base

```python
# Objectif : Vérifier que la fenêtre s'ouvre
1. Lancer l'application
2. Valider une cible
3. Cliquer sur "Processus"
4. ✓ La fenêtre ProcessManager s'ouvre
5. ✓ La liste des processus s'affiche
```

### Test 2 : Défilement

```python
# Objectif : Vérifier le défilement
1. Ouvrir ProcessManager avec >20 processus
2. Utiliser la molette de la souris
3. ✓ La liste défile correctement
4. ✓ Tous les processus sont accessibles
```

### Test 3 : Suppression Simple

```python
# Objectif : Tuer un processus non critique
1. Lancer notepad.exe sur la machine distante
2. Ouvrir ProcessManager
3. Trouver "notepad" dans la liste
4. Cliquer sur [Kill]
5. Confirmer
6. ✓ Le bouton devient rouge
7. ✓ Notepad se ferme sur la machine distante
```

### Test 4 : Rafraîchissement

```python
# Objectif : Tester la fonction Refresh
1. Noter les processus affichés
2. Lancer un nouveau programme sur la machine distante
3. Cliquer sur "Refresh List"
4. ✓ Le nouveau processus apparaît
5. ✓ Les processus tués ont disparu
```

### Test 5 : Gestion d'Erreurs

```python
# Objectif : Tester la robustesse
1. Essayer de tuer un processus système protégé
2. ✓ Message d'erreur approprié
3. ✓ L'application ne plante pas
4. ✓ Le log contient l'erreur
```

## Logs et Débogage

### Fichiers de Log

```
HelpIT/
├── HelpIT.log              # Log principal de l'application
└── tmp/
    └── session_*.log       # Logs de sessions
```

### Informations Loguées

Le module ProcessManager logue :
- Chargement des processus
- Tentatives de suppression
- Succès et échecs
- Erreurs d'accès fichier

### Activer le Debug

Pour plus de détails, modifiez dans `main.py` :

```python
# Ligne 30
logging.basicConfig(
    filename=MAIN_LOG,
    level=logging.DEBUG,  # Changez INFO en DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

## Conseils de Développement

### Modifier l'Interface

Pour personnaliser les couleurs des boutons :

```python
# Dans process.py, ligne ~138
kill_btn = tk.Button(
    process_frame,
    text="Kill",
    bg="#4CAF50",     # Changez cette couleur (vert)
    fg="white",
    width=8
)

# Ligne ~195
button.config(bg="#F44336")  # Changez cette couleur (rouge)
```

### Ajouter des Colonnes

Pour afficher plus d'informations (PID, mémoire, etc.) :

1. Modifiez `psexec.py` pour inclure plus de données dans le CSV
2. Modifiez `_load_processes()` pour lire les nouvelles colonnes
3. Ajoutez des labels supplémentaires dans `process_frame`

### Performance

Pour de grandes listes (>100 processus) :
- La solution Canvas + Scrollbar est optimale
- Envisagez un filtrage/recherche si >200 processus
- Utilisez un TreeView pour des colonnes multiples

## Checklist Avant Utilisation

- [ ] Python 3.6+ installé
- [ ] PyCharm Community configuré
- [ ] PsExec64.exe dans `bin/`
- [ ] `config.json` correctement rempli
- [ ] Droits administrateur disponibles
- [ ] Pare-feu configuré
- [ ] Tests de base effectués
- [ ] Logs vérifiés

## Support et Documentation

- **README.md** : Documentation complète en anglais
- **DOCUMENTATION_FR.md** : Guide détaillé en français
- **ARCHITECTURE.txt** : Diagrammes et schémas
- **example_usage.py** : Exemples de code

---

**Note** : Ce module a été développé pour Windows 11 avec PyCharm Community, sans Docker ni WSL, conformément à vos préférences. Tous les commentaires de code sont en anglais pour faciliter la diffusion internationale.
