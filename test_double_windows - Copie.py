import tkinter as tk
from tkinter import ttk, messagebox
import os
import shutil
from pathlib import Path
import threading


class DualFileExplorer:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestionnaire de Fichiers - Double Panneau")
        self.root.geometry("1200x700")

        # Chemins initiaux
        self.left_path = r"C:\PMF"
        self.right_path = r"\\55.156.49.61\c$"  # À adapter

        self.setup_ui()
        self.refresh_both()

    def setup_ui(self):
        # === TOOLBAR ===
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Label(toolbar, text="IP distante:").pack(side=tk.LEFT, padx=5)
        self.ip_entry = ttk.Entry(toolbar, width=15)
        self.ip_entry.insert(0, "192.168.1.50")
        self.ip_entry.pack(side=tk.LEFT)

        ttk.Button(toolbar, text="Connecter",
                   command=self.connect_remote).pack(side=tk.LEFT, padx=5)

        # === PANNEAU PRINCIPAL ===
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # PANNEAU GAUCHE (Local)
        left_frame = ttk.LabelFrame(main_frame, text="📁 Local", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Barre d'adresse gauche
        self.left_path_var = tk.StringVar(value=self.left_path)
        left_addr = ttk.Entry(left_frame, textvariable=self.left_path_var)
        left_addr.pack(fill=tk.X, pady=(0, 5))
        left_addr.bind('<Return>', lambda e: self.refresh_left())

        # Arbre gauche
        left_tree_frame = ttk.Frame(left_frame)
        left_tree_frame.pack(fill=tk.BOTH, expand=True)

        left_scroll = ttk.Scrollbar(left_tree_frame)
        left_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.left_tree = ttk.Treeview(
            left_tree_frame,
            columns=('size', 'modified'),
            yscrollcommand=left_scroll.set
        )
        self.left_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_scroll.config(command=self.left_tree.yview)

        self.left_tree.heading('#0', text='Nom')
        self.left_tree.heading('size', text='Taille')
        self.left_tree.heading('modified', text='Modifié')
        self.left_tree.column('size', width=100)
        self.left_tree.column('modified', width=150)

        self.left_tree.bind('<Double-1>', lambda e: self.on_double_click('left'))

        # PANNEAU CENTRAL (Boutons)
        middle_frame = ttk.Frame(main_frame, width=80)
        middle_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        middle_frame.pack_propagate(False)

        ttk.Label(middle_frame, text="Actions",
                  font=('Arial', 10, 'bold')).pack(pady=10)

        ttk.Button(middle_frame, text="→ Copier →",
                   command=self.copy_left_to_right,
                   width=12).pack(pady=5)

        ttk.Button(middle_frame, text="← Copier ←",
                   command=self.copy_right_to_left,
                   width=12).pack(pady=5)

        ttk.Separator(middle_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        ttk.Button(middle_frame, text="🗑️ Supprimer",
                   command=self.delete_selected,
                   width=12).pack(pady=5)

        ttk.Button(middle_frame, text="🔄 Actualiser",
                   command=self.refresh_both,
                   width=12).pack(pady=5)

        # PANNEAU DROIT (Réseau)
        right_frame = ttk.LabelFrame(main_frame, text="🌐 Réseau", padding=5)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Barre d'adresse droite
        self.right_path_var = tk.StringVar(value=self.right_path)
        right_addr = ttk.Entry(right_frame, textvariable=self.right_path_var)
        right_addr.pack(fill=tk.X, pady=(0, 5))
        right_addr.bind('<Return>', lambda e: self.refresh_right())

        # Arbre droit
        right_tree_frame = ttk.Frame(right_frame)
        right_tree_frame.pack(fill=tk.BOTH, expand=True)

        right_scroll = ttk.Scrollbar(right_tree_frame)
        right_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.right_tree = ttk.Treeview(
            right_tree_frame,
            columns=('size', 'modified'),
            yscrollcommand=right_scroll.set
        )
        self.right_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_scroll.config(command=self.right_tree.yview)

        self.right_tree.heading('#0', text='Nom')
        self.right_tree.heading('size', text='Taille')
        self.right_tree.heading('modified', text='Modifié')
        self.right_tree.column('size', width=100)
        self.right_tree.column('modified', width=150)

        self.right_tree.bind('<Double-1>', lambda e: self.on_double_click('right'))

        # === BARRE DE STATUS ===
        self.status_var = tk.StringVar(value="Prêt")
        status_bar = ttk.Label(self.root, textvariable=self.status_var,
                               relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def connect_remote(self):
        ip = self.ip_entry.get()
        self.right_path = f"\\\\{ip}\\c$"
        self.right_path_var.set(self.right_path)
        self.refresh_right()

    def list_directory(self, path):
        """Liste le contenu d'un répertoire"""
        try:
            items = []

            # Ajouter ".." pour remonter
            if path != os.path.dirname(path):  # Pas à la racine
                items.append({
                    'name': '..',
                    'path': os.path.dirname(path),
                    'is_dir': True,
                    'size': '',
                    'modified': ''
                })

            # Lister les fichiers et dossiers
            for entry in os.scandir(path):
                try:
                    stat = entry.stat()
                    items.append({
                        'name': entry.name,
                        'path': entry.path,
                        'is_dir': entry.is_dir(),
                        'size': self.format_size(stat.st_size) if not entry.is_dir() else '<DIR>',
                        'modified': self.format_time(stat.st_mtime)
                    })
                except:
                    continue  # Ignorer les fichiers inaccessibles

            # Trier : dossiers d'abord
            items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
            return items

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire {path}\n{str(e)}")
            return []

    def populate_tree(self, tree, items):
        """Remplit un TreeView avec des items"""
        # Vider l'arbre
        tree.delete(*tree.get_children())

        # Ajouter chaque item
        for item in items:
            icon = '📁' if item['is_dir'] else '📄'

            tree.insert(
                '',
                tk.END,
                text=f"{icon} {item['name']}",
                values=(item['size'], item['modified']),
                tags=(item['path'], 'dir' if item['is_dir'] else 'file')
            )

    def refresh_left(self):
        path = self.left_path_var.get()
        if os.path.exists(path):
            self.left_path = path
            items = self.list_directory(path)
            self.populate_tree(self.left_tree, items)
            self.status_var.set(f"Local: {len(items)} éléments")

    def refresh_right(self):
        path = self.right_path_var.get()
        if os.path.exists(path):
            self.right_path = path
            items = self.list_directory(path)
            self.populate_tree(self.right_tree, items)
            self.status_var.set(f"Réseau: {len(items)} éléments")

    def refresh_both(self):
        self.refresh_left()
        self.refresh_right()

    def on_double_click(self, side):
        """Navigation dans les dossiers"""
        tree = self.left_tree if side == 'left' else self.right_tree
        selection = tree.selection()

        if not selection:
            return

        item = selection[0]
        tags = tree.item(item, 'tags')

        if len(tags) > 0:
            path = tags[0]
            is_dir = 'dir' in tags

            if is_dir:
                if side == 'left':
                    self.left_path = path
                    self.left_path_var.set(path)
                    self.refresh_left()
                else:
                    self.right_path = path
                    self.right_path_var.set(path)
                    self.refresh_right()

    def get_selected_path(self, tree):
        """Récupère le chemin du fichier sélectionné"""
        selection = tree.selection()
        if not selection:
            return None

        item = selection[0]
        tags = tree.item(item, 'tags')
        return tags[0] if tags else None

    def copy_left_to_right(self):
        src = self.get_selected_path(self.left_tree)
        if not src:
            messagebox.showwarning("Attention", "Sélectionnez un fichier à gauche")
            return

        if os.path.isdir(src):
            messagebox.showinfo("Info", "La copie de dossiers n'est pas encore implémentée")
            return

        dst = os.path.join(self.right_path, os.path.basename(src))
        self.copy_file(src, dst, 'right')

    def copy_right_to_left(self):
        src = self.get_selected_path(self.right_tree)
        if not src:
            messagebox.showwarning("Attention", "Sélectionnez un fichier à droite")
            return

        if os.path.isdir(src):
            messagebox.showinfo("Info", "La copie de dossiers n'est pas encore implémentée")
            return

        dst = os.path.join(self.left_path, os.path.basename(src))
        self.copy_file(src, dst, 'left')

    def copy_file(self, src, dst, refresh_side):
        """Copie un fichier avec barre de progression"""

        def do_copy():
            try:
                self.status_var.set(f"Copie de {os.path.basename(src)}...")
                shutil.copy2(src, dst)
                self.status_var.set(f"✅ Copie terminée : {os.path.basename(src)}")

                # Rafraîchir le côté destination
                if refresh_side == 'left':
                    self.refresh_left()
                else:
                    self.refresh_right()

            except Exception as e:
                messagebox.showerror("Erreur de copie", str(e))
                self.status_var.set("❌ Erreur de copie")

        # Lancer dans un thread pour ne pas bloquer l'UI
        threading.Thread(target=do_copy, daemon=True).start()

    def delete_selected(self):
        # Déterminer quel panneau est actif
        if self.left_tree.focus():
            tree = self.left_tree
            side = 'left'
        elif self.right_tree.focus():
            tree = self.right_tree
            side = 'right'
        else:
            messagebox.showwarning("Attention", "Sélectionnez un fichier")
            return

        path = self.get_selected_path(tree)
        if not path:
            return

        if messagebox.askyesno("Confirmation",
                               f"Supprimer définitivement :\n{path} ?"):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)

                self.status_var.set(f"✅ Supprimé : {os.path.basename(path)}")

                if side == 'left':
                    self.refresh_left()
                else:
                    self.refresh_right()

            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de supprimer\n{str(e)}")

    @staticmethod
    def format_size(size):
        """Formate la taille en Ko, Mo, Go"""
        for unit in ['o', 'Ko', 'Mo', 'Go']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} To"

    @staticmethod
    def format_time(timestamp):
        """Formate un timestamp"""
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')


def main():
    root = tk.Tk()
    app = DualFileExplorer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
