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
from credential import PasswordDialog, PasswordManager
from process import ProcessManager
from service import ServiceManager
from wolmanager import WolManager


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
            logging.error("Aucune lettre de lecteur disponible")
            return None
        else:
            command = f"NET USE {drive_letter} {remote_path} {password} /user:{username} /persistent:no"
            try:
                if username and password:
                    logging.info(f"Tentative de montage: {remote_path} sur {drive_letter}")
                    print(f"NET USE {drive_letter} {remote_path} ####### /user:{username} /persistent:no")
                    result = subprocess.run(command, capture_output=True, text=True, check=False, encoding='cp850')

                    if result.returncode == 0:
                        self.mounted_drives[drive_letter] = remote_path
                        logging.info(f"Lecteur monté avec succès: {drive_letter}")
                        return drive_letter
                    else:
                        logging.error(f"Erreur montage: {result.stderr}")
                        return None

            except Exception as e:
                logging.error(f"Erreur montage lecteur: {e}")

            return None



    def unmount_all(self):
        """Démonte tous les lecteurs"""
        if not self.mounted_drives:
            logging.info("Aucun lecteur réseau à démonter")
            return

        """Démonte tous les lecteurs"""
        for drive in list(self.mounted_drives.keys()):
            print(f'NET USE {drive}: /delete /y')
            try:
                subprocess.run(f'NET USE {drive} /delete /y', shell=True)
                del self.mounted_drives[drive]
            except Exception as e:
                logging.error(f"Erreur démontage {drive}: {e}")


    def _get_free_drive_letter(self):
        """Trouve une lettre de lecteur disponible"""
        if sys.platform == 'win32':
            import string
            used_drives = [d.split(':')[0] for d in self.mounted_drives.keys()]
            for letter in string.ascii_uppercase[4:]:  # Commence à E:
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


