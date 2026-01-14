import tkinter as tk
from tkinter import messagebox
import json
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from pathlib import Path


class PasswordManager:
    def __init__(self):
        self.salt = self._get_machine_salt()
        self.master_password = None  # Stockage du mot de passe maître en mémoire

    def _get_machine_salt(self):
        """Génère un salt basé sur des informations système"""
        import platform
        import getpass

        machine_id = f"{platform.node()}-{getpass.getuser()}-{os.getenv('COMPUTERNAME', '')}"
        return machine_id.encode()[:16].ljust(16, b'0')

    def _get_key(self, master_password=""):
        """Génère une clé de cryptage basée sur la machine et le mot de passe maître"""
        import platform

        key_base = f"{platform.node()}{os.getenv('USERNAME', '')}{master_password}"

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_base.encode()))
        return Fernet(key)

    def set_master_password(self, master_password):
        """Définit le mot de passe maître en mémoire"""
        self.master_password = master_password

    def get_master_password(self):
        """Récupère le mot de passe maître stocké en mémoire"""
        return self.master_password

    def clear_master_password(self):
        """Efface le mot de passe maître de la mémoire"""
        self.master_password = None

    def encrypt_password(self, password, master_password=None):
        """Crypte le mot de passe avec le mot de passe maître"""
        if master_password is None:
            master_password = self.master_password or ""

        fernet = self._get_key(master_password)
        encrypted = fernet.encrypt(password.encode())
        return encrypted.decode()

    def decrypt_password(self, encrypted_password, master_password=None):
        """Décrypte le mot de passe avec le mot de passe maître"""
        try:
            if master_password is None:
                master_password = self.master_password or ""

            fernet = self._get_key(master_password)
            decrypted = fernet.decrypt(encrypted_password.encode())
            return decrypted.decode()
        except Exception as e:
            return None

    def save_to_config(self, encrypted_password, filename="config.json", username=None, domain=None):
        """Sauvegarde le mot de passe crypté, username et domain dans config.json"""
        config = {}
        if Path(filename).exists():
            with open(filename, 'r') as f:
                config = json.load(f)

        config['password'] = encrypted_password

        if username is not None:
            config['username'] = username

        if domain is not None:
            config['domain'] = domain

        with open(filename, 'w') as f:
            json.dump(config, f, indent=4)

    def load_from_config(self, filename="config.json"):
        """Charge les données depuis config.json"""
        if not Path(filename).exists():
            return None

        with open(filename, 'r') as f:
            config = json.load(f)
            return config

    def config_exists(self, filename="config.json"):
        """Vérifie si le fichier config.json existe"""
        return Path(filename).exists()

    def get_decrypted_password(self, filename="config.json"):
        """Récupère et décrypte le mot de passe admin à la volée"""
        config = self.load_from_config(filename)
        if config and 'password' in config:
            return self.decrypt_password(config['password'])
        return None

    def get_username(self, filename="config.json"):
        """Récupère le username depuis config.json"""
        config = self.load_from_config(filename)
        return config.get('username') if config else None

    def get_domain(self, filename="config.json"):
        """Récupère le domain depuis config.json"""
        config = self.load_from_config(filename)
        return config.get('domain') if config else None


