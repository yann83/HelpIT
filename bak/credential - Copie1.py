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
        # Utilise des données système uniques comme base pour le cryptage
        # Combine le nom de l'ordinateur et l'utilisateur
        self.salt = self._get_machine_salt()

    def _get_machine_salt(self):
        """Génère un salt basé sur des informations système"""
        import platform
        import getpass

        # Combine plusieurs informations système uniques
        machine_id = f"{platform.node()}-{getpass.getuser()}-{os.getenv('COMPUTERNAME', '')}"
        # Utilise un salt fixe basé sur la machine
        return machine_id.encode()[:16].ljust(16, b'0')

    def _get_key(self, master_password=""):
        """Génère une clé de cryptage basée sur la machine et optionnellement un mot de passe maître"""
        # Combine des données système pour plus de sécurité
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

    def encrypt_password(self, password, master_password=""):
        """Crypte le mot de passe"""
        fernet = self._get_key(master_password)
        encrypted = fernet.encrypt(password.encode())
        return encrypted.decode()

    def decrypt_password(self, encrypted_password, master_password=""):
        """Décrypte le mot de passe"""
        try:
            fernet = self._get_key(master_password)
            decrypted = fernet.decrypt(encrypted_password.encode())
            return decrypted.decode()
        except Exception as e:
            return None

    def save_to_config(self, encrypted_password, filename="config.json"):
        """Sauvegarde le mot de passe crypté dans config.json"""
        config = {}
        if Path(filename).exists():
            with open(filename, 'r') as f:
                config = json.load(f)

        config['password'] = encrypted_password

        with open(filename, 'w') as f:
            json.dump(config, f, indent=4)

    def load_from_config(self, filename="config.json"):
        """Charge le mot de passe crypté depuis config.json"""
        if not Path(filename).exists():
            return None

        with open(filename, 'r') as f:
            config = json.load(f)
            return config.get('password')


