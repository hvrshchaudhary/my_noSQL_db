# src/main.py

import json
import os
import threading
import copy

class SimpleNoSQLDB:
    def __init__(self, db_file, in_transaction=False, transaction_store=None):
        """
        Initialize the SimpleNoSQLDB with the specified database file and transaction state.
        """
        self.db_file = db_file
        self.lock = threading.Lock()
        self._load_data()
        self.in_transaction = in_transaction
        if in_transaction and transaction_store is not None:
            self.transaction_store = transaction_store
        else:
            self.transaction_store = None

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
        """Save the in-memory store to the JSON file atomically."""
        dir_name = os.path.dirname(self.db_file)
        temp_file = os.path.join(dir_name, 'temp.json')
        with open(temp_file, 'w') as f:
            json.dump(self.store, f, indent=4)
        os.replace(temp_file, self.db_file)

    def begin_transaction(self):
        """Begin a new transaction."""
        with self.lock:
            if not self.in_transaction:
                self.in_transaction = True
                self.transaction_store = copy.deepcopy(self.store)
            else:
                raise Exception("Transaction already in progress.")

    def commit(self):
        """Commit the current transaction."""
        with self.lock:
            if self.in_transaction:
                self.store = self.transaction_store
                self._save_data()
                self.transaction_store = None
                self.in_transaction = False
            else:
                raise Exception("No transaction in progress.")

    def rollback(self):
        """Rollback the current transaction."""
        with self.lock:
            if self.in_transaction:
                self.transaction_store = None
                self.in_transaction = False
            else:
                raise Exception("No transaction in progress.")

    def create(self, key, value):
        """Create a new key-value pair in the database."""
        with self.lock:
            target_store = self.transaction_store if self.in_transaction else self.store
            if key in target_store:
                raise KeyError(f"Key '{key}' already exists.")
            target_store[key] = value
            if not self.in_transaction:
                self._save_data()

    def read(self, key):
        """Read the value associated with a key."""
        with self.lock:
            target_store = self.transaction_store if self.in_transaction else self.store
            return target_store.get(key, None)

    def update(self, key, value):
        """Update the value of an existing key."""
        with self.lock:
            target_store = self.transaction_store if self.in_transaction else self.store
            if key not in target_store:
                raise KeyError(f"Key '{key}' does not exist.")
            target_store[key] = value
            if not self.in_transaction:
                self._save_data()

    def delete(self, key):
        """Delete a key-value pair from the database."""
        with self.lock:
            target_store = self.transaction_store if self.in_transaction else self.store
            if key in target_store:
                del target_store[key]
                if not self.in_transaction:
                    self._save_data()
            else:
                raise KeyError(f"Key '{key}' does not exist.")

    def list_keys(self):
        """List all keys in the database."""
        with self.lock:
            target_store = self.transaction_store if self.in_transaction else self.store
            return list(target_store.keys())

    def query(self, field, operator, value):
        """
        Query the database for records where a field meets a condition.
        Supported operators: '=', '!=', '>', '<', '>=', '<='.
        """
        with self.lock:
            target_store = self.transaction_store if self.in_transaction else self.store
            results = {}
            for key, record in target_store.items():
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

    def get_db(self, db_name, in_transaction=False, transaction_store=None):
        """
        Retrieve a SimpleNoSQLDB instance for the specified database with transaction state.
        """
        db_file = self._get_db_file(db_name)
        if not os.path.exists(db_file):
            raise FileNotFoundError(f"Database '{db_name}' does not exist.")
        return SimpleNoSQLDB(db_file, in_transaction, transaction_store)

    def _get_db_file(self, db_name):
        """
        Get the file path for the specified database.
        """
        return os.path.join(self.databases_dir, f"{db_name}.json")
