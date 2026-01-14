import sys
import json
import configparser
import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import socket
import ping3
import logging
import ipaddress
from datetime import datetime
from pathlib import Path
from wakeonlan import send_magic_packet

from psexec import PsExecManager
from credential import PasswordDialog
from process import ProcessManager

# Configuration des chemins
SCRIPT_DIR = Path(__file__).parent
CONFIG_JSON = SCRIPT_DIR / "config.json"
LOG_PATH = SCRIPT_DIR / "tmp"
MAIN_LOG = SCRIPT_DIR / "HelpIT.log"
BIN_PATH = SCRIPT_DIR / "bin"

# Création des dossiers nécessaires
LOG_PATH.mkdir(exist_ok=True)

# Configuration du logging
logging.basicConfig(
    filename=MAIN_LOG,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class NetworkDrive:
    """Gestion des lecteurs réseau"""

    def __init__(self):
        self.mounted_drives = {}

    def mount(self, remote_path, username, password):
        """Monte un lecteur réseau"""
        drive_letter = self._get_free_drive_letter()
        if not drive_letter:
            return None

        try:
            if sys.platform == 'win32':
                if username:
                    cmd = f'net use {drive_letter}: "{remote_path}" /user:{username} {password}'
                else:
                    cmd = f'net use {drive_letter}: "{remote_path}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    self.mounted_drives[drive_letter] = remote_path
                    return drive_letter
            """   
            else:
                # Pour Linux: utiliser mount.cifs
                mount_point = f"/mnt/{drive_letter}"
                os.makedirs(mount_point, exist_ok=True)
                cmd = f'sudo mount -t cifs "{remote_path}" {mount_point} -o username={username},password={password}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    self.mounted_drives[mount_point] = remote_path
                    return mount_point
            """
        except Exception as e:
            logging.error(f"Erreur montage lecteur: {e}")

        return None

    def unmount_all(self):
        """Démonte tous les lecteurs"""
        for drive in list(self.mounted_drives.keys()):
            try:
                if sys.platform == 'win32':
                    subprocess.run(f'net use {drive}: /delete /y', shell=True)
                else:
                    subprocess.run(f'sudo umount {drive}', shell=True)
                del self.mounted_drives[drive]
            except Exception as e:
                logging.error(f"Erreur démontage {drive}: {e}")

    def _get_free_drive_letter(self):
        """Trouve une lettre de lecteur disponible"""
        if sys.platform == 'win32':
            import string
            used_drives = [d.split(':')[0] for d in self.mounted_drives.keys()]
            for letter in string.ascii_uppercase[3:]:  # Commence à D:
                if letter not in used_drives:
                    return f"{letter}:"
        else:
            return f"drive_{len(self.mounted_drives)}"
        return None

    def count_free_drives(self):
        """Compte le nombre de lecteurs disponibles"""
        if sys.platform == 'win32':
            import string
            return 26 - 3 - len(self.mounted_drives)  # 26 lettres - A,B,C - utilisés
        return 10 - len(self.mounted_drives)

class HelpITGUI:
    """Interface graphique principale"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HelpIT")
        self.root.geometry("430x250")

        # Initialisation des composants
        self.config = configparser.ConfigParser()
        self.network_drives = NetworkDrive()

        # Variables
        self.admin_id = tk.StringVar()
        self.admin_pwd = ""
        self.admin_domain = ""
        self.current_target = ""
        self.current_ip = ""
        self.current_hostname = ""
        self.current_os_name = ""
        self.current_os_version = ""
        self.logged_user = ""
        self.fqdn = ""

        # Instance PsExecManager (sera initialisée lors de la validation de la cible)
        self.psexec = None
        self.psexec_path = str(BIN_PATH / "PsExec64.exe")

        # Chargement de la configuration
        self._load_config()

        # Création de l'interface
        self._create_widgets()

        # Log de démarrage
        logging.info(f"Démarrage de HelpIT par {self.admin_id}")

    def _load_config(self):
        """Charge la configuration"""
        if not CONFIG_JSON.exists():
            self.create_default_config(CONFIG_JSON)

        if CONFIG_JSON.exists():
            try:
                with open(str(CONFIG_JSON), "r") as file:
                    self.data = json.load(file)
            except Exception as e:
                logging.error(f"Erreur chargement configuration: {e}")
                messagebox.showerror("Erreur", "Erreur lors du chargement de la configuration")
                sys.exit(1)
        else:
            messagebox.showerror("Erreur",  "Config file missing.")
            sys.exit(1)

        self.admin_id = self.data["username"]
        self.admin_domain = self.data["domain"]

        if not Path(self.psexec_path).exists():
            messagebox.showerror("Erreur", "PsExec64 missing.")
            sys.exit(1)


    def create_default_config(self, file_path: Path) -> None:
        """
        Create a default configuration file if it does not exist.

        Args:
            file_path (Path): The path to the configuration file.
        """
        default_config = {
              "username": "",
              "password":"",
              "domain": ""
        }

        with open(file_path, "w") as file:
            json.dump(default_config, file, indent=4)

        dialog = PasswordDialog(mode="encrypt")
        result = dialog.show()

        if result:
            print(f"Mot de passe créé : {result}")
        else:
            print("Annulé")

    def _check_password(self):
        dialog = PasswordDialog(mode="change")
        result = dialog.show()

        if result:
            print("Mot de passe changé avec succès !")
        else:
            print("Changement annulé")

    def _create_widgets(self):
        """Crée les widgets de l'interface"""
        # Frame principale
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Zone de saisie
        ttk.Label(main_frame, text="Nom / IP", font=('Arial', 12, 'bold'),
                  foreground='#3B99FE').grid(row=0, column=1, pady=5)

        self.input_target = ttk.Entry(main_frame, width=20)
        self.input_target.grid(row=1, column=1, padx=5, sticky=(tk.W, tk.E))
        self.input_target.bind('<Return>', lambda e: self.validate_target())

        ttk.Button(main_frame, text="Valider", command=self.validate_target).grid(row=1, column=2, sticky=tk.W)

        # Barre de progression - commence à la colonne 1 comme l'input
        self.progressbar = ttk.Progressbar(main_frame, mode='determinate')
        self.progressbar.grid(row=2, column=1, columnspan=2, pady=5, padx=5, sticky=(tk.W, tk.E))

        # Labels d'information
        self.label_ping = ttk.Label(main_frame, text="", foreground='blue')
        self.label_ping.grid(row=3, column=1, padx=5)

        self.label_ip = ttk.Label(main_frame, text="Adresse IP/Nom: ")
        self.label_ip.grid(row=4, column=1, columnspan=3, sticky=tk.W)

        self.label_os = ttk.Label(main_frame, text="OS Version: ")
        self.label_os.grid(row=5, column=1, columnspan=3, sticky=tk.W)

        self.label_user = ttk.Label(main_frame, text="Session: ")
        self.label_user.grid(row=6, column=1, columnspan=3, sticky=tk.W)

        self.label_fqdn = ttk.Label(main_frame, text="Chemin AD: ")
        self.label_fqdn.grid(row=7, column=1, columnspan=3, sticky=tk.W)

        # Frame des boutons d'action
        action_frame = ttk.LabelFrame(main_frame, text="Actions", padding="5")
        action_frame.grid(row=1, column=0, rowspan=6, padx=5, sticky=(tk.N, tk.S))

        # Colonne 1 de boutons - commence à row=0 pour être aligné avec input_target (qui est en row=1)
        ttk.Button(action_frame, text="Processus", command=self.show_processes).grid(row=0, column=0, pady=2, padx=2,
                                                                                     sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="Gestion", command=self.open_computer_management).grid(row=1, column=0, pady=2,
                                                                                             padx=2, sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="Services", command=self.open_services).grid(row=2, column=0, pady=2, padx=2,
                                                                                   sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="WOL", command=self.wake_on_lan).grid(row=3, column=0, pady=2, padx=2,
                                                                            sticky=tk.W + tk.E)
        # Colonne 2 de boutons
        ttk.Button(action_frame, text="Assistance", command=self.remote_assistance).grid(row=0, column=1, pady=2,
                                                                                         padx=2, sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="Bureau", command=self.remote_desktop).grid(row=1, column=1, pady=2, padx=2,
                                                                                  sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="Lect C", command=lambda: self.open_drive('C')).grid(row=2, column=1, pady=2,
                                                                                           padx=2, sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="CMD", command=self.open_remote_cmd).grid(row=3, column=1, pady=2, padx=2,
                                                                            sticky=tk.W + tk.E)

        # Barre de statut
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=9, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)

        self.label_login = ttk.Label(status_frame, text=self.admin_id, font=('Arial', 8, 'bold'))
        self.label_login.pack(side=tk.LEFT, padx=5)

        self.label_drives = ttk.Label(status_frame, text=str(self.network_drives.count_free_drives()))
        self.label_drives.pack(side=tk.RIGHT, padx=5)

        ttk.Button(status_frame, text="⚙", width=3, command=self.change_password).pack(side=tk.LEFT, padx=2)
        ttk.Button(status_frame, text="Logs", width=5, command=self.open_logs).pack(side=tk.LEFT, padx=2)


    def validate_target(self):
        """Valide et récupère les informations de la cible"""
        target = self.input_target.get().strip()
        if not target:
            messagebox.showwarning("Attention", "Veuillez entrer une IP ou un nom d'hôte")
            return

        # Test si c'est une adresse IP et validation
        is_valid_ip = False

        # Vérifier si ça ressemble à une IP (contient des points et des chiffres)
        if '.' in target and any(c.isdigit() for c in target):
            try:
                ipaddress.ip_address(target)
                is_valid_ip = True
                logging.info(f"Adresse IP valide: {target}")
            except ValueError:
                messagebox.showerror("Erreur", f"L'adresse IP '{target}' n'est pas valide")
                logging.warning(f"Adresse IP invalide: {target}")
                return
        else:
            # Ce n'est pas une IP, c'est un nom d'hôte
            logging.info(f"Nom d'hôte détecté: {target}")

        self.current_target = target
        self.progressbar['value'] = 0

        # Test de ping
        try:
            ping_time = ping3.ping(target, timeout=2)
            if ping_time is None:
                self.label_ping.config(text="Pas de ping", foreground='red')
                logging.warning(f"Pas de réponse ping pour {target}")
                return

            ping_ms = int(ping_time * 1000)
            self.label_ping.config(text=f"Ping: {ping_ms}ms", foreground='blue')
            logging.info(f"Ping vers {target}: {ping_ms}ms")

        except Exception as e:
            self.label_ping.config(text="Erreur ping", foreground='red')
            logging.error(f"Erreur ping vers {target}: {e}")
            return

        self.progressbar['value'] = 10

        # Résolution du nom/IP
        try:
            if is_valid_ip:
                self.current_ip = target
                self.current_hostname = socket.gethostbyaddr(target)[0]
            else:
                self.current_hostname = target
                self.current_ip = socket.gethostbyname(target)

            self.label_ip.config(text=f"Nom: {self.current_hostname} | IP: {self.current_ip}")
        except Exception as e:
            logging.error(f"Erreur résolution {target}: {e}")
            self.label_ip.config(text=f"Adresse: {target}")

        self.progressbar['value'] = 30

        self.psexec = PsExecManager(self.current_ip,netbios=self.current_hostname ,psexec_path=self.psexec_path,tmp_dir=str(LOG_PATH))

        self.current_os_name = self.psexec.get_product_name()
        if not self.current_os_name: self.current_os_name = "?"

        self.current_os_version = self.psexec.get_display_version()
        if not self.current_os_version: self.current_os_version = "?"

        self.label_os.config(text=f"OS Version: {self.current_os_name} {self.current_os_version}")

        self.progressbar['value'] = 50

        self.logged_user = self.psexec.get_active_user()
        if not self.logged_user: self.logged_user = "?"
        self.label_user.config(text=f"Session: {self.logged_user}")


        self.progressbar['value'] = 60

        self.fqdn = self.psexec.get_distinguished_name()
        if not self.fqdn: self.fqdn = "?"
        self.label_fqdn.config(text=f"Chemin AD: {self.fqdn}")

        self.progressbar['value'] = 100

        # Log de la session
        log_file = LOG_PATH / f"{self.current_hostname}.log"
        with open(log_file, 'a') as f:
            f.write(f"\n{'=' * 50}\n")
            f.write(f"Session démarrée: {datetime.now()}\n")
            f.write(f"Nom: {self.current_hostname} | IP: {self.current_ip}\n")
            f.write(f"Utilisateur: {self.logged_user}\n")
            f.write(f"OS: {self.current_os_name} {self.current_os_version}\n")
            f.write(f"Ping: {ping_ms}ms\n")
            f.write(f"{'=' * 50}\n")

        logging.info(f"Session validée pour {self.current_hostname} ({self.current_ip})")

    def change_password(self):
        dialog = PasswordDialog(mode="change")
        result = dialog.show()

        if result:
            print("Mot de passe changé avec succès !")
        else:
            print("Changement annulé")

    def show_processes(self):
        """
        Display process manager window for the remote machine
        """
        # Check if a target is selected
        if not self.current_ip:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        try:
            if sys.platform == 'win32':
                # Get processes list using PsExec (requires SysInternals)
                self.psexec.get_processes_to_csv()
                csv_filename = Path(LOG_PATH / f"{self.current_hostname}_processus.csv")
                
                # Check if CSV file was created successfully
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
                    # Note: ProcessManager window will handle its own mainloop as a Toplevel window
                else:
                    messagebox.showerror("Erreur", "Impossible de générer la liste des processus")
                    logging.error(f"CSV file not created: {csv_filename}")

        except Exception as e:
            logging.error(f"Erreur ouverture gestionnaire de processus: {e}")
            messagebox.showerror("Erreur", "Impossible d'ouvrir le gestionnaire de processus")

    def open_computer_management(self):
        """Ouvre la console de gestion de l'ordinateur"""
        if not self.current_ip:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        try:
            if sys.platform == 'win32':
                subprocess.Popen(f'compmgmt.msc /computer={self.current_ip}')
            else:
                messagebox.showinfo("Information", "Fonctionnalité disponible uniquement sous Windows")
        except Exception as e:
            logging.error(f"Erreur ouverture gestion ordinateur: {e}")
            messagebox.showerror("Erreur", "Impossible d'ouvrir la gestion de l'ordinateur")

    def open_services(self):
        if not self.current_ip:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        try:
            if sys.platform == 'win32':
                # Utilisation de PsExec (nécessite SysInternals)
                self.psexec.get_services_to_csv()
                csv_filename = Path(LOG_PATH / f"{self.current_hostname}_services.csv")
                if csv_filename.exists():
                    pass

        except Exception as e:
            logging.error(f"Erreur ouverture CMD distante: {e}")
            messagebox.showerror("Erreur", "Impossible d'ouvrir l'invite de commande distante")

    def remote_assistance(self):
        """Lance l'assistance à distance"""
        if not self.current_ip:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        try:
            if sys.platform == 'win32':
                subprocess.Popen(f'msra.exe /offerra {self.current_ip}')
                logging.info(f"Assistance à distance lancée vers {self.current_ip}")
            else:
                messagebox.showinfo("Information", "Fonctionnalité disponible uniquement sous Windows")
        except Exception as e:
            logging.error(f"Erreur lancement assistance: {e}")
            messagebox.showerror("Erreur", "Impossible de lancer l'assistance à distance")

    def remote_desktop(self):
        """Lance le bureau à distance"""
        if not self.current_ip:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        try:
            if sys.platform == 'win32':
                subprocess.Popen(f'mstsc /v:{self.current_ip}')
                logging.info(f"Bureau à distance lancé vers {self.current_ip}")
            else:
                # Pour Linux, utiliser rdesktop ou xfreerdp
                subprocess.Popen(f'xfreerdp /v:{self.current_ip}')
        except Exception as e:
            logging.error(f"Erreur lancement bureau à distance: {e}")
            messagebox.showerror("Erreur", "Impossible de lancer le bureau à distance")

    def open_drive(self, drive_letter):
        """Ouvre un lecteur réseau"""
        if not self.current_ip:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        # use_creds = self._use_credentials(f'BoutonLect{drive_letter}')
        remote_path = f"\\\\{self.current_ip}\\{drive_letter.lower()}$"
        drive = self.network_drives.mount(remote_path)
        if drive:
            if sys.platform == 'win32':
                os.startfile(drive)
            else:
                subprocess.Popen(['xdg-open', drive])
            logging.info(f"Accès au lecteur {drive_letter}: sur {self.current_ip}")
        else:
            messagebox.showerror("Erreur", "Impossible de monter le lecteur")

        # Mise à jour du compteur
        self.label_drives.config(text=str(self.network_drives.count_free_drives()))
        """
        try:
            if use_creds:
                drive = self.network_drives.mount(
                    remote_path,
                    f"{self.admin_domain}\\{self.admin_id.get()}",
                    self.admin_pwd
                )
                if drive:
                    if sys.platform == 'win32':
                        os.startfile(drive)
                    else:
                        subprocess.Popen(['xdg-open', drive])
                    logging.info(f"Accès au lecteur {drive_letter}: sur {self.current_ip}")
                else:
                    messagebox.showerror("Erreur", "Impossible de monter le lecteur")
            else:
                if sys.platform == 'win32':
                    os.startfile(remote_path)
                else:
                    messagebox.showinfo("Information", "Fonctionnalité limitée sous Linux")

            # Mise à jour du compteur
            self.label_drives.config(text=str(self.network_drives.count_free_drives()))
        """
    def wake_on_lan(self):
        pass
        """
        Get-DhcpServerv4Lease -ComputerName "NomDuServeurDHCP" -ScopeId 192.168.1.0 | 
        Where-Object HostName -eq "NOMDUPOSTE" | 
        Select-Object IPAddress, ClientId

        # Envoie un paquet Wake-on-LAN"
        if not self.current_hostname:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return
        
        try:
            send_magic_packet(mac_address)
            messagebox.showinfo("Succès", f"Paquet WOL envoyé à {mac_address}")
            logging.info(f"WOL envoyé à {self.current_hostname} ({mac_address})")
        else:
            messagebox.showerror("Erreur", "Adresse MAC introuvable")

        except Exception as e:
            logging.error(f"Erreur WOL: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'envoi du WOL: {e}")
        """
    def open_remote_cmd(self):
        """Ouvre une invite de commande distante"""
        if not self.current_ip:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        try:
            if sys.platform == 'win32':
                # Utilisation de PsExec (nécessite SysInternals)
                self.psexec.open_terminal()
            # else:
                # Pour Linux, utiliser SSH
                # subprocess.Popen(f'xterm -e ssh {self.admin_id.get()}@{self.current_ip}')

        except Exception as e:
            logging.error(f"Erreur ouverture CMD distante: {e}")
            messagebox.showerror("Erreur", "Impossible d'ouvrir l'invite de commande distante")

    def open_logs(self):
        """Ouvre le dossier des logs"""
        try:
            if sys.platform == 'win32':
                os.startfile(LOG_PATH)
            else:
                subprocess.Popen(['xdg-open', LOG_PATH])
        except Exception as e:
            logging.error(f"Erreur ouverture logs: {e}")

    def run(self):
        """Lance l'application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        """Gestion de la fermeture"""
        self.network_drives.unmount_all()
        logging.info(f"Fermeture de HelpIT par {self.admin_id}")
        self.root.destroy()

def main():
    """Fonction principale"""
    app = HelpITGUI()
    app.run()


if __name__ == "__main__":
    main()