class ToolTip:
    """Crée un tooltip pour un widget"""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("Arial", 9, "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def update_text(self, new_text):
        """Met à jour le texte du tooltip"""
        self.text = new_text


class HelpITGUI:
    """Interface graphique principale"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HelpIT")
        self.root.geometry("440x255")

        # Initialisation des composants
        self.config = configparser.ConfigParser()
        self.network_drives = NetworkDrive()

        # Variables
        self.password = ""
        self.admin_id = tk.StringVar()
        self.admin_pwd = ""
        self.admin_domain = ""
        self.ping_threshold = ""
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

            dialog = PasswordDialog(mode="decrypt")
            self.password = dialog.show()
            if not self.password:
                print("Access denied or cancelled")
                sys.exit(1)

        else:
            messagebox.showerror("Erreur",  "Config file missing.")
            sys.exit(1)

        # self.admin_id est un tk.StringVar() et non un str donc set
        self.admin_id.set(self.data["username"])
        self.admin_domain = self.data["domain"]
        self.ping_threshold = self.data["ping_threshold"]

        if not Path(self.psexec_path).exists():
            messagebox.showerror("Erreur", "PsExec64 missing.")
            sys.exit(1)

    def get_mac_address(self, ip_address):
        """
        Retrieve the MAC address for a given IP address using ARP table.
        Works on Windows by executing 'arp -a' command.

        Args:
            ip_address: The IP address to look up

        Returns:
            str: The MAC address in format XX-XX-XX-XX-XX-XX, or None if not found
        """
        try:
            # Execute arp -a command to get ARP table
            result = subprocess.run(
                ['arp', '-a', ip_address],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Parse the output to find MAC address
                # Windows ARP output format: Internet Address      Physical Address      Type
                #                           192.168.1.100          6c-02-e0-00-8d-39     dynamic
                lines_output = result.stdout.splitlines()

                for line in lines_output:
                    if ip_address in line:
                        # Split the line and look for MAC address pattern
                        parts = line.split()
                        for part in parts:
                            # Check if this part matches MAC address pattern (xx-xx-xx-xx-xx-xx)
                            if '-' in part and len(part) == 17:
                                # Validate it's a proper MAC address
                                mac_parts = part.split('-')
                                if len(mac_parts) == 6 and all(len(p) == 2 for p in mac_parts):
                                    # Convert to uppercase for consistency
                                    mac_address = part.upper()
                                    logging.info(f"MAC address found for {ip_address}: {mac_address}")
                                    return mac_address

                logging.warning(f"MAC address not found in ARP table for {ip_address}")
                return None
            else:
                logging.error(f"Failed to execute arp command: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logging.error(f"Timeout while retrieving MAC address for {ip_address}")
            return None
        except Exception as e:
            logging.error(f"Error retrieving MAC address for {ip_address}: {e}")
            return None


    def create_default_config(self, file_path: Path) -> None:
        """
        Create a default configuration file if it does not exist.

        Args:
            file_path (Path): The path to the configuration file.
        """
        default_config = {
              "username": "",
              "password":"",
              "domain": "",
              "ping_threshold" : 75
        }

        with open(file_path, "w") as file:
            json.dump(default_config, file, indent=4)

        dialog = PasswordDialog(mode="encrypt")
        result = dialog.show()

        if result:
            print(f"Mot de passe créé l'application se ferme")
            sys.exit(1)
        else:
            print("Annulé")
            Path(file_path).unlink()
            sys.exit(1)

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
        self.progressbar = ttk.Progressbar(main_frame, mode='determinate', length=200)
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

        self.fqdn_tooltip = ToolTip(self.label_fqdn, "")

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

        self.label_login = ttk.Label(status_frame, textvariable=self.admin_id, font=('Arial', 8, 'bold'))
        self.label_login.pack(side=tk.LEFT, padx=5)

        self.label_drives = ttk.Label(status_frame, text=str(self.network_drives.count_free_drives()))
        self.label_drives.pack(side=tk.RIGHT, padx=5)

        ttk.Button(status_frame, text="⚙", width=3, command=self.change_password).pack(side=tk.LEFT, padx=2)
        ttk.Button(status_frame, text="Logs", width=5, command=self.open_logs).pack(side=tk.LEFT, padx=2)

    def _extract_first_ou(self, fqdn):
        """
        Extrait le premier OU d'un Distinguished Name

        Args:
            fqdn (str): Le Distinguished Name complet

        Returns:
            str: Le premier OU trouvé ou "?" si non trouvé
        """
        if not fqdn or fqdn == "?":
            return "?"

        try:
            # Recherche du premier OU= dans la chaîne
            import re
            match = re.search(r'OU=([^,]+)', fqdn)
            if match:
                return match.group(1)
            return "?"
        except Exception as e:
            logging.error(f"Erreur extraction OU: {e}")
            return "?"

    def _truncate_text(self, text, max_length=40):
        """
        Tronque un texte s'il est trop long

        Args:
            text (str): Le texte à tronquer
            max_length (int): Longueur maximale

        Returns:
            str: Le texte tronqué avec "..." si nécessaire
        """
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text


    def validate_target(self):
        """Valide et récupère les informations de la cible"""
        target = self.input_target.get().strip()
        if not target:
            messagebox.showwarning("Attention", "Veuillez entrer une IP ou un nom d'hôte")
            return

        # Seuil de ping en millisecondes (ajustable)
        PING_THRESHOLD = self.ping_threshold

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
            if ping_time is None or ping_time is False or ping_time <= 0:
                self.label_ping.config(text="Pas de ping", foreground='red')
                logging.warning(f"Pas de réponse ping pour {target}")
                return

            ping_ms = int(ping_time * 1000)

            # Déterminer la couleur en fonction du temps de réponse
            if ping_ms >= PING_THRESHOLD:
                color = 'orange'
                logging.warning(f"Ping lent vers {target}: {ping_ms}ms (seuil: {PING_THRESHOLD}ms)")
            else:
                color = 'green'
                logging.info(f"Ping vers {target}: {ping_ms}ms")

            self.label_ping.config(text=f"Ping: {ping_ms}ms", foreground=color)
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

        # Retrieve MAC address and store it in the database
        try:
            # Get MAC address from ARP table
            mac_address = self.get_mac_address(self.current_ip)

            if mac_address:
                # Initialize WolManager and store the MAC address
                wol_manager = WolManager("config.sqlite")
                row_id = wol_manager.update_mac_address(mac_address, self.current_hostname)
                logging.info(
                    f"MAC address stored in database: {mac_address} for {self.current_hostname} (ID: {row_id})")
            else:
                logging.warning(f"Could not retrieve MAC address for {self.current_ip}")
        except Exception as e:
            # Don't stop the validation process if MAC retrieval fails
            logging.error(f"Error storing MAC address in database: {e}")

        self.network_drives.unmount_all()

        self.psexec = PsExecManager(self.current_ip,netbios=self.current_hostname ,psexec_path=self.psexec_path,tmp_dir=LOG_PATH)

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
        if not self.fqdn:
            self.fqdn = "?"
            first_ou = "?"
        else:
            first_ou = self._extract_first_ou(self.fqdn)

        # Tronquer si trop long
        display_text = f"Chemin AD: {first_ou}"
        truncated_text = self._truncate_text(display_text, 40)

        self.label_fqdn.config(text=truncated_text)

        # Affichage du premier OU seulement
        # self.label_fqdn.config(text=f"Chemin AD: {first_ou}")

        # Mise à jour du tooltip avec le chemin complet
        self.fqdn_tooltip.update_text(self.fqdn)

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
        if not self.current_ip:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        try:
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
                    log_path=LOG_PATH
                )
                # Note: ProcessManager window will handle its own mainloop as a Toplevel window

        except Exception as e:
            logging.error(f"Erreur ouverture gestionnaire de processus: {e}")
            messagebox.showerror("Erreur", "Impossible d'ouvrir le gestionnaire de processus")

    def open_computer_management(self):
        """Ouvre la console de gestion de l'ordinateur"""
        if not self.current_ip:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        try:
            subprocess.Popen(f'compmgmt.msc /computer={self.current_ip}', shell=True)
        except Exception as e:
            logging.error(f"Erreur ouverture gestion ordinateur: {e}")
            messagebox.showerror("Erreur", "Impossible d'ouvrir la gestion de l'ordinateur")

    def open_services(self):
        if not self.current_ip:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        try:
            # Utilisation de PsExec (nécessite SysInternals)
            self.psexec.get_services_to_csv()
            csv_filename = Path(LOG_PATH / f"{self.current_hostname}_services.csv")
            # Check if CSV file was created successfully
            if csv_filename.exists():
                # Create and show the ServiceManager window
                service_manager = ServiceManager(
                    csv_filename=csv_filename,
                    psexec_manager=self.psexec,
                    current_ip=self.current_ip,
                    current_hostname=self.current_hostname,
                    psexec_path=self.psexec_path,
                    log_path=LOG_PATH
                )
                # Note: ServiceManager window will handle its own mainloop as a Toplevel window

        except Exception as e:
            logging.error(f"Erreur ouverture gestionnaire de services: {e}")
            messagebox.showerror("Erreur", "Impossible d'ouvrir le gestionnaire de services")

    def remote_assistance(self):
        """Lance l'assistance à distance"""
        if not self.current_ip:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return
        command_string = f'msra.exe /offerra {self.current_ip}'
        subprocess.run(command_string, shell=True, check=True, capture_output=True, text=True)
        """
        try:
            if sys.platform == 'win32':
                subprocess.run(['msra.exe', '/offerra',f'{self.current_ip}'])
                logging.info(f"Assistance à distance lancée vers {self.current_ip}")
            else:
                messagebox.showinfo("Information", "Fonctionnalité disponible uniquement sous Windows")
        except Exception as e:
            logging.error(f"Erreur lancement assistance: {e}")
            messagebox.showerror("Erreur", "Impossible de lancer l'assistance à distance")
        """
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

    """
    def _use_credentials(self, button_name):
        #Vérifie si les identifiants doivent être utilisés
        return self.config.getboolean('ElevationPrivilege', button_name, fallback=True)
    """

    def open_drive(self, drive_letter):
        """Ouvre un lecteur réseau"""
        if not self.current_ip:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        #use_creds = self._use_credentials(f'BoutonLect{drive_letter}')
        remote_path = f"\\\\{self.current_ip}\\{drive_letter.lower()}$"

        # Récupération du mot de passe
        manager = PasswordManager()
        try:
            self.admin_pwd = manager.get_decrypted_password(self.password)
        except Exception as e:
            logging.error(f"Erreur déchiffrement mot de passe: {e}")
            messagebox.showerror("Erreur", "Erreur lors du déchiffrement du mot de passe")
            return

        # Vérification des identifiants
        username = self.admin_id.get()  # ← Utiliser .get() pour StringVar
        if not username or not self.admin_pwd:
            messagebox.showerror("Erreur", "Identifiants administrateur manquants")
            return

        # Construction du nom d'utilisateur complet
        if self.admin_domain:
            full_username = f"{self.admin_domain}\\{username}"
        else:
            full_username = username

        logging.info(f"Tentative de connexion avec l'utilisateur: {full_username}")

        try:
            drive = self.network_drives.mount(
                remote_path,
                full_username,
                self.admin_pwd
            )
            if drive:
                os.startfile(drive)
                logging.info(f"Accès au lecteur {drive_letter}: sur {self.current_ip}")
                # Mise à jour du compteur
                self.label_drives.config(text=str(self.network_drives.count_free_drives()))
            else:
                messagebox.showerror("Erreur",
                                     f"Impossible de monter le lecteur {drive_letter}$\n"
                                     f"Vérifiez:\n"
                                     f"- Les identifiants\n"
                                     f"- Le partage administratif C$ est activé\n"
                                     f"- Le pare-feu autorise l'accès")

        except Exception as e:
            logging.error(f"Erreur ouverture lecteur {drive_letter}: {e}")
            messagebox.showerror("Erreur", f"Impossible d'accéder au lecteur {drive_letter}:\n{str(e)}")

    def wake_on_lan(self):
        """Send a Wake-on-LAN magic packet to all MAC addresses associated with the current hostname"""
        # Check if a target hostname has been validated
        if not self.current_hostname:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        try:
            # Initialize the WolManager to access the database
            wol_manager = WolManager("config.sqlite")

            # Retrieve all MAC addresses associated with the current hostname
            mac_addresses = wol_manager.read_mac_address(self.current_hostname)

            # Check if any MAC addresses were found
            if not mac_addresses:
                messagebox.showwarning("Attention",
                                       f"Aucune adresse MAC trouvée pour {self.current_hostname}")
                logging.warning(f"No MAC address found for {self.current_hostname}")
                return

            # Counter for successful packets sent
            success_count = 0
            failed_macs = []

            # Iterate through all MAC addresses and send magic packet to each
            for mac_address in mac_addresses:
                try:
                    # Send the Wake-on-LAN magic packet
                    send_magic_packet(mac_address)
                    success_count += 1
                    logging.info(f"WOL packet sent to {self.current_hostname} ({mac_address})")
                except Exception as e:
                    # Log individual failures but continue with other MAC addresses
                    failed_macs.append(mac_address)
                    logging.error(f"Failed to send WOL to {mac_address}: {e}")

            # Display result message to user
            if success_count > 0:
                if failed_macs:
                    # Partial success
                    messagebox.showinfo("Succès partiel",
                                        f"Paquets WOL envoyés avec succès: {success_count}/{len(mac_addresses)}\n"
                                        f"Adresses en échec: {', '.join(failed_macs)}")
                else:
                    # Complete success
                    messagebox.showinfo("Succès",
                                        f"Paquets WOL envoyés avec succès à {success_count} adresse(s) MAC\n"
                                        f"Cible: {self.current_hostname}")
            else:
                # All packets failed
                messagebox.showerror("Erreur",
                                     f"Échec de l'envoi de tous les paquets WOL à {self.current_hostname}")

        except Exception as e:
            # Handle any unexpected errors
            logging.error(f"Error in wake_on_lan: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'envoi du WOL: {e}")

    def open_remote_cmd(self):
        # Ouvre une invite de commande distante
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
        logging.info(f"Fermeture de HelpIT par {self.admin_id.get()}")
        self.root.destroy()

def main():
    """Fonction principale"""
    app = HelpITGUI()
    app.run()


if __name__ == "__main__":
    main()