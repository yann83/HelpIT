# Gestionnaire de Processus - Documentation en Français

## Résumé des Modifications

J'ai créé un module complet `process.py` qui gère l'affichage et la suppression de processus distants via une interface graphique Tkinter.

## Fichiers Créés/Modifiés

### 1. process.py (NOUVEAU)
Fichier principal contenant la classe `ProcessManager` avec toutes les fonctionnalités demandées :

**Fonctionnalités principales :**
- Lecture du fichier CSV de processus
- Affichage dans une fenêtre avec liste déroulante
- Boutons verts "Kill" à gauche de chaque processus
- Bouton devient rouge et inactif après suppression réussie
- Fonction "Refresh" pour recharger la liste
- Support de la molette de souris pour le défilement
- Gestion complète des erreurs avec logging

**Architecture de la classe :**
```python
class ProcessManager:
    def __init__(self, csv_filename, psexec_manager, current_ip, 
                 current_hostname, psexec_path, log_path)
    def _create_widgets(self)          # Crée l'interface graphique
    def _load_processes(self)          # Charge les processus depuis le CSV
    def _kill_process(self, process_name)  # Tue un processus
    def _refresh_process_list(self)    # Rafraîchit la liste
    def show(self)                     # Affiche la fenêtre
```

### 2. main.py (MODIFIÉ)
Le fichier `main.py` a été mis à jour pour intégrer le nouveau module :

**Changements effectués :**
1. Ajout de l'import : `from process import ProcessManager`
2. Modification de la fonction `show_processes()` pour :
   - Générer le CSV des processus via PsExec
   - Créer une instance de `ProcessManager`
   - Passer tous les paramètres nécessaires (IP, hostname, chemins)

**Code de la nouvelle fonction show_processes :**
```python
def show_processes(self):
    """
    Display process manager window for the remote machine
    """
    if not self.current_ip:
        messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
        return

    try:
        if sys.platform == 'win32':
            # Get processes list using PsExec
            self.psexec.get_processes_to_csv()
            csv_filename = Path(LOG_PATH / f"{self.current_hostname}_processus.csv")
            
            if csv_filename.exists():
                # Create and show the ProcessManager window
                process_manager = ProcessManager(
                    csv_filename=csv_filename,
                    psexec_manager=self.psexec,
                    current_ip=self.current_ip,
                    current_hostname=self.current_hostname,
                    psexec_path=self.psexec_path,
                    log_path=str(LOG_PATH)
                )
            else:
                messagebox.showerror("Erreur", "Impossible de générer la liste des processus")
    except Exception as e:
        logging.error(f"Erreur ouverture gestionnaire de processus: {e}")
        messagebox.showerror("Erreur", "Impossible d'ouvrir le gestionnaire de processus")
```

### 3. README.md (NOUVEAU)
Documentation complète en anglais expliquant :
- Vue d'ensemble du module
- Architecture de la classe
- Utilisation et intégration
- Format du CSV
- Gestion des erreurs
- Améliorations futures possibles

### 4. example_usage.py (NOUVEAU)
Fichier d'exemples avec deux scénarios :
- **Standalone** : Utilisation indépendante du ProcessManager
- **Intégré** : Simulation simplifiée de l'intégration dans l'application principale

## Comment Utiliser

### Dans votre application HelpIT :

1. **Copiez les fichiers** dans votre projet :
   - `process.py` → à la racine (même niveau que `main.py`)
   - `main.py` → remplace votre fichier existant

2. **Lancez l'application** normalement

3. **Pour afficher les processus** :
   - Sélectionnez une cible (IP ou nom)
   - Cliquez sur le bouton "Processus"
   - Une nouvelle fenêtre s'ouvre avec la liste

4. **Pour tuer un processus** :
   - Cliquez sur le bouton vert "Kill" à côté du processus
   - Confirmez l'action
   - Le bouton devient rouge si réussi

## Détails Techniques

### Récupération des Paramètres
Tous les paramètres nécessaires sont passés depuis `main.py` :
- `self.current_ip` → Adresse IP de la machine distante
- `self.current_hostname` → Nom de la machine
- `self.psexec_path` → Chemin vers PsExec64.exe
- `str(LOG_PATH)` → Chemin du dossier de logs
- `self.psexec` → Instance de PsExecManager

### Fonctionnement de kill_process
```python
def _kill_process(self, process_name):
    # 1. Demande confirmation à l'utilisateur
    # 2. Appelle self.psexec_manager.kill_process(process_name)
    # 3. Si retour = 1 : bouton rouge + désactivé
    # 4. Si retour = 0 : message d'erreur
    # 5. Log de toutes les opérations
```

### Interface Graphique
- **Fenêtre principale** : Tkinter Toplevel (fenêtre secondaire)
- **Liste déroulante** : Canvas + Frame pour gérer le défilement
- **Boutons** : tk.Button avec couleurs personnalisées
  - Vert (#4CAF50) : État initial (actif)
  - Rouge (#F44336) : Après suppression réussie (inactif)

## Commentaires dans le Code

Tous les commentaires sont en **anglais** comme demandé :
```python
# Create a frame for each process row
process_frame = ttk.Frame(self.scrollable_frame)

# Create kill button (initially green)
kill_btn = tk.Button(...)

# Store button reference for later updates
self.process_buttons[process_name] = kill_btn
```

## Points d'Attention

1. **Fichier CSV** : Le format doit avoir une colonne "name" avec les noms de processus
2. **PsExec** : Nécessite PsExec64.exe dans le dossier `bin`
3. **Droits** : L'utilisateur doit avoir les droits admin sur la machine distante
4. **Windows uniquement** : Le module utilise `sys.platform == 'win32'`

## Avantages de cette Implémentation

✅ **Module séparé** : Code organisé dans un fichier dédié
✅ **Classe complète** : Toute la logique encapsulée
✅ **Annotations** : Commentaires détaillés en anglais
✅ **Réutilisable** : Peut être utilisé dans d'autres projets
✅ **Gestion d'erreurs** : Try/except partout avec logging
✅ **Interface intuitive** : Boutons colorés, confirmation, feedback visuel
✅ **Scalable** : Fonctionne avec des listes de centaines de processus

## Tests Suggérés

1. **Test basique** :
   - Lancer l'application
   - Valider une machine cible
   - Ouvrir le gestionnaire de processus
   - Vérifier que la liste s'affiche

2. **Test de suppression** :
   - Sélectionner un processus non critique (ex: notepad)
   - Cliquer sur "Kill"
   - Vérifier que le bouton devient rouge
   - Confirmer la suppression sur la machine distante

3. **Test de rafraîchissement** :
   - Cliquer sur "Refresh List"
   - Vérifier que la liste se met à jour
   - Les processus tués doivent avoir disparu

## Dépannage

**Problème** : La fenêtre ne s'ouvre pas
- Vérifier que le CSV a été créé dans le dossier `tmp`
- Vérifier les logs dans `HelpIT.log`

**Problème** : Bouton ne devient pas rouge
- La fonction `kill_process` a peut-être échoué
- Vérifier les droits sur la machine distante
- Consulter les logs

**Problème** : Erreur d'import
- Vérifier que `process.py` est au bon endroit
- S'assurer que l'import est présent dans `main.py`

## Support

Pour toute question ou amélioration :
- Consultez le README.md (en anglais)
- Regardez example_usage.py pour des exemples
- Vérifiez les logs dans HelpIT.log

Bon développement ! 🚀
