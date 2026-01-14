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
        # Use unique system data as the base for encryption
        # Combines computer name and username
        self.salt = self._get_machine_salt()

    def _get_machine_salt(self):
        """Generate a salt based on system information"""
        import platform
        import getpass

        # Combine multiple unique system information
        machine_id = f"{platform.node()}-{getpass.getuser()}-{os.getenv('COMPUTERNAME', '')}"
        # Use a fixed salt based on the machine
        return machine_id.encode()[:16].ljust(16, b'0')

    def _get_key(self, master_password=""):
        """Generate an encryption key based on the machine and optionally a master password"""
        # Combine system data for more security
        import platform

        #key_base = f"{platform.node()}{os.getenv('USERNAME', '')}{master_password}"
        key_base = f"{platform.node()}{master_password}"

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_base.encode()))
        return Fernet(key)

    def encrypt_password(self, password, master_password=""):
        """Encrypt the password"""
        fernet = self._get_key(master_password)
        encrypted = fernet.encrypt(password.encode())
        return encrypted.decode()

    def decrypt_password(self, encrypted_password, master_password=""):
        """Decrypt the password"""
        try:
            fernet = self._get_key(master_password)
            decrypted = fernet.decrypt(encrypted_password.encode())
            return decrypted.decode()
        except Exception as e:
            return None

    def save_to_config(self, encrypted_password, filename="config.json", username=None, domain=None):
        """Save the encrypted password, username, and domain to config.json"""
        config = {}
        if Path(filename).exists():
            with open(filename, 'r') as f:
                config = json.load(f)

        # Update password
        config['password'] = encrypted_password

        # Update username if provided
        if username is not None:
            config['username'] = username

        # Update domain if provided
        if domain is not None:
            config['domain'] = domain

        with open(filename, 'w') as f:
            json.dump(config, f, indent=4)

    def load_from_config(self, filename="config.json"):
        """Load the encrypted password from config.json"""
        if not Path(filename).exists():
            return None

        with open(filename, 'r') as f:
            config = json.load(f)
            return config.get('password')

    def get_decrypted_password(self, master_password):
        """
        Decrypt and return the password using the master password

        Args:
            master_password (str): The master password to use for decryption

        Returns:
            str: The decrypted password, or None if decryption fails
        """
        # Load the encrypted password from config.json
        encrypted_password = self.load_from_config()

        if encrypted_password is None:
            print("Error: No password found in config.json")
            return None

        # Decrypt the password using the master password
        decrypted_password = self.decrypt_password(encrypted_password, master_password)

        if decrypted_password is None:
            print("Error: Failed to decrypt password. Invalid master password?")
            return None

        return decrypted_password


