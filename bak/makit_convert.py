import os
import sys
import subprocess
import configparser
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import socket
import ping3
import wmi
import logging
from datetime import datetime
from pathlib import Path
from cryptography.fernet import Fernet
import hashlib
import base64
import mysql.connector
from wakeonlan import send_magic_packet

# Configuration des chemins
SCRIPT_DIR = Path(__file__).parent
CONFIG_INI = SCRIPT_DIR / "config.ini"
LOG_PATH = SCRIPT_DIR / "tmp"
MAIN_LOG = SCRIPT_DIR / "MakeIT.log"
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


class CryptoManager:
    """Gestion du chiffrement/déchiffrement des mots de passe"""

    def __init__(self):
        self.key = self._get_machine_key()
        self.cipher = Fernet(self.key)

    def _get_machine_key(self):
        """Génère une clé basée sur l'identifiant machine"""
        # Équivalent du MachineGuid Windows
        if sys.platform == 'win32':
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                     r"SOFTWARE\Microsoft\Cryptography")
                guid, _ = winreg.QueryValueEx(key, "MachineGuid")
                winreg.CloseKey(key)
            except:
                guid = "default-machine-guid"
        else:
            # Pour Linux/Mac, utiliser l'UUID de la machine
            try:
                with open('/etc/machine-id', 'r') as f:
                    guid = f.read().strip()
            except:
                guid = "default-machine-guid"

        # Convertir en clé Fernet valide
        key_hash = hashlib.sha256(guid.encode()).digest()
        return base64.urlsafe_b64encode(key_hash)

    def encrypt(self, data):
        """Chiffre une chaîne"""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data):
        """Déchiffre une chaîne"""
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logging.error(f"Erreur déchiffrement: {e}")
            return None


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
                cmd = f'net use {drive_letter}: "{remote_path}" /user:{username} {password}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    self.mounted_drives[drive_letter] = remote_path
                    return drive_letter
            else:
                # Pour Linux: utiliser mount.cifs
                mount_point = f"/mnt/{drive_letter}"
                os.makedirs(mount_point, exist_ok=True)
                cmd = f'sudo mount -t cifs "{remote_path}" {mount_point} -o username={username},password={password}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    self.mounted_drives[mount_point] = remote_path
                    return mount_point
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


class RemoteSystemInfo:
    """Récupération d'informations système à distance"""

    def __init__(self, target, username=None, password=None, domain=None):
        self.target = target
        self.username = username
        self.password = password
        self.domain = domain
        self.wmi_conn = None

    def connect_wmi(self):
        """Connexion WMI à la machine distante (Windows uniquement)"""
        if sys.platform != 'win32':
            return False

        try:
            if self.username and self.password:
                user = f"{self.domain}\\{self.username}" if self.domain else self.username
                self.wmi_conn = wmi.WMI(computer=self.target, user=user, password=self.password)
            else:
                self.wmi_conn = wmi.WMI(computer=self.target)
            return True
        except Exception as e:
            logging.error(f"Erreur connexion WMI à {self.target}: {e}")
            return False

    def get_hostname(self):
        """Récupère le nom d'hôte"""
        try:
            return socket.gethostbyaddr(self.target)[0]
        except:
            return "Inconnu"

    def get_os_version(self):
        """Récupère la version de l'OS"""
        if not self.wmi_conn:
            if not self.connect_wmi():
                return "?"

        try:
            for os in self.wmi_conn.Win32_OperatingSystem():
                return os.Version
        except Exception as e:
            logging.error(f"Erreur récupération OS version: {e}")
            return "?"

    def get_logged_user(self):
        """Récupère l'utilisateur connecté"""
        if not self.wmi_conn:
            if not self.connect_wmi():
                return "Inconnu"

        try:
            for system in self.wmi_conn.Win32_ComputerSystem():
                return system.UserName if system.UserName else "Aucun"
        except Exception as e:
            logging.error(f"Erreur récupération utilisateur: {e}")
            return "Inconnu"

    def get_processes(self):
        """Récupère la liste des processus"""
        if not self.wmi_conn:
            if not self.connect_wmi():
                return []

        try:
            return [(p.Caption, p.ProcessId) for p in self.wmi_conn.Win32_Process()]
        except Exception as e:
            logging.error(f"Erreur récupération processus: {e}")
            return []

    def kill_process(self, process_name):
        """Tue un processus"""
        try:
            cmd = f'taskkill /s {self.target} /u {self.username} /p {self.password} /FI "IMAGENAME eq {process_name}" /F'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            logging.error(f"Erreur kill processus {process_name}: {e}")
            return False


