import sqlite3
import re
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path
from constants import *


class WolManager:
    """
    Manager for the SQLite database of Wake-on-LAN MAC addresses.
    """

    def __init__(self, db_path: str = "config.sqlite"):
        """
        Initializes the manager with the database path.

        Args:
        db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._ensure_database_exists()

    def _ensure_database_exists(self):
        """Verify that the database and table exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS mac_list (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        mac_address TEXT NOT NULL,
                        name TEXT NOT NULL,
                        datetime TEXT NOT NULL
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Error initializing the database : {e}")

    def read_mac_address(self, name: str) -> List[str]:
        """
        Reads all MAC addresses associated with a given name.

        Args:

        name: The name for which to retrieve MAC addresses

        Returns:
        List of MAC addresses found (can be empty)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT mac_address FROM mac_list WHERE name = ? ORDER BY datetime DESC",
                    (name,)
                )
                results = cursor.fetchall()
                return [row[0] for row in results]
        except sqlite3.Error as e:
            raise Exception(f"Error reading MAC addresses: {e}")

    def _validate_mac_address(self, mac: str) -> bool:
        """
        Validate MAC address format.

        Args:
            mac: MAC address string to validate.

        Returns:
            True if valid, False otherwise.
        """
        # Accept formats: XX-XX-XX-XX-XX-XX or XX:XX:XX:XX:XX:XX
        pattern = r'^([0-9A-Fa-f]{2}[-:]){5}[0-9A-Fa-f]{2}$'
        return bool(re.match(pattern, mac))

    def update_mac_address(self, mac: str, name: str) -> int:
        """
        Inserts a new entry with the provided MAC address and name.

        The date and time are automatically set to the current time.

        Args:
        mac: The MAC address to insert
        name: The name associated with the MAC address

        Returns:
        The ID of the inserted entry

        Raises:
        ValueError: If MAC address format is invalid.
        """
        # Validate MAC address format
        if not self._validate_mac_address(mac):
            raise ValueError(f"Invalid MAC address format: {mac}")

        try:
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO mac_list (mac_address, name, datetime) VALUES (?, ?, ?)",
                    (mac, name, current_datetime)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            raise Exception(f"Error inserting MAC address: {e}")

    def clean_base(self, days: int) -> int:
        """
        Deletes entries older than the specified number of days.

        Args:
        days: Number of days. Older entries will be deleted.

        Returns:
        The number of deleted rows
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM mac_list WHERE datetime < ?",
                    (cutoff_date,)
                )
                conn.commit()
                return cursor.rowcount
        except sqlite3.Error as e:
            raise Exception(f"Error during database cleanup: {e}")

    def get_all_entries(self) -> List[tuple]:
        """
        Retrieves all entries from the database.

        Returns:
        List of tuples (id, mac_address, name, datetime)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, mac_address, name, datetime FROM mac_list ORDER BY datetime DESC")
                return cursor.fetchall()
        except sqlite3.Error as e:
            raise Exception(f"Error retrieving inputs: {e}")

    def delete_by_id(self, entry_id: int) -> bool:
        """
        Deletes a specific entry by its ID.

        Args:
        entry_id: The ID of the entry to delete

        Returns:
        True if a row was deleted, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM mac_list WHERE id = ?", (entry_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            raise Exception(f"Error deleting entry: {e}")


if __name__ == "__main__":
    # GUI
    wol_manager = WolManager("config.sqlite")

    # Insert datas
    print("Inserting new MAC addresses...")
    id1 = wol_manager.update_mac_address("6C-02-E0-00-8D-39", "P123456-0AZ-032")
    id2 = wol_manager.update_mac_address("AA-BB-CC-DD-EE-FF", "P123456-0AZ-032")
    id3 = wol_manager.update_mac_address("11-22-33-44-55-66", "P789012-1BC-045")
    print(f"IDs inserted: {id1}, {id2}, {id3}")

    # Reading MAC addresses for a given name
    print("\nLecture des adresses MAC pour 'P123456-0AZ-032':")
    mac_list = wol_manager.read_mac_address("P123456-0AZ-032")
    for mac in mac_list:
        print(f"  - {mac}")

    # Displaying all entries
    print("\nToutes les entrées:")
    all_entries = wol_manager.get_all_entries()
    for entry in all_entries:
        print(f"  ID: {entry[0]}, MAC: {entry[1]}, Name: {entry[2]}, Date: {entry[3]}")

    # Cleaning up old data (> 30 days)
    print("\nNettoyage des données de plus de 30 jours...")
    deleted_count = wol_manager.clean_base(MAC_RETENTION_DAYS)
