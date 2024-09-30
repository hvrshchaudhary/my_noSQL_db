# src/main.py

import json
import os
import threading

class SimpleNoSQLDB:
    def __init__(self, db_file):
        """
        Initialize the SimpleNoSQLDB with the specified database file.
        """
        self.db_file = db_file
        self.lock = threading.Lock()
        self._load_data()

    def _load_data(self):
        """Load data from the JSON file into the in-memory store."""
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r') as f:
                try:
                    self.store = json.load(f)
                except json.JSONDecodeError:
                    self.store = {}
        else:
            self.store = {}

    def _save_data(self):
        """Save the in-memory store to the JSON file."""
        with open(self.db_file, 'w') as f:
            json.dump(self.store, f, indent=4)

    def create(self, key, value):
        """Create a new key-value pair in the database."""
        with self.lock:
            if key in self.store:
                raise KeyError(f"Key '{key}' already exists.")
            self.store[key] = value
            self._save_data()

    def read(self, key):
        """Read the value associated with a key."""
        with self.lock:
            return self.store.get(key, None)

    def update(self, key, value):
        """Update the value of an existing key."""
        with self.lock:
            if key not in self.store:
                raise KeyError(f"Key '{key}' does not exist.")
            self.store[key] = value
            self._save_data()

    def delete(self, key):
        """Delete a key-value pair from the database."""
        with self.lock:
            if key in self.store:
                del self.store[key]
                self._save_data()
            else:
                raise KeyError(f"Key '{key}' does not exist.")

    def list_keys(self):
        """List all keys in the database."""
        with self.lock:
            return list(self.store.keys())

    def query(self, field, operator, value):
        """
        Query the database for records where a field meets a condition.
        Supported operators: '=', '!=', '>', '<', '>=', '<='.
        """
        with self.lock:
            results = {}
            for key, record in self.store.items():
                if isinstance(record, dict):
                    record_value = record.get(field)
                    if record_value is None:
                        continue
                    if self._compare(record_value, operator, value):
                        results[key] = record
                else:
                    # Skip non-dict records for field-based queries
                    continue
            return results

    def _compare(self, record_value, operator, value):
        """Helper method to compare values based on the operator."""
        try:
            # Attempt to convert both values to float for numerical comparisons
            record_num = float(record_value)
            value_num = float(value)
            if operator == '=':
                return record_num == value_num
            elif operator == '!=':
                return record_num != value_num
            elif operator == '>':
                return record_num > value_num
            elif operator == '<':
                return record_num < value_num
            elif operator == '>=':
                return record_num >= value_num
            elif operator == '<=':
                return record_num <= value_num
        except (ValueError, TypeError):
            # If conversion fails, fall back to string comparison
            if operator == '=':
                return str(record_value) == str(value)
            elif operator == '!=':
                return str(record_value) != str(value)
            elif operator == '>':
                return str(record_value) > str(value)
            elif operator == '<':
                return str(record_value) < str(value)
            elif operator == '>=':
                return str(record_value) >= str(value)
            elif operator == '<=':
                return str(record_value) <= str(value)
        return False

class DatabaseManager:
    def __init__(self, databases_dir='../data/databases'):
        """
        Initialize the DatabaseManager with the specified directory for databases.
        """
        self.databases_dir = databases_dir
        if not os.path.exists(self.databases_dir):
            os.makedirs(self.databases_dir)

    def create_database(self, db_name):
        """
        Create a new database with the given name.
        """
        db_file = self._get_db_file(db_name)
        if os.path.exists(db_file):
            raise FileExistsError(f"Database '{db_name}' already exists.")
        with open(db_file, 'w') as f:
            json.dump({}, f, indent=4)

    def delete_database(self, db_name):
        """
        Delete the specified database.
        """
        db_file = self._get_db_file(db_name)
        if os.path.exists(db_file):
            os.remove(db_file)
        else:
            raise FileNotFoundError(f"Database '{db_name}' does not exist.")

    def list_databases(self):
        """
        List all existing databases.
        """
        return [f[:-5] for f in os.listdir(self.databases_dir) if f.endswith('.json')]

    def get_db(self, db_name):
        """
        Retrieve a SimpleNoSQLDB instance for the specified database.
        """
        db_file = self._get_db_file(db_name)
        if not os.path.exists(db_file):
            raise FileNotFoundError(f"Database '{db_name}' does not exist.")
        return SimpleNoSQLDB(db_file)

    def _get_db_file(self, db_name):
        """
        Get the file path for the specified database.
        """
        return os.path.join(self.databases_dir, f"{db_name}.json")