class PasswordDialog:
    def __init__(self, mode="decrypt"):
        """
        mode: "encrypt" pour créer un mot de passe
              "decrypt" pour vérifier un mot de passe
              "change" pour changer le mot de passe
        """
        self.mode = mode
        self.result = None
        self.manager = PasswordManager()

        self.root = tk.Tk()
        self.root.title("Gestion du mot de passe")

        # Ajuster la taille selon le mode
        if mode == "change":
            self.root.geometry("400x350")
        else:
            self.root.geometry("400x200")

        self.root.resizable(False, False)

        # Centrer la fenêtre
        self.root.eval('tk::PlaceWindow . center')

        self._create_widgets()

    def _create_widgets(self):
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(expand=True, fill='both')

        if self.mode == "decrypt":
            label_text = "Entrez votre mot de passe :"
            self._create_simple_password_input(main_frame, label_text)

        elif self.mode == "encrypt":
            label_text = "Créez votre mot de passe :"
            self._create_simple_password_input(main_frame, label_text)

        elif self.mode == "change":
            self._create_change_password_inputs(main_frame)

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

        self.root.bind('<Escape>', lambda e: self._on_cancel())

    def _create_simple_password_input(self, parent, label_text):
        """Créer un simple champ de mot de passe"""
        label = tk.Label(parent, text=label_text, font=('Arial', 10))
        label.pack(pady=(0, 10))

        self.password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.password_entry.pack(pady=(0, 10))
        self.password_entry.focus()

        # Case à cocher pour afficher le mot de passe
        self.show_password_var = tk.BooleanVar()
        show_check = tk.Checkbutton(
            parent,
            text="Afficher le mot de passe",
            variable=self.show_password_var,
            command=self._toggle_password_visibility
        )
        show_check.pack(pady=(0, 10))

        self.password_entry.bind('<Return>', lambda e: self._on_validate())

    def _create_change_password_inputs(self, parent):
        """Créer les champs pour changer le mot de passe"""
        # Ancien mot de passe
        label_old = tk.Label(parent, text="Ancien mot de passe :", font=('Arial', 10))
        label_old.pack(pady=(0, 5))

        self.old_password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.old_password_entry.pack(pady=(0, 15))
        self.old_password_entry.focus()

        # Nouveau mot de passe
        label_new = tk.Label(parent, text="Nouveau mot de passe :", font=('Arial', 10))
        label_new.pack(pady=(0, 5))

        self.new_password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.new_password_entry.pack(pady=(0, 15))

        # Confirmation nouveau mot de passe
        label_confirm = tk.Label(parent, text="Confirmer le nouveau mot de passe :", font=('Arial', 10))
        label_confirm.pack(pady=(0, 5))

        self.confirm_password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.confirm_password_entry.pack(pady=(0, 10))

        # Case à cocher pour afficher les mots de passe
        self.show_password_var = tk.BooleanVar()
        show_check = tk.Checkbutton(
            parent,
            text="Afficher les mots de passe",
            variable=self.show_password_var,
            command=self._toggle_password_visibility
        )
        show_check.pack(pady=(0, 10))

        self.confirm_password_entry.bind('<Return>', lambda e: self._on_validate())

    def _toggle_password_visibility(self):
        """Afficher/masquer les mots de passe"""
        show_value = "" if self.show_password_var.get() else "*"

        if self.mode == "change":
            self.old_password_entry.config(show=show_value)
            self.new_password_entry.config(show=show_value)
            self.confirm_password_entry.config(show=show_value)
        else:
            self.password_entry.config(show=show_value)

    def _on_validate(self):
        if self.mode == "encrypt":
            self._handle_encrypt()
        elif self.mode == "decrypt":
            self._handle_decrypt()
        elif self.mode == "change":
            self._handle_change()

    def _handle_encrypt(self):
        """Gérer la création d'un mot de passe"""
        password = self.password_entry.get()

        if not password:
            messagebox.showwarning("Attention", "Veuillez entrer un mot de passe")
            return

        if len(password) < 4:
            messagebox.showwarning("Attention", "Le mot de passe doit contenir au moins 4 caractères")
            return

        encrypted = self.manager.encrypt_password(password)
        self.manager.save_to_config(encrypted)
        messagebox.showinfo("Succès", "Mot de passe crypté et sauvegardé !")
        self.result = password
        self.root.quit()
        self.root.destroy()

    def _handle_decrypt(self):
        """Gérer la vérification d'un mot de passe"""
        password = self.password_entry.get()

        if not password:
            messagebox.showwarning("Attention", "Veuillez entrer un mot de passe")
            return

        encrypted = self.manager.load_from_config()

        if encrypted is None:
            messagebox.showerror("Erreur", "Aucun mot de passe enregistré dans config.json")
            return

        decrypted = self.manager.decrypt_password(encrypted)

        if decrypted == password:
            messagebox.showinfo("Succès", "Mot de passe correct !")
            self.result = True
            self.root.quit()
            self.root.destroy()
        else:
            messagebox.showerror("Erreur", "Mot de passe incorrect !")
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()

    def _handle_change(self):
        """Gérer le changement de mot de passe"""
        old_password = self.old_password_entry.get()
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        # Vérifications
        if not old_password or not new_password or not confirm_password:
            messagebox.showwarning("Attention", "Veuillez remplir tous les champs")
            return

        if new_password != confirm_password:
            messagebox.showerror("Erreur", "Les nouveaux mots de passe ne correspondent pas")
            self.new_password_entry.delete(0, tk.END)
            self.confirm_password_entry.delete(0, tk.END)
            self.new_password_entry.focus()
            return

        if len(new_password) < 4:
            messagebox.showwarning("Attention", "Le nouveau mot de passe doit contenir au moins 4 caractères")
            return

        if old_password == new_password:
            messagebox.showwarning("Attention", "Le nouveau mot de passe doit être différent de l'ancien")
            return

        # Vérifier l'ancien mot de passe
        encrypted = self.manager.load_from_config()

        if encrypted is None:
            messagebox.showerror("Erreur", "Aucun mot de passe enregistré dans config.json")
            return

        decrypted = self.manager.decrypt_password(encrypted)

        if decrypted != old_password:
            messagebox.showerror("Erreur", "L'ancien mot de passe est incorrect")
            self.old_password_entry.delete(0, tk.END)
            self.old_password_entry.focus()
            return

        # Sauvegarder le nouveau mot de passe
        new_encrypted = self.manager.encrypt_password(new_password)
        self.manager.save_to_config(new_encrypted)

        messagebox.showinfo("Succès", "Mot de passe modifié avec succès !")
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