class PasswordDialog:
    def __init__(self, mode="master", manager=None):
        """
        mode: "create" pour créer les identifiants (étape 1)
              "master" pour demander le mot de passe maître
              "change_master" pour changer le mot de passe maître
        manager: Instance de PasswordManager (partagée)
        """
        self.mode = mode
        self.result = None
        self.manager = manager if manager else PasswordManager()

        self.root = tk.Tk()
        self.show_password_var = tk.BooleanVar()

        # Titre selon le mode
        if mode == "create":
            self.root.title("Création des identifiants")
            self.root.geometry("400x450")
        elif mode == "master":
            self.root.title("Mot de passe maître")
            self.root.geometry("400x200")
        elif mode == "change_master":
            self.root.title("Changer le mot de passe maître")
            self.root.geometry("400x300")

        self.root.resizable(False, False)
        self.root.eval('tk::PlaceWindow . center')

        self._create_widgets()

    def _create_widgets(self):
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(expand=True, fill='both')

        if self.mode == "create":
            self._create_create_inputs(main_frame)
        elif self.mode == "master":
            self._create_master_input(main_frame)
        elif self.mode == "change_master":
            self._create_change_master_inputs(main_frame)

        # Boutons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))

        validate_btn = tk.Button(
            button_frame,
            text="Valider",
            command=self._on_validate,
            width=10,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        validate_btn.pack(side='left', padx=5)

        cancel_btn = tk.Button(
            button_frame,
            text="Annuler",
            command=self._on_cancel,
            width=10,
            bg='#f44336',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        cancel_btn.pack(side='left', padx=5)

        self.root.bind('<Return>', lambda e: self._on_validate())
        self.root.bind('<Escape>', lambda e: self._on_cancel())

    def _create_create_inputs(self, parent):
        """Créer les champs pour la création initiale (étape 1)"""
        # Username
        tk.Label(parent, text="Nom d'utilisateur :", font=('Arial', 10, 'bold')).pack(pady=(0, 5))
        self.username_entry = tk.Entry(parent, font=('Arial', 12), width=30)
        self.username_entry.pack(pady=(0, 10))

        # Password admin
        tk.Label(parent, text="Mot de passe administrateur :", font=('Arial', 10, 'bold')).pack(pady=(0, 5))
        self.admin_password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.admin_password_entry.pack(pady=(0, 10))

        # Confirm admin password
        tk.Label(parent, text="Confirmer le mot de passe admin :", font=('Arial', 10)).pack(pady=(0, 5))
        self.confirm_admin_password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.confirm_admin_password_entry.pack(pady=(0, 10))

        # Domain
        tk.Label(parent, text="Domaine :", font=('Arial', 10, 'bold')).pack(pady=(0, 5))
        self.domain_entry = tk.Entry(parent, font=('Arial', 12), width=30)
        self.domain_entry.pack(pady=(0, 10))

        # Master password
        tk.Label(parent, text="Mot de passe maître :", font=('Arial', 10, 'bold')).pack(pady=(0, 5))
        self.master_password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.master_password_entry.pack(pady=(0, 10))

        # Confirm master password
        tk.Label(parent, text="Confirmer le mot de passe maître :", font=('Arial', 10)).pack(pady=(0, 5))
        self.confirm_master_password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.confirm_master_password_entry.pack(pady=(0, 10))

        # Checkbox
        tk.Checkbutton(
            parent,
            text="Afficher les mots de passe",
            variable=self.show_password_var,
            command=self._toggle_password_visibility
        ).pack(pady=(0, 10))

        self.username_entry.focus()

    def _create_master_input(self, parent):
        """Créer le champ pour demander le mot de passe maître"""
        tk.Label(parent, text="Entrez le mot de passe maître :", font=('Arial', 12, 'bold')).pack(pady=(10, 15))

        self.master_password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.master_password_entry.pack(pady=(0, 10))
        self.master_password_entry.focus()

        tk.Checkbutton(
            parent,
            text="Afficher le mot de passe",
            variable=self.show_password_var,
            command=self._toggle_password_visibility
        ).pack(pady=(0, 10))

    def _create_change_master_inputs(self, parent):
        """Créer les champs pour changer le mot de passe maître"""
        # Ancien mot de passe maître
        tk.Label(parent, text="Ancien mot de passe maître :", font=('Arial', 10, 'bold')).pack(pady=(0, 5))
        self.old_master_password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.old_master_password_entry.pack(pady=(0, 15))
        self.old_master_password_entry.focus()

        # Nouveau mot de passe maître
        tk.Label(parent, text="Nouveau mot de passe maître :", font=('Arial', 10, 'bold')).pack(pady=(0, 5))
        self.new_master_password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.new_master_password_entry.pack(pady=(0, 15))

        # Confirmation
        tk.Label(parent, text="Confirmer le nouveau mot de passe :", font=('Arial', 10)).pack(pady=(0, 5))
        self.confirm_master_password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.confirm_master_password_entry.pack(pady=(0, 10))

        tk.Checkbutton(
            parent,
            text="Afficher les mots de passe",
            variable=self.show_password_var,
            command=self._toggle_password_visibility
        ).pack(pady=(0, 10))

    def _toggle_password_visibility(self):
        """Basculer la visibilité des mots de passe"""
        show_value = "" if self.show_password_var.get() else "*"

        if self.mode == "create":
            if hasattr(self, 'admin_password_entry'):
                self.admin_password_entry.config(show=show_value)
            if hasattr(self, 'confirm_admin_password_entry'):
                self.confirm_admin_password_entry.config(show=show_value)
            if hasattr(self, 'master_password_entry'):
                self.master_password_entry.config(show=show_value)
            if hasattr(self, 'confirm_master_password_entry'):
                self.confirm_master_password_entry.config(show=show_value)
        elif self.mode == "master":
            if hasattr(self, 'master_password_entry'):
                self.master_password_entry.config(show=show_value)
        elif self.mode == "change_master":
            if hasattr(self, 'old_master_password_entry'):
                self.old_master_password_entry.config(show=show_value)
            if hasattr(self, 'new_master_password_entry'):
                self.new_master_password_entry.config(show=show_value)
            if hasattr(self, 'confirm_master_password_entry'):
                self.confirm_master_password_entry.config(show=show_value)

    def _on_validate(self):
        if self.mode == "create":
            self._handle_create()
        elif self.mode == "master":
            self._handle_master()
        elif self.mode == "change_master":
            self._handle_change_master()

    def _handle_create(self):
        """Gérer la création initiale des identifiants (étape 1)"""
        username = self.username_entry.get().strip()
        admin_password = self.admin_password_entry.get()
        confirm_admin = self.confirm_admin_password_entry.get()
        domain = self.domain_entry.get().strip()
        master_password = self.master_password_entry.get()
        confirm_master = self.confirm_master_password_entry.get()

        # Validations
        if not username:
            messagebox.showwarning("Attention", "Veuillez entrer un nom d'utilisateur")
            self.username_entry.focus()
            return

        if not admin_password:
            messagebox.showwarning("Attention", "Veuillez entrer un mot de passe administrateur")
            self.admin_password_entry.focus()
            return

        if len(admin_password) < 4:
            messagebox.showwarning("Attention", "Le mot de passe admin doit contenir au moins 4 caractères")
            self.admin_password_entry.focus()
            return

        if admin_password != confirm_admin:
            messagebox.showerror("Erreur", "Les mots de passe administrateur ne correspondent pas")
            self.admin_password_entry.delete(0, tk.END)
            self.confirm_admin_password_entry.delete(0, tk.END)
            self.admin_password_entry.focus()
            return

        if not domain:
            messagebox.showwarning("Attention", "Veuillez entrer un domaine")
            self.domain_entry.focus()
            return

        if not master_password:
            messagebox.showwarning("Attention", "Veuillez entrer un mot de passe maître")
            self.master_password_entry.focus()
            return

        if len(master_password) < 4:
            messagebox.showwarning("Attention", "Le mot de passe maître doit contenir au moins 4 caractères")
            self.master_password_entry.focus()
            return

        if master_password != confirm_master:
            messagebox.showerror("Erreur", "Les mots de passe maître ne correspondent pas")
            self.master_password_entry.delete(0, tk.END)
            self.confirm_master_password_entry.delete(0, tk.END)
            self.master_password_entry.focus()
            return

        # Crypter le mot de passe admin avec le mot de passe maître
        encrypted = self.manager.encrypt_password(admin_password, master_password)
        self.manager.save_to_config(encrypted, username=username, domain=domain)

        # Stocker le mot de passe maître en mémoire
        self.manager.set_master_password(master_password)

        messagebox.showinfo("Succès", "Identifiants créés et sauvegardés avec succès !")
        self.result = True
        self.root.quit()
        self.root.destroy()

    def _handle_master(self):
        """Gérer la saisie du mot de passe maître (étape 2)"""
        master_password = self.master_password_entry.get()

        if not master_password:
            messagebox.showwarning("Attention", "Veuillez entrer le mot de passe maître")
            return

        # Vérifier si le mot de passe maître est correct
        config = self.manager.load_from_config()

        if not config or 'password' not in config:
            messagebox.showerror("Erreur", "Aucun mot de passe enregistré")
            return

        decrypted = self.manager.decrypt_password(config['password'], master_password)

        if decrypted is not None:
            # Stocker le mot de passe maître en mémoire
            self.manager.set_master_password(master_password)
            messagebox.showinfo("Succès", "Authentification réussie !")
            self.result = True
            self.root.quit()
            self.root.destroy()
        else:
            messagebox.showerror("Erreur", "Mot de passe maître incorrect !")
            self.master_password_entry.delete(0, tk.END)
            self.master_password_entry.focus()

    def _handle_change_master(self):
        """Gérer le changement du mot de passe maître (étape 5)"""
        old_master = self.old_master_password_entry.get()
        new_master = self.new_master_password_entry.get()
        confirm_master = self.confirm_master_password_entry.get()

        if not old_master or not new_master or not confirm_master:
            messagebox.showwarning("Attention", "Veuillez remplir tous les champs")
            return

        if new_master != confirm_master:
            messagebox.showerror("Erreur", "Les nouveaux mots de passe maître ne correspondent pas")
            self.new_master_password_entry.delete(0, tk.END)
            self.confirm_master_password_entry.delete(0, tk.END)
            self.new_master_password_entry.focus()
            return

        if len(new_master) < 4:
            messagebox.showwarning("Attention", "Le nouveau mot de passe maître doit contenir au moins 4 caractères")
            return

        if old_master == new_master:
            messagebox.showwarning("Attention", "Le nouveau mot de passe maître doit être différent de l'ancien")
            return

        # Vérifier l'ancien mot de passe maître
        config = self.manager.load_from_config()

        if not config or 'password' not in config:
            messagebox.showerror("Erreur", "Aucun mot de passe enregistré")
            return

        # Décrypter avec l'ancien mot de passe maître
        admin_password = self.manager.decrypt_password(config['password'], old_master)

        if admin_password is None:
            messagebox.showerror("Erreur", "L'ancien mot de passe maître est incorrect")
            self.old_master_password_entry.delete(0, tk.END)
            self.old_master_password_entry.focus()
            return

        # Re-crypter le mot de passe admin avec le nouveau mot de passe maître
        new_encrypted = self.manager.encrypt_password(admin_password, new_master)

        # Conserver username et domain
        username = config.get('username')
        domain = config.get('domain')

        self.manager.save_to_config(new_encrypted, username=username, domain=domain)

        # Mettre à jour le mot de passe maître en mémoire
        self.manager.set_master_password(new_master)

        messagebox.showinfo("Succès", "Mot de passe maître modifié avec succès !")
        self.result = True
        self.root.quit()
        self.root.destroy()

    def _on_cancel(self):
        self.result = False
        self.root.quit()
        self.root.destroy()

    def show(self):
        """Affiche la fenêtre et retourne le résultat"""
        self.root.mainloop()
        return self.result


# ============= CLASSE PRINCIPALE POUR L'APPLICATION =============

class Application:
    """
    Classe principale qui gère l'authentification et l'accès aux credentials
    """

    def __init__(self):
        self.manager = PasswordManager()
        self.authenticated = False

    def demarrer(self):
        """
        Point d'entrée principal - Gère le workflow complet
        """
        print("\n" + "=" * 60)
        print("DÉMARRAGE DE L'APPLICATION")
        print("=" * 60)

        # Étape 6: Vérifier si config.json existe
        if not self.manager.config_exists():
            print("\n⚠️  Aucune configuration trouvée")
            print("→ Création des identifiants...")

            # Étape 1: Créer les identifiants
            dialog = PasswordDialog(mode="create", manager=self.manager)
            result = dialog.show()

            if not result:
                print("❌ Création annulée. Fermeture de l'application.")
                return False

            print("✓ Configuration créée avec succès")
            self.authenticated = True

        else:
            # Étape 2: Demander le mot de passe maître
            print("\n🔐 Authentification requise")
            dialog = PasswordDialog(mode="master", manager=self.manager)
            result = dialog.show()

            if not result:
                print("❌ Authentification annulée. Fermeture de l'application.")
                return False

            print("✓ Authentification réussie")
            self.authenticated = True

        # Étape 3: Le mot de passe maître reste en mémoire
        print(f"✓ Mot de passe maître stocké en mémoire")

        return True

    def executer_fonction_admin(self, nom_fonction):
        """
        Étape 4: Exécute une fonction qui a besoin du mot de passe admin
        Le mot de passe est décrypté à la volée avec le master password en mémoire
        """
        if not self.authenticated:
            print("❌ Non authentifié")
            return None

        print(f"\n--- Exécution de '{nom_fonction}' ---")

        # Récupérer les credentials décryptés à la volée
        username = self.manager.get_username()
        password = self.manager.get_decrypted_password()
        domain = self.manager.get_domain()

        if password is None:
            print("❌ Impossible de décrypter le mot de passe")
            return None

        print(f"✓ Credentials récupérés pour {username}@{domain}")

        # Simuler l'utilisation du mot de passe admin
        # Dans votre vraie application, vous utiliseriez ces credentials ici
        return {
            'username': username,
            'password': password,
            'domain': domain
        }

    def changer_mot_de_passe_maitre(self):
        """
        Étape 5: Permet de changer le mot de passe maître
        """
        if not self.authenticated:
            print("❌ Non authentifié")
            return False

        print("\n🔄 Changement du mot de passe maître")
        dialog = PasswordDialog(mode="change_master", manager=self.manager)
        result = dialog.show()

        if result:
            print("✓ Mot de passe maître changé avec succès")
            return True
        else:
            print("❌ Changement annulé")
            return False

    def fermer(self):
        """
        Nettoie la mémoire à la fermeture
        """
        print("\n🔒 Fermeture sécurisée de l'application")
        self.manager.clear_master_password()
        self.authenticated = False
        print("✓ Mot de passe maître effacé de la mémoire")


# ============= EXEMPLES D'UTILISATION =============

def exemple_workflow_complet():
    """
    Exemple du workflow complet selon vos spécifications
    """
    # Créer l'application
    app = Application()

    # Démarrer (gère automatiquement la création ou l'authentification)
    if not app.demarrer():
        return

    print("\n" + "=" * 60)
    print("APPLICATION PRÊTE")
    print("=" * 60)

    # Simuler l'utilisation normale de l'application
    print("\n--- UTILISATION NORMALE ---")

    # Exemple 1: Exécuter une fonction qui a besoin du mot de passe admin
    credentials = app.executer_fonction_admin("Fonction_1")
    if credentials:
        print(f"  → Username: {credentials['username']}")
        print(f"  → Password: {credentials['password']}")
        print(f"  → Domain: {credentials['domain']}")

    # Exemple 2: Exécuter une autre fonction
    print("\n")
    credentials = app.executer_fonction_admin("Fonction_2")
    if credentials:
        print(f"  → Mot de passe récupéré: {credentials['password']}")

    # Exemple 3: Changer le mot de passe maître (optionnel)
    print("\n--- TEST: CHANGEMENT DU MOT DE PASSE MAÎTRE ---")
    reponse = input("Voulez-vous changer le mot de passe maître? (o/n): ")
    if reponse.lower() == 'o':
        app.changer_mot_de_passe_maitre()

    # Fermeture de l'application
    app.fermer()


def exemple_utilisation_simple():
    """
    Exemple d'utilisation simple dans votre main.py
    """
    # Initialiser l'application
    app = Application()

    # Démarrer (authentification)
    if not app.demarrer():
        return

    # Votre code applicatif ici...
    # Le mot de passe maître est maintenant en mémoire

    # Quand vous avez besoin du mot de passe admin:
    creds = app.executer_fonction_admin("Ma_Fonction")

    # Utiliser les credentials...
    if creds:
        # Faire quelque chose avec creds['password']
        pass

    # À la fermeture
    app.fermer()


def exemple_integration_main():
    """
    Exemple d'intégration dans votre main.py
    """
    print("=" * 60)
    print("EXEMPLE D'INTÉGRATION DANS MAIN.PY")
    print("=" * 60)

    # Au début de votre main.py
    app = Application()

    if not app.demarrer():
        print("Impossible de démarrer l'application")
        return

    # Votre application continue normalement
    print("\n→ Application démarrée, le mot de passe maître est en mémoire")

    # Exemple: fonction qui a besoin du mot de passe admin
    def ma_fonction_qui_utilise_admin_password():
        creds = app.executer_fonction_admin("ma_fonction")
        if creds:
            admin_pwd = creds['password']
            # Utiliser admin_pwd pour vos opérations
            print(f"  Opération effectuée avec le password: {admin_pwd}")

    # Appeler votre fonction
    ma_fonction_qui_utilise_admin_password()

    # Une autre fonction
    def autre_fonction():
        creds = app.executer_fonction_admin("autre_fonction")
        if creds:
            print(f"  Domaine utilisé: {creds['domain']}")

    autre_fonction()

    # Fermeture
    app.fermer()


if __name__ == "__main__":
    print("=" * 60)
    print("GESTIONNAIRE DE MOTS DE PASSE AVEC MOT DE PASSE MAÎTRE")
    print("=" * 60)

    # Workflow complet (recommandé)
    exemple_workflow_complet()

    # Autres exemples (décommentez pour tester)
    # exemple_utilisation_simple()
    # exemple_integration_main()