class MakeITGUI:
    """Interface graphique principale"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MakeIT")
        self.root.geometry("460x270")

        # Initialisation des composants
        self.config = configparser.ConfigParser()
        self.crypto = CryptoManager()
        self.network_drives = NetworkDrive()

        # Variables
        self.admin_id = tk.StringVar()
        self.admin_pwd = ""
        self.admin_domain = ""
        self.current_target = ""
        self.current_ip = ""
        self.current_hostname = ""
        self.current_os_version = ""

        # Chargement de la configuration
        self._load_config()

        # Vérification du mot de passe
        if not self._check_password():
            sys.exit(0)

        # Création de l'interface
        self._create_widgets()

        # Log de démarrage
        logging.info(f"Démarrage de MakeIT par {self.admin_id.get()}")

    def _load_config(self):
        """Charge la configuration"""
        if not CONFIG_INI.exists():
            # self._first_run_setup()

            pass

        try:
            self.config.read(CONFIG_INI)

            self.admin_id.set(self.config.get('admin', 'login', fallback=''))
            encrypted_pwd = self.config.get('admin', 'motdepasse', fallback='')
            self.admin_pwd = self.crypto.decrypt(encrypted_pwd) or ''
            self.admin_domain = self.config.get('admin', 'domaine', fallback='')

            # Configuration MySQL
            self.mysql_server = self.config.get('admin', 'SQLserveur', fallback='')
            self.mysql_user = self.config.get('admin', 'SQLlogin', fallback='')
            encrypted_sql_pwd = self.config.get('admin', 'SQLmotdepasse', fallback='')
            self.mysql_pwd = self.crypto.decrypt(encrypted_sql_pwd) or ''
            self.mysql_db = self.config.get('admin', 'SQLbase', fallback='')

        except Exception as e:
            logging.error(f"Erreur chargement configuration: {e}")
            messagebox.showerror("Erreur", "Erreur lors du chargement de la configuration")
            sys.exit(1)

    def _first_run_setup(self):
        """Configuration initiale au premier lancement"""
        dialog = FirstRunDialog(self.root, self.crypto)
        if not dialog.result:
            sys.exit(0)

        # Création du fichier de configuration
        self.config['admin'] = dialog.result
        with open(CONFIG_INI, 'w') as f:
            self.config.write(f)

    def _check_password(self):
        """Vérifie le mot de passe administrateur"""
        max_attempts = 3
        attempts = 0

        while attempts < max_attempts:
            password = simpledialog.askstring(
                "Sécurité",
                f"Vérification du compte :\n{self.admin_id.get()}\nEntrez votre mot de passe.",
                show='*'
            )

            if password is None:  # Annulé
                return False

            if password == self.admin_pwd:
                return True

            attempts += 1
            messagebox.showerror("Erreur", f"Mauvais mot de passe. {max_attempts - attempts} tentatives restantes.")

        return False

    def _create_widgets(self):
        """Crée les widgets de l'interface"""
        # Frame principale
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Zone de saisie
        ttk.Label(main_frame, text="Nom/IP", font=('Arial', 12, 'bold'),
                  foreground='#3B99FE').grid(row=0, column=1, pady=5)

        self.input_target = ttk.Entry(main_frame, width=20)
        self.input_target.grid(row=1, column=1, padx=5)
        self.input_target.bind('<Return>', lambda e: self.validate_target())

        ttk.Button(main_frame, text="Valider", command=self.validate_target).grid(row=1, column=2)
        ttk.Button(main_frame, text="?", width=3, command=self.show_help).grid(row=1, column=3)

        # Barre de progression
        self.progressbar = ttk.Progressbar(main_frame, length=150, mode='determinate')
        self.progressbar.grid(row=2, column=1, columnspan=2, pady=5)

        # Labels d'information
        self.label_ip = ttk.Label(main_frame, text="Adresse IP/Nom: ")
        self.label_ip.grid(row=3, column=1, columnspan=3, sticky=tk.W)

        self.label_os = ttk.Label(main_frame, text="OS Version: ")
        self.label_os.grid(row=4, column=1, columnspan=3, sticky=tk.W)

        self.label_user = ttk.Label(main_frame, text="Session: ")
        self.label_user.grid(row=5, column=1, columnspan=3, sticky=tk.W)

        self.label_fqdn = ttk.Label(main_frame, text="Chemin AD: ")
        self.label_fqdn.grid(row=6, column=1, columnspan=3, sticky=tk.W)

        self.label_ping = ttk.Label(main_frame, text="", foreground='blue')
        self.label_ping.grid(row=2, column=3, padx=5)

        # Frame des boutons d'action
        action_frame = ttk.LabelFrame(main_frame, text="Actions", padding="5")
        action_frame.grid(row=3, column=0, rowspan=6, padx=5, sticky=(tk.N, tk.S))

        # Colonne 1 de boutons
        ttk.Button(action_frame, text="Processus", command=self.show_processes).grid(row=0, column=0, pady=2, padx=2,
                                                                                     sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="Informations", command=self.show_info).grid(row=1, column=0, pady=2, padx=2,
                                                                                   sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="Netstat", command=self.show_netstat).grid(row=2, column=0, pady=2, padx=2,
                                                                                 sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="Gestion", command=self.open_computer_management).grid(row=3, column=0, pady=2,
                                                                                             padx=2, sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="Services", command=self.open_services).grid(row=4, column=0, pady=2, padx=2,
                                                                                   sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="Inventaire", command=self.show_inventory).grid(row=5, column=0, pady=2, padx=2,
                                                                                      sticky=tk.W + tk.E)

        # Colonne 2 de boutons
        ttk.Button(action_frame, text="Assistance", command=self.remote_assistance).grid(row=0, column=1, pady=2,
                                                                                         padx=2, sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="Bureau", command=self.remote_desktop).grid(row=1, column=1, pady=2, padx=2,
                                                                                  sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="Lect C", command=lambda: self.open_drive('C')).grid(row=2, column=1, pady=2,
                                                                                           padx=2, sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="Lect D", command=lambda: self.open_drive('D')).grid(row=3, column=1, pady=2,
                                                                                           padx=2, sticky=tk.W + tk.E)
        ttk.Button(action_frame, text="WOL", command=self.wake_on_lan).grid(row=4, column=1, pady=2, padx=2,
                                                                            sticky=tk.W + tk.E)

        # Barre de statut
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=9, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)

        self.label_login = ttk.Label(status_frame, text=self.admin_id.get(), font=('Arial', 8, 'bold'))
        self.label_login.pack(side=tk.LEFT, padx=5)

        self.label_drives = ttk.Label(status_frame, text=str(self.network_drives.count_free_drives()))
        self.label_drives.pack(side=tk.RIGHT, padx=5)

        ttk.Button(status_frame, text="CMD", width=5, command=self.open_remote_cmd).pack(side=tk.LEFT, padx=2)
        ttk.Button(status_frame, text="Logs", width=5, command=self.open_logs).pack(side=tk.LEFT, padx=2)
        ttk.Button(status_frame, text="⚙", width=3, command=self.change_password).pack(side=tk.RIGHT, padx=2)

    def validate_target(self):
        """Valide et récupère les informations de la cible"""
        target = self.input_target.get().strip()
        if not target:
            messagebox.showwarning("Attention", "Veuillez entrer une IP ou un nom d'hôte")
            return

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
            if self._is_ip(target):
                self.current_ip = target
                self.current_hostname = socket.gethostbyaddr(target)[0]
            else:
                self.current_hostname = target
                self.current_ip = socket.gethostbyname(target)

            self.label_ip.config(text=f"Nom: {self.current_hostname} | IP: {self.current_ip}")
        except Exception as e:
            logging.error(f"Erreur résolution {target}: {e}")
            self.label_ip.config(text=f"Adresse: {target}")

        self.progressbar['value'] = 35

        # Récupération des informations système
        use_creds = self._use_credentials('BoutonValider')
        if use_creds:
            remote_info = RemoteSystemInfo(
                self.current_ip,
                self.admin_id.get(),
                self.admin_pwd,
                self.admin_domain
            )
        else:
            remote_info = RemoteSystemInfo(self.current_ip)

        # Version OS
        os_version = remote_info.get_os_version()
        self.current_os_version = os_version
        self.label_os.config(text=f"OS Version: {os_version}")

        self.progressbar['value'] = 60

        # Utilisateur connecté
        logged_user = remote_info.get_logged_user()
        self.label_user.config(text=f"Session: {logged_user}")

        self.progressbar['value'] = 80

        # FQDN Active Directory
        fqdn = self._get_ad_path()
        self.label_fqdn.config(text=f"Chemin AD: {fqdn}")

        self.progressbar['value'] = 100

        # Log de la session
        log_file = LOG_PATH / f"{self.current_hostname}.log"
        with open(log_file, 'a') as f:
            f.write(f"\n{'=' * 50}\n")
            f.write(f"Session démarrée: {datetime.now()}\n")
            f.write(f"Nom: {self.current_hostname} | IP: {self.current_ip}\n")
            f.write(f"Utilisateur: {logged_user}\n")
            f.write(f"OS: {os_version}\n")
            f.write(f"Ping: {ping_ms}ms\n")
            f.write(f"{'=' * 50}\n")

        logging.info(f"Session validée pour {self.current_hostname} ({self.current_ip})")

    def show_processes(self):
        """Affiche la liste des processus"""
        if not self.current_ip:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        use_creds = self._use_credentials('BoutonProcessus')
        if use_creds:
            remote_info = RemoteSystemInfo(
                self.current_ip,
                self.admin_id.get(),
                self.admin_pwd,
                self.admin_domain
            )
        else:
            remote_info = RemoteSystemInfo(self.current_ip)

        processes = remote_info.get_processes()

        if not processes:
            messagebox.showerror("Erreur", "Impossible de récupérer la liste des processus")
            return

        # Création d'une fenêtre pour afficher les processus
        ProcessWindow(self.root, processes, remote_info)

    def show_info(self):
        """Affiche les informations système"""
        if not self.current_ip:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        use_creds = self._use_credentials('BoutonInformations')
        if use_creds:
            remote_info = RemoteSystemInfo(
                self.current_ip,
                self.admin_id.get(),
                self.admin_pwd,
                self.admin_domain
            )
        else:
            remote_info = RemoteSystemInfo(self.current_ip)

        InfoWindow(self.root, remote_info)

    def show_netstat(self):
        """Affiche les ports ouverts"""
        if not self.current_ip:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        use_creds = self._use_credentials('BoutonNetstat')

        NetstatWindow(self.root, self.current_ip, self.admin_id.get(),
                      self.admin_pwd, self.admin_domain, use_creds)

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
        """Ouvre la console des services"""
        if not self.current_ip:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        try:
            if sys.platform == 'win32':
                subprocess.Popen(f'services.msc /computer={self.current_ip}')
            else:
                messagebox.showinfo("Information", "Fonctionnalité disponible uniquement sous Windows")
        except Exception as e:
            logging.error(f"Erreur ouverture services: {e}")
            messagebox.showerror("Erreur", "Impossible d'ouvrir les services")

    def show_inventory(self):
        """Affiche les informations d'inventaire depuis GLPI"""
        if not self.current_hostname:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        if not self.mysql_server:
            messagebox.showerror("Erreur", "Nécessite une base GLPI configurée")
            return

        try:
            conn = mysql.connector.connect(
                host=self.mysql_server,
                user=self.mysql_user,
                password=self.mysql_pwd,
                database=self.mysql_db
            )

            cursor = conn.cursor()
            # Exemple de requête GLPI (à adapter selon votre schéma)
            query = "SELECT * FROM glpi_computers WHERE name = %s"
            cursor.execute(query, (self.current_hostname,))

            results = cursor.fetchall()
            if results:
                InventoryWindow(self.root, results)
            else:
                messagebox.showinfo("Information", "Aucune information d'inventaire trouvée")

            cursor.close()
            conn.close()

        except Exception as e:
            logging.error(f"Erreur requête GLPI: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de la requête: {e}")

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

        use_creds = self._use_credentials(f'BoutonLect{drive_letter}')
        remote_path = f"\\\\{self.current_ip}\\{drive_letter.lower()}$"

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

        except Exception as e:
            logging.error(f"Erreur ouverture lecteur {drive_letter}: {e}")
            messagebox.showerror("Erreur", f"Impossible d'accéder au lecteur {drive_letter}")

    def wake_on_lan(self):
        """Envoie un paquet Wake-on-LAN"""
        if not self.current_hostname:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        if not self.mysql_server:
            messagebox.showerror("Erreur", "Nécessite une base GLPI configurée")
            return

        try:
            # Récupération de l'adresse MAC depuis GLPI
            conn = mysql.connector.connect(
                host=self.mysql_server,
                user=self.mysql_user,
                password=self.mysql_pwd,
                database=self.mysql_db
            )

            cursor = conn.cursor()
            # Requête pour récupérer la MAC (à adapter)
            query = "SELECT mac FROM glpi_networkports WHERE itemtype='Computer' AND items_id IN (SELECT id FROM glpi_computers WHERE name=%s)"
            cursor.execute(query, (self.current_hostname,))

            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result and result[0]:
                mac_address = result[0]
                send_magic_packet(mac_address)
                messagebox.showinfo("Succès", f"Paquet WOL envoyé à {mac_address}")
                logging.info(f"WOL envoyé à {self.current_hostname} ({mac_address})")
            else:
                messagebox.showerror("Erreur", "Adresse MAC introuvable")

        except Exception as e:
            logging.error(f"Erreur WOL: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'envoi du WOL: {e}")

    def open_remote_cmd(self):
        """Ouvre une invite de commande distante"""
        if not self.current_ip:
            messagebox.showwarning("Attention", "Veuillez d'abord valider une cible")
            return

        try:
            if sys.platform == 'win32':
                # Utilisation de PsExec (nécessite SysInternals)
                psexec_path = BIN_PATH / "PsExec.exe"
                if psexec_path.exists():
                    subprocess.Popen(
                        f'"{psexec_path}" -accepteula \\\\{self.current_ip} '
                        f'-u {self.admin_id.get()} -p {self.admin_pwd} cmd.exe'
                    )
                else:
                    messagebox.showerror("Erreur", "PsExec.exe introuvable dans le dossier bin")
            else:
                # Pour Linux, utiliser SSH
                subprocess.Popen(f'xterm -e ssh {self.admin_id.get()}@{self.current_ip}')

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

    def show_help(self):
        """Affiche l'aide pour rechercher par numéro d'inventaire"""
        inventory_num = simpledialog.askstring("Aide", "Entrez le numéro d'inventaire:")

        if not inventory_num:
            return

        if not self.mysql_server:
            messagebox.showerror("Erreur", "Nécessite une base GLPI configurée")
            return

        try:
            conn = mysql.connector.connect(
                host=self.mysql_server,
                user=self.mysql_user,
                password=self.mysql_pwd,
                database=self.mysql_db
            )

            cursor = conn.cursor()
            query = "SELECT name FROM glpi_computers WHERE otherserial = %s"
            cursor.execute(query, (inventory_num,))

            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                self.input_target.delete(0, tk.END)
                self.input_target.insert(0, result[0])
                messagebox.showinfo("Résultat", f"Nom trouvé: {result[0]}")
            else:
                messagebox.showinfo("Résultat", "Aucun ordinateur trouvé avec ce numéro")

        except Exception as e:
            logging.error(f"Erreur recherche inventaire: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de la recherche: {e}")

    def change_password(self):
        """Change le mot de passe"""
        PasswordDialog(self.root, self.config, self.crypto, CONFIG_INI)

    def _use_credentials(self, button_name):
        """Vérifie si les identifiants doivent être utilisés"""
        return self.config.getboolean('ElevationPrivilege', button_name, fallback=True)

    def _is_ip(self, address):
        """Vérifie si l'adresse est une IP"""
        try:
            socket.inet_aton(address)
            return True
        except:
            return False

    def _get_ad_path(self):
        """Récupère le chemin AD"""
        # Implémentation simplifiée
        # Dans l'original, cela utilise LDAP/AD
        return "Non implémenté"

    def run(self):
        """Lance l'application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        """Gestion de la fermeture"""
        self.network_drives.unmount_all()
        logging.info(f"Fermeture de MakeIT par {self.admin_id.get()}")
        self.root.destroy()


class ProcessWindow:
    """Fenêtre d'affichage des processus"""

    def __init__(self, parent, processes, remote_info):
        self.window = tk.Toplevel(parent)
        self.window.title("Processus distants")
        self.window.geometry("600x400")

        self.processes = processes
        self.remote_info = remote_info

        # Liste des processus
        frame = ttk.Frame(self.window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Listbox
        self.listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        # Remplissage
        for name, pid in sorted(processes):
            self.listbox.insert(tk.END, f"{name} (PID: {pid})")

        # Bouton kill
        ttk.Button(self.window, text="Arrêter le processus sélectionné",
                   command=self.kill_selected).pack(pady=5)

    def kill_selected(self):
        """Arrête le processus sélectionné"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un processus")
            return

        process_text = self.listbox.get(selection[0])
        process_name = process_text.split(' (PID:')[0]

        if messagebox.askyesno("Confirmation", f"Voulez-vous vraiment arrêter {process_name} ?"):
            if self.remote_info.kill_process(process_name):
                messagebox.showinfo("Succès", "Processus arrêté")
                self.listbox.delete(selection[0])
            else:
                messagebox.showerror("Erreur", "Impossible d'arrêter le processus")


class InfoWindow:
    """Fenêtre d'informations système"""

    def __init__(self, parent, remote_info):
        self.window = tk.Toplevel(parent)
        self.window.title("Informations système")
        self.window.geometry("700x500")

        self.remote_info = remote_info

        # Zone de texte
        frame = ttk.Frame(self.window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text = tk.Text(frame, yscrollcommand=scrollbar.set, wrap=tk.WORD)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text.yview)

        # Menu de sélection
        ttk.Label(self.window, text="Catégorie:").pack()

        self.combo = ttk.Combobox(self.window, values=[
            "Système d'exploitation",
            "Processeur",
            "Mémoire",
            "Disques",
            "Réseau",
            "Logiciels installés"
        ], state='readonly')
        self.combo.pack(pady=5)
        self.combo.bind('<<ComboboxSelected>>', self.load_info)

        ttk.Button(self.window, text="Rafraîchir", command=self.load_info).pack(pady=5)

    def load_info(self, event=None):
        """Charge les informations selon la catégorie"""
        category = self.combo.get()
        self.text.delete('1.0', tk.END)

        if not self.remote_info.connect_wmi():
            self.text.insert('1.0', "Erreur de connexion WMI")
            return

        try:
            if category == "Système d'exploitation":
                for os in self.remote_info.wmi_conn.Win32_OperatingSystem():
                    info = f"""
Nom: {os.Caption}
Version: {os.Version}
Architecture: {os.OSArchitecture}
Fabricant: {os.Manufacturer}
Date d'installation: {os.InstallDate}
Répertoire système: {os.SystemDirectory}
Numéro de série: {os.SerialNumber}
                    """
                    self.text.insert('1.0', info)

            elif category == "Processeur":
                for cpu in self.remote_info.wmi_conn.Win32_Processor():
                    info = f"""
Nom: {cpu.Name}
Fabricant: {cpu.Manufacturer}
Nombre de coeurs: {cpu.NumberOfCores}
Nombre de threads: {cpu.NumberOfLogicalProcessors}
Vitesse max: {cpu.MaxClockSpeed} MHz
                    """
                    self.text.insert('1.0', info)

            elif category == "Mémoire":
                total_memory = 0
                for mem in self.remote_info.wmi_conn.Win32_PhysicalMemory():
                    capacity_gb = int(mem.Capacity) / (1024 ** 3)
                    total_memory += capacity_gb
                    info = f"""
Capacité: {capacity_gb:.2f} GB
Vitesse: {mem.Speed} MHz
Fabricant: {mem.Manufacturer}
---
                    """
                    self.text.insert(tk.END, info)

                self.text.insert('1.0', f"Mémoire totale: {total_memory:.2f} GB\n\n")

            elif category == "Disques":
                for disk in self.remote_info.wmi_conn.Win32_LogicalDisk():
                    if disk.Size:
                        size_gb = int(disk.Size) / (1024 ** 3)
                        free_gb = int(disk.FreeSpace) / (1024 ** 3)
                        used_gb = size_gb - free_gb
                        percent = (used_gb / size_gb) * 100

                        info = f"""
Lecteur: {disk.DeviceID}
Type: {disk.Description}
Taille: {size_gb:.2f} GB
Utilisé: {used_gb:.2f} GB ({percent:.1f}%)
Libre: {free_gb:.2f} GB
---
                        """
                        self.text.insert(tk.END, info)

            elif category == "Réseau":
                for adapter in self.remote_info.wmi_conn.Win32_NetworkAdapterConfiguration(IPEnabled=True):
                    info = f"""
Carte: {adapter.Description}
Adresse MAC: {adapter.MACAddress}
Adresses IP: {', '.join(adapter.IPAddress) if adapter.IPAddress else 'Aucune'}
Passerelle: {', '.join(adapter.DefaultIPGateway) if adapter.DefaultIPGateway else 'Aucune'}
DHCP activé: {'Oui' if adapter.DHCPEnabled else 'Non'}
---
                    """
                    self.text.insert(tk.END, info)

            elif category == "Logiciels installés":
                for software in self.remote_info.wmi_conn.Win32_Product():
                    info = f"{software.Name} - {software.Version}\n"
                    self.text.insert(tk.END, info)

        except Exception as e:
            self.text.insert('1.0', f"Erreur lors de la récupération: {e}")


class NetstatWindow:
    """Fenêtre d'affichage netstat"""

    def __init__(self, parent, target_ip, username, password, domain, use_creds):
        self.window = tk.Toplevel(parent)
        self.window.title("Ports réseau")
        self.window.geometry("800x600")

        self.target_ip = target_ip
        self.username = username
        self.password = password
        self.domain = domain
        self.use_creds = use_creds

        # Options
        option_frame = ttk.Frame(self.window, padding="10")
        option_frame.pack(fill=tk.X)

        self.option_var = tk.StringVar(value="all")

        ttk.Radiobutton(option_frame, text="Toutes les connexions",
                        variable=self.option_var, value="all").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(option_frame, text="Connexions établies",
                        variable=self.option_var, value="established").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(option_frame, text="Ports en écoute",
                        variable=self.option_var, value="listening").pack(side=tk.LEFT, padx=5)

        ttk.Button(option_frame, text="Rafraîchir", command=self.load_netstat).pack(side=tk.RIGHT, padx=5)

        # Zone de texte
        text_frame = ttk.Frame(self.window, padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text = tk.Text(text_frame, yscrollcommand=scrollbar.set, font=('Courier', 9))
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text.yview)

        # Chargement initial
        self.load_netstat()

    def load_netstat(self):
        """Charge les informations netstat"""
        self.text.delete('1.0', tk.END)

        option = self.option_var.get()

        try:
            if self.use_creds:
                cmd = f'psexec \\\\{self.target_ip} -u {self.username} -p {self.password} netstat -ano'
            else:
                cmd = f'netstat -ano'  # Local

            # Ajout des options
            if option == "established":
                cmd += ' | findstr ESTABLISHED'
            elif option == "listening":
                cmd += ' | findstr LISTENING'

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                self.text.insert('1.0', result.stdout)
            else:
                self.text.insert('1.0', f"Erreur: {result.stderr}")

        except Exception as e:
            self.text.insert('1.0', f"Erreur lors de l'exécution: {e}")


class InventoryWindow:
    """Fenêtre d'affichage de l'inventaire"""

    def __init__(self, parent, data):
        self.window = tk.Toplevel(parent)
        self.window.title("Inventaire")
        self.window.geometry("800x600")

        # Treeview pour afficher les données
        frame = ttk.Frame(self.window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical")
        hsb = ttk.Scrollbar(frame, orient="horizontal")

        # Treeview
        self.tree = ttk.Treeview(frame, yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Configuration des colonnes (à adapter selon vos données)
        if data:
            columns = [f"Col{i}" for i in range(len(data[0]))]
            self.tree['columns'] = columns

            for col in columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, width=100)

            # Insertion des données
            for row in data:
                self.tree.insert('', tk.END, values=row)


class FirstRunDialog:
    """Dialogue de première configuration"""

    def __init__(self, parent, crypto):
        self.result = None
        self.crypto = crypto

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Configuration initiale")
        self.dialog.geometry("400x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Configuration de MakeIT",
                  font=('Arial', 14, 'bold')).pack(pady=10)

        # Identifiant
        ttk.Label(frame, text="Identifiant administrateur:").pack(anchor=tk.W, pady=5)
        self.entry_login = ttk.Entry(frame, width=40)
        self.entry_login.pack(pady=5)

        # Mot de passe
        ttk.Label(frame, text="Mot de passe:").pack(anchor=tk.W, pady=5)
        self.entry_pwd = ttk.Entry(frame, width=40, show='*')
        self.entry_pwd.pack(pady=5)

        # Confirmation mot de passe
        ttk.Label(frame, text="Confirmer le mot de passe:").pack(anchor=tk.W, pady=5)
        self.entry_pwd_confirm = ttk.Entry(frame, width=40, show='*')
        self.entry_pwd_confirm.pack(pady=5)

        # Domaine
        ttk.Label(frame, text="Domaine:").pack(anchor=tk.W, pady=5)
        self.entry_domain = ttk.Entry(frame, width=40)
        self.entry_domain.pack(pady=5)

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        ttk.Label(frame, text="Configuration MySQL (optionnel)",
                  font=('Arial', 10, 'bold')).pack(pady=5)

        # MySQL Serveur
        ttk.Label(frame, text="Serveur MySQL:").pack(anchor=tk.W, pady=5)
        self.entry_sql_server = ttk.Entry(frame, width=40)
        self.entry_sql_server.pack(pady=5)

        # MySQL Login
        ttk.Label(frame, text="Login MySQL:").pack(anchor=tk.W, pady=5)
        self.entry_sql_login = ttk.Entry(frame, width=40)
        self.entry_sql_login.pack(pady=5)

        # MySQL Password
        ttk.Label(frame, text="Mot de passe MySQL:").pack(anchor=tk.W, pady=5)
        self.entry_sql_pwd = ttk.Entry(frame, width=40, show='*')
        self.entry_sql_pwd.pack(pady=5)

        # MySQL Base
        ttk.Label(frame, text="Base de données:").pack(anchor=tk.W, pady=5)
        self.entry_sql_db = ttk.Entry(frame, width=40)
        self.entry_sql_db.pack(pady=5)

        # Boutons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="Valider", command=self.validate).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Annuler", command=self.cancel).pack(side=tk.LEFT, padx=5)

        self.dialog.wait_window()

    def validate(self):
        """Valide la configuration"""
        login = self.entry_login.get().strip()
        pwd = self.entry_pwd.get()
        pwd_confirm = self.entry_pwd_confirm.get()
        domain = self.entry_domain.get().strip()

        if not login or not pwd:
            messagebox.showerror("Erreur", "L'identifiant et le mot de passe sont obligatoires")
            return

        if pwd != pwd_confirm:
            messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas")
            return

        # Chiffrement du mot de passe
        encrypted_pwd = self.crypto.encrypt(pwd)

        # Récupération des paramètres MySQL
        sql_server = self.entry_sql_server.get().strip()
        sql_login = self.entry_sql_login.get().strip()
        sql_pwd = self.entry_sql_pwd.get()
        sql_db = self.entry_sql_db.get().strip()

        encrypted_sql_pwd = self.crypto.encrypt(sql_pwd) if sql_pwd else ""

        self.result = {
            'login': login,
            'motdepasse': encrypted_pwd,
            'domaine': domain,
            'SQLserveur': sql_server,
            'SQLlogin': sql_login,
            'SQLmotdepasse': encrypted_sql_pwd,
            'SQLbase': sql_db
        }

        self.dialog.destroy()

    def cancel(self):
        """Annule la configuration"""
        self.dialog.destroy()


class PasswordDialog:
    """Dialogue de changement de mot de passe"""

    def __init__(self, parent, config, crypto, config_file):
        self.config = config
        self.crypto = crypto
        self.config_file = config_file

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Changer le mot de passe")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        frame = ttk.Frame(self.dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Modification du mot de passe",
                  font=('Arial', 12, 'bold')).pack(pady=10)

        # Ancien mot de passe
        ttk.Label(frame, text="Ancien mot de passe:").pack(anchor=tk.W, pady=5)
        self.entry_old_pwd = ttk.Entry(frame, width=40, show='*')
        self.entry_old_pwd.pack(pady=5)

        # Nouveau mot de passe
        ttk.Label(frame, text="Nouveau mot de passe:").pack(anchor=tk.W, pady=5)
        self.entry_new_pwd = ttk.Entry(frame, width=40, show='*')
        self.entry_new_pwd.pack(pady=5)

        # Confirmation
        ttk.Label(frame, text="Confirmer le nouveau mot de passe:").pack(anchor=tk.W, pady=5)
        self.entry_confirm_pwd = ttk.Entry(frame, width=40, show='*')
        self.entry_confirm_pwd.pack(pady=5)

        # Boutons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="Valider", command=self.change_password).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Annuler", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)

    def change_password(self):
        """Change le mot de passe"""
        old_pwd = self.entry_old_pwd.get()
        new_pwd = self.entry_new_pwd.get()
        confirm_pwd = self.entry_confirm_pwd.get()

        # Vérification de l'ancien mot de passe
        stored_pwd = self.crypto.decrypt(self.config.get('admin', 'motdepasse'))
        if old_pwd != stored_pwd:
            messagebox.showerror("Erreur", "L'ancien mot de passe est incorrect")
            return

        if not new_pwd:
            messagebox.showerror("Erreur", "Le nouveau mot de passe ne peut pas être vide")
            return

        if new_pwd != confirm_pwd:
            messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas")
            return

        # Chiffrement et sauvegarde
        encrypted_pwd = self.crypto.encrypt(new_pwd)
        self.config.set('admin', 'motdepasse', encrypted_pwd)

        with open(self.config_file, 'w') as f:
            self.config.write(f)

        messagebox.showinfo("Succès", "Le mot de passe a été modifié avec succès")
        logging.info("Mot de passe administrateur modifié")
        self.dialog.destroy()


def main():
    """Fonction principale"""
    app = MakeITGUI()
    app.run()


if __name__ == "__main__":
    main()