# ============= EXEMPLES D'UTILISATION =============

def exemple_creer_mot_de_passe():
    """Exemple : Créer et crypter un mot de passe"""
    dialog = PasswordDialog(mode="encrypt")
    result = dialog.show()

    if result:
        print(f"Mot de passe créé : {result}")
    else:
        print("Annulé")


def exemple_verifier_mot_de_passe():
    """Exemple : Vérifier le mot de passe"""
    dialog = PasswordDialog(mode="decrypt")
    result = dialog.show()

    if result:
        print("Accès autorisé !")
        # Votre code ici...
    else:
        print("Accès refusé ou annulé")


def exemple_changer_mot_de_passe():
    """Exemple : Changer le mot de passe"""
    dialog = PasswordDialog(mode="change")
    result = dialog.show()

    if result:
        print("Mot de passe changé avec succès !")
    else:
        print("Changement annulé")


def exemple_cryptage_manuel():
    """Exemple : Crypter/Décrypter manuellement"""
    manager = PasswordManager()

    # Crypter
    mon_password = "MonSuperMotDePasse123!"
    encrypted = manager.encrypt_password(mon_password)
    print(f"Crypté : {encrypted}")

    # Sauvegarder
    manager.save_to_config(encrypted)

    # Charger et décrypter
    loaded = manager.load_from_config()
    decrypted = manager.decrypt_password(loaded)
    print(f"Décrypté : {decrypted}")


if __name__ == "__main__":
    # Décommentez l'exemple que vous souhaitez tester

    # 1. Créer un nouveau mot de passe
    exemple_creer_mot_de_passe()

    # 2. Vérifier le mot de passe
    exemple_verifier_mot_de_passe()

    # 3. Changer le mot de passe
    exemple_changer_mot_de_passe()

    # 4. Cryptage manuel
    # exemple_cryptage_manuel()

    # 5. Workflow complet
    # exemple_complet()


"""
🔐 Sécurité

Le système utilise :

    PBKDF2 avec 100 000 itérations
    SHA-256 pour le hashing
    AES (via Fernet) pour le cryptage
    Salt unique basé sur le nom de la machine et l'utilisateur

Le mot de passe est lié à la machine, donc même si quelqu'un copie le config.json, il ne pourra pas le décrypter sur un autre ordinateur.
📝 Utilisation

Pour créer un mot de passe :

dialog = PasswordDialog(mode="encrypt")
dialog.show()

Pour vérifier un mot de passe :

dialog = PasswordDialog(mode="decrypt")
if dialog.show():
    print("Authentifié !")
    
Mode "change" :

    Demande l'ancien mot de passe
    Demande le nouveau mot de passe
    Demande la confirmation du nouveau mot de passe
    Vérifications :
        ✅ Tous les champs remplis
        ✅ Ancien mot de passe correct
        ✅ Nouveaux mots de passe identiques
        ✅ Nouveau mot de passe différent de l'ancien
        ✅ Longueur minimale (4 caractères)

📝 Utilisation :

# Changer le mot de passe
dialog = PasswordDialog(mode="change")
if dialog.show():
    print("Mot de passe changé !")

Testez avec exemple_changer_mot_de_passe() ! 🚀
"""