class PasswordDialog:
    def __init__(self, mode="decrypt"):
        """
        mode: "encrypt" to create a password
              "decrypt" to verify a password
              "change" to change the password
        """
        self.mode = mode
        self.result = None
        self.manager = PasswordManager()

        self.root = tk.Tk()
        self.root.title("Password Management")

        # Adjust size according to mode
        if mode == "change":
            self.root.geometry("400x450")  # Increased height for master password field
        elif mode == "encrypt":
            self.root.geometry("400x550")  # Increased height for all new fields
        else:
            self.root.geometry("400x200")

        self.root.resizable(False, False)

        # Center the window
        self.root.eval('tk::PlaceWindow . center')

        self._create_widgets()

    def _create_widgets(self):
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(expand=True, fill='both')

        if self.mode == "decrypt":
            label_text = "Enter your master password:"
            self._create_simple_password_input(main_frame, label_text)

        elif self.mode == "encrypt":
            self._create_encrypt_inputs(main_frame)

        elif self.mode == "change":
            self._create_change_password_inputs(main_frame)

        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))

        validate_btn = tk.Button(
            button_frame,
            text="Validate",
            command=self._on_validate,
            width=10,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        validate_btn.pack(side='left', padx=5)

        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=10,
            bg='#f44336',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        cancel_btn.pack(side='left', padx=5)

        self.root.bind('<Escape>', lambda e: self._on_cancel())

    def _create_simple_password_input(self, parent, label_text):
        """Create a simple master password field for decryption/validation"""
        label = tk.Label(parent, text=label_text, font=('Arial', 10))
        label.pack(pady=(0, 10))

        # Master password entry field (hidden with *)
        self.master_password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.master_password_entry.pack(pady=(0, 10))
        self.master_password_entry.focus()

        # Checkbox to show/hide password
        self.show_password_var = tk.BooleanVar()
        show_check = tk.Checkbutton(
            parent,
            text="Show password",
            #variable=self.show_password_var,
            command=self._toggle_password_visibility
        )
        show_check.pack(pady=(0, 10))

        # Bind Enter key to validation
        self.master_password_entry.bind('<Return>', lambda e: self._on_validate())

    def _create_encrypt_inputs(self, parent):
        """Create input fields for username, password, confirmation, domain, master password and confirmation"""
        # Username field
        label_username = tk.Label(parent, text="Username:", font=('Arial', 10))
        label_username.pack(pady=(0, 5))

        self.username_entry = tk.Entry(parent, font=('Arial', 12), width=30)
        self.username_entry.pack(pady=(0, 10))
        self.username_entry.focus()

        # Password field (hidden with *)
        label_password = tk.Label(parent, text="Create your password:", font=('Arial', 10))
        label_password.pack(pady=(0, 5))

        self.password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.password_entry.pack(pady=(0, 10))

        # Password confirmation field (hidden with *)
        label_password_confirm = tk.Label(parent, text="Confirm your password:", font=('Arial', 10))
        label_password_confirm.pack(pady=(0, 5))

        self.password_confirm_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.password_confirm_entry.pack(pady=(0, 10))

        # Domain field
        label_domain = tk.Label(parent, text="Domain:", font=('Arial', 10))
        label_domain.pack(pady=(0, 5))

        self.domain_entry = tk.Entry(parent, font=('Arial', 12), width=30)
        self.domain_entry.pack(pady=(0, 10))

        # Master password field (hidden with *)
        label_master = tk.Label(parent, text="Master password:", font=('Arial', 10))
        label_master.pack(pady=(0, 5))

        self.master_password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.master_password_entry.pack(pady=(0, 10))

        # Master password confirmation field (hidden with *)
        label_master_confirm = tk.Label(parent, text="Confirm master password:", font=('Arial', 10))
        label_master_confirm.pack(pady=(0, 5))

        self.master_password_confirm_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.master_password_confirm_entry.pack(pady=(0, 10))

        # Checkbox to show/hide all passwords
        self.show_password_var = tk.BooleanVar()
        show_check = tk.Checkbutton(
            parent,
            text="Show passwords",
            #variable=self.show_password_var,
            command=self._toggle_password_visibility
        )
        show_check.pack(pady=(0, 10))

        # Bind Enter key to validation on the last field
        self.master_password_confirm_entry.bind('<Return>', lambda e: self._on_validate())

    def _create_change_password_inputs(self, parent):
        """Create fields for changing password with master password validation"""
        # Old password field (hidden with *)
        label_old = tk.Label(parent, text="Old password:", font=('Arial', 10))
        label_old.pack(pady=(0, 5))

        self.old_password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.old_password_entry.pack(pady=(0, 10))
        self.old_password_entry.focus()

        # New password field (hidden with *)
        label_new = tk.Label(parent, text="New password:", font=('Arial', 10))
        label_new.pack(pady=(0, 5))

        self.new_password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.new_password_entry.pack(pady=(0, 10))

        # Confirm new password field (hidden with *)
        label_confirm = tk.Label(parent, text="Confirm new password:", font=('Arial', 10))
        label_confirm.pack(pady=(0, 5))

        self.confirm_password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.confirm_password_entry.pack(pady=(0, 10))

        # Master password field (hidden with *)
        label_master = tk.Label(parent, text="Master password:", font=('Arial', 10))
        label_master.pack(pady=(0, 5))

        self.master_password_entry = tk.Entry(parent, show="*", font=('Arial', 12), width=30)
        self.master_password_entry.pack(pady=(0, 10))

        # Checkbox to show/hide all passwords
        self.show_password_var = tk.BooleanVar()
        show_check = tk.Checkbutton(
            parent,
            text="Show passwords",
            #variable=self.show_password_var,
            command=self._toggle_password_visibility
        )
        show_check.pack(pady=(0, 10))

        # Bind Enter key to validation on the last field
        self.master_password_entry.bind('<Return>', lambda e: self._on_validate())

    def _toggle_password_visibility(self):
        """Show/hide passwords based on checkbox state"""
        #show_value = "" if self.show_password_var.get() else "*"

        # Récupérer la valeur actuelle de la BooleanVar
        current_value_before_toggle = self.show_password_var.get()
        # Inverser manuellement la valeur de la BooleanVar
        self.show_password_var.set(not current_value_before_toggle)

        # Obtenir la NOUVELLE valeur (après l'inversion manuelle)
        current_boolean_var_value = self.show_password_var.get()

        # La logique show_value doit maintenant être normale :
        # Si current_boolean_var_value est True (case cochée visuellement), afficher en clair ('')
        # Si current_boolean_var_value est False (case décochée visuellement), masquer ('*')
        show_value = "" if current_boolean_var_value else "*"

        if self.mode == "change":
            # Show/hide all password fields in change mode
            self.old_password_entry.config(show=show_value)
            self.new_password_entry.config(show=show_value)
            self.confirm_password_entry.config(show=show_value)
            self.master_password_entry.config(show=show_value)
        elif self.mode == "encrypt":
            # Show/hide all password fields in encrypt mode
            self.password_entry.config(show=show_value)
            self.password_confirm_entry.config(show=show_value)
            self.master_password_entry.config(show=show_value)
            self.master_password_confirm_entry.config(show=show_value)
        else:
            # Show/hide master password in decrypt mode
            self.master_password_entry.config(show=show_value)

    def _on_validate(self):
        if self.mode == "encrypt":
            self._handle_encrypt()
        elif self.mode == "decrypt":
            self._handle_decrypt()
        elif self.mode == "change":
            self._handle_change()

    def _handle_encrypt(self):
        """Handle the creation of password with username, domain, and master password"""
        # Get values from input fields
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        password_confirm = self.password_confirm_entry.get()
        domain = self.domain_entry.get().strip()
        master_password = self.master_password_entry.get()
        master_password_confirm = self.master_password_confirm_entry.get()

        # Validate username
        if not username:
            messagebox.showwarning("Warning", "Please enter a username")
            self.username_entry.focus()
            return

        # Validate password
        if not password:
            messagebox.showwarning("Warning", "Please enter a password")
            self.password_entry.focus()
            return

        if len(password) < 4:
            messagebox.showwarning("Warning", "Password must be at least 4 characters long")
            self.password_entry.focus()
            return

        # Validate password confirmation
        if not password_confirm:
            messagebox.showwarning("Warning", "Please confirm your password")
            self.password_confirm_entry.focus()
            return

        if password != password_confirm:
            messagebox.showerror("Error", "Passwords do not match")
            self.password_entry.delete(0, tk.END)
            self.password_confirm_entry.delete(0, tk.END)
            self.password_entry.focus()
            return

        # Validate domain
        if not domain:
            messagebox.showwarning("Warning", "Please enter a domain")
            self.domain_entry.focus()
            return

        # Validate master password
        if not master_password:
            messagebox.showwarning("Warning", "Please enter a master password")
            self.master_password_entry.focus()
            return

        if len(master_password) < 6:
            messagebox.showwarning("Warning", "Master password must be at least 6 characters long")
            self.master_password_entry.focus()
            return

        # Validate master password confirmation
        if not master_password_confirm:
            messagebox.showwarning("Warning", "Please confirm your master password")
            self.master_password_confirm_entry.focus()
            return

        if master_password != master_password_confirm:
            messagebox.showerror("Error", "Master passwords do not match")
            self.master_password_entry.delete(0, tk.END)
            self.master_password_confirm_entry.delete(0, tk.END)
            self.master_password_entry.focus()
            return

        # Encrypt password with master password and save all data to config.json
        encrypted = self.manager.encrypt_password(password, master_password)
        self.manager.save_to_config(encrypted, username=username, domain=domain)

        # messagebox.showinfo("Success", "Credentials encrypted and saved!")
        self.result = password

        # Clear sensitive data from memory before closing
        self._clear_sensitive_data()

        self.root.quit()
        self.root.destroy()

    def _handle_decrypt(self):
        """Handle password verification with master password"""
        master_password = self.master_password_entry.get()

        # Validate master password input
        if not master_password:
            messagebox.showwarning("Warning", "Please enter your master password")
            return

        # Load encrypted password from config.json
        encrypted = self.manager.load_from_config()

        if encrypted is None:
            messagebox.showerror("Error", "No password saved in config.json")
            return

        # Try to decrypt with the provided master password
        decrypted = self.manager.decrypt_password(encrypted, master_password)

        if decrypted is None:
            messagebox.showerror("Error", "Invalid master password!")
            self.master_password_entry.delete(0, tk.END)
            self.master_password_entry.focus()
        else:
            # messagebox.showinfo("Success", "Master password validated!")
            self.result = master_password

            # Clear decrypted password from memory immediately
            decrypted = None

            # Clear master password from entry field
            self.master_password_entry.delete(0, tk.END)

            self.root.quit()
            self.root.destroy()

    def _handle_change(self):
        """Handle password change with master password validation"""
        old_password = self.old_password_entry.get()
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        master_password = self.master_password_entry.get()

        # Validate all fields are filled
        if not old_password or not new_password or not confirm_password or not master_password:
            messagebox.showwarning("Warning", "Please fill all fields")
            return

        # Validate master password
        if not master_password:
            messagebox.showwarning("Warning", "Please enter your master password")
            self.master_password_entry.focus()
            return

        # Load encrypted password from config
        encrypted = self.manager.load_from_config()

        if encrypted is None:
            messagebox.showerror("Error", "No password saved in config.json")
            return

        # Decrypt old password with master password to validate
        decrypted_old = self.manager.decrypt_password(encrypted, master_password)

        if decrypted_old is None:
            messagebox.showerror("Error", "Invalid master password!")
            self.master_password_entry.delete(0, tk.END)
            self.master_password_entry.focus()
            return

        # Validate old password matches the decrypted one
        if decrypted_old != old_password:
            messagebox.showerror("Error", "Old password is incorrect")
            self.old_password_entry.delete(0, tk.END)
            self.old_password_entry.focus()
            # Clear decrypted password from memory
            decrypted_old = None
            return

        # Clear old decrypted password from memory
        decrypted_old = None

        # Validate new password confirmation
        if new_password != confirm_password:
            messagebox.showerror("Error", "New passwords do not match")
            self.new_password_entry.delete(0, tk.END)
            self.confirm_password_entry.delete(0, tk.END)
            self.new_password_entry.focus()
            return

        # Validate new password length
        if len(new_password) < 4:
            messagebox.showwarning("Warning", "New password must be at least 4 characters long")
            return

        # Validate new password is different from old
        if old_password == new_password:
            messagebox.showwarning("Warning", "New password must be different from old password")
            return

        # Encrypt new password with master password
        new_encrypted = self.manager.encrypt_password(new_password, master_password)
        self.manager.save_to_config(new_encrypted)

        # messagebox.showinfo("Success", "Password changed successfully!")
        self.result = True

        # Clear sensitive data from memory
        self._clear_sensitive_data()

        self.root.quit()
        self.root.destroy()

    def _clear_sensitive_data(self):
        """Clear all sensitive data from entry fields and memory"""
        if hasattr(self, 'password_entry'):
            self.password_entry.delete(0, tk.END)
        if hasattr(self, 'password_confirm_entry'):
            self.password_confirm_entry.delete(0, tk.END)
        if hasattr(self, 'master_password_entry'):
            self.master_password_entry.delete(0, tk.END)
        if hasattr(self, 'master_password_confirm_entry'):
            self.master_password_confirm_entry.delete(0, tk.END)
        if hasattr(self, 'old_password_entry'):
            self.old_password_entry.delete(0, tk.END)
        if hasattr(self, 'new_password_entry'):
            self.new_password_entry.delete(0, tk.END)
        if hasattr(self, 'confirm_password_entry'):
            self.confirm_password_entry.delete(0, tk.END)

    def _on_cancel(self):
        """Handle cancel button - clear sensitive data before closing"""
        self._clear_sensitive_data()
        self.result = False
        self.root.quit()
        self.root.destroy()

    def show(self):
        """Show the window and return the result"""
        self.root.mainloop()
        return self.result


# ============= USAGE EXAMPLES =============

def example_create_password():
    """Example: Create and encrypt a password"""
    dialog = PasswordDialog(mode="encrypt")
    result = dialog.show()

    if result:
        print(f"Password created: {result}")
    else:
        print("Cancelled")


def example_verify_password():
    """Example: Verify the password"""
    dialog = PasswordDialog(mode="decrypt")
    result = dialog.show()
    manager = PasswordManager()
    if result:
        print(f"Access granted! {result}")
        password = manager.get_decrypted_password(result)
        print(f"Password created: {password}")
        # Your code here...
    else:
        print("Access denied or cancelled")


def example_change_password():
    """Example: Change the password"""
    dialog = PasswordDialog(mode="change")
    result = dialog.show()

    if result:
        print("Password changed successfully!")
    else:
        print("Change cancelled")


def example_manual_encryption():
    """Example: Manually encrypt/decrypt"""
    manager = PasswordManager()

    # Encrypt
    my_password = "MySuperPassword123!"
    master_password = "MasterKey456!"
    encrypted = manager.encrypt_password(my_password, master_password)
    print(f"Encrypted: {encrypted}")

    # Save
    manager.save_to_config(encrypted)

    # Load and decrypt
    loaded = manager.load_from_config()
    decrypted = manager.decrypt_password(loaded, master_password)
    print(f"Decrypted: {decrypted}")


if __name__ == "__main__":
    # Uncomment the example you want to test

    # 1. Create a new password
    #example_create_password()

    # 2. Verify password
    example_verify_password()

    # 3. Change password
    #example_change_password()

    # 4. Manual encryption
    # example_manual_encryption()

"""
🔐 Security

The system uses:

    PBKDF2 with 100,000 iterations
    SHA-256 for hashing
    AES (via Fernet) for encryption
    Unique salt based on machine name and username
    Master password for additional security layer

The password is tied to the machine, so even if someone copies the config.json, 
they cannot decrypt it on another computer without the master password.

📝 Usage

To create a password:

dialog = PasswordDialog(mode="encrypt")
dialog.show()

To verify a password:

dialog = PasswordDialog(mode="decrypt")
if dialog.show():
    print("Authenticated!")

"change" mode:

    Asks for old password
    Asks for new password
    Asks for new password confirmation
    Asks for master password
    Validations:
        ✅ All fields filled
        ✅ Master password validates old password
        ✅ New passwords match
        ✅ New password different from old
        ✅ Minimum length (4 characters)

📝 Usage:

# Change password
dialog = PasswordDialog(mode="change")
if dialog.show():
    print("Password changed!")

Test with example_change_password()! 🚀

🔒 Master Password Security:
- All passwords are encrypted with a master password
- Master password is never stored, only used for encryption/decryption
- Master password is cleared from memory after use
- Minimum length: 6 characters for master password, 4 for regular password
"""