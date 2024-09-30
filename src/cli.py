# src/cli.py

import argparse
from main import SimpleNoSQLDB, DatabaseManager
import json
import sys

def main():
    parser = argparse.ArgumentParser(description="Simple NoSQL Database CLI with Multiple Databases")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Database management commands
    db_parser = subparsers.add_parser('create_db', help='Create a new database')
    db_parser.add_argument('database', type=str, help='Name of the database to create')

    del_db_parser = subparsers.add_parser('delete_db', help='Delete an existing database')
    del_db_parser.add_argument('database', type=str, help='Name of the database to delete')

    list_db_parser = subparsers.add_parser('list_dbs', help='List all existing databases')

    # Data operation commands
    create_parser = subparsers.add_parser('create', help='Create a new key-value pair in a specified database')
    create_parser.add_argument('database', type=str, help='Name of the database')
    create_parser.add_argument('key', type=str, help='The key')
    create_parser.add_argument('value', type=str, help='The value (JSON string)')

    read_parser = subparsers.add_parser('read', help='Read the value of a key from a specified database')
    read_parser.add_argument('database', type=str, help='Name of the database')
    read_parser.add_argument('key', type=str, help='The key')

    update_parser = subparsers.add_parser('update', help='Update the value of an existing key in a specified database')
    update_parser.add_argument('database', type=str, help='Name of the database')
    update_parser.add_argument('key', type=str, help='The key')
    update_parser.add_argument('value', type=str, help='The new value (JSON string)')

    delete_parser = subparsers.add_parser('delete', help='Delete a key-value pair from a specified database')
    delete_parser.add_argument('database', type=str, help='Name of the database')
    delete_parser.add_argument('key', type=str, help='The key')

    list_keys_parser = subparsers.add_parser('list', help='List all keys in a specified database')
    list_keys_parser.add_argument('database', type=str, help='Name of the database')

    query_parser = subparsers.add_parser('query', help='Query the database')
    query_parser.add_argument('database', type=str, help='Name of the database')
    query_parser.add_argument('field', type=str, help='Field to query')
    query_parser.add_argument('operator', type=str, choices=['=', '!=', '>', '<', '>=', '<='], help='Comparison operator')
    query_parser.add_argument('value', type=str, help='Value to compare against')

    args = parser.parse_args()
    db_manager = DatabaseManager()

    if args.command == 'create_db':
        try:
            db_manager.create_database(args.database)
            print(f"Database '{args.database}' created successfully.")
        except FileExistsError as e:
            print(e)

    elif args.command == 'delete_db':
        try:
            db_manager.delete_database(args.database)
            print(f"Database '{args.database}' deleted successfully.")
        except FileNotFoundError as e:
            print(e)

    elif args.command == 'list_dbs':
        dbs = db_manager.list_databases()
        if not dbs:
            print("No databases found.")
        else:
            print("Databases:")
            for db in dbs:
                print(f"- {db}")

    elif args.command == 'create':
        try:
            db = db_manager.get_db(args.database)
        except FileNotFoundError as e:
            print(e)
            sys.exit(1)
        print(f"Received value: {args.value}")  # Debugging line
        try:
            value = json.loads(args.value)
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            print("Ensure that the value is a valid JSON string.")
            sys.exit(1)
        try:
            db.create(args.key, value)
            print(f"Key '{args.key}' created successfully in database '{args.database}'.")
        except KeyError as e:
            print(e)

    elif args.command == 'read':
        try:
            db = db_manager.get_db(args.database)
        except FileNotFoundError as e:
            print(e)
            sys.exit(1)
        value = db.read(args.key)
        if value is not None:
            print(f"Value for key '{args.key}' in database '{args.database}':")
            print(json.dumps(value, indent=4))
        else:
            print(f"Key '{args.key}' not found in database '{args.database}'.")

    elif args.command == 'update':
        try:
            db = db_manager.get_db(args.database)
        except FileNotFoundError as e:
            print(e)
            sys.exit(1)
        print(f"Received value: {args.value}")  # Debugging line
        try:
            value = json.loads(args.value)
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            print("Ensure that the value is a valid JSON string.")
            sys.exit(1)
        try:
            db.update(args.key, value)
            print(f"Key '{args.key}' updated successfully in database '{args.database}'.")
        except KeyError as e:
            print(e)

    elif args.command == 'delete':
        try:
            db = db_manager.get_db(args.database)
        except FileNotFoundError as e:
            print(e)
            sys.exit(1)
        try:
            db.delete(args.key)
            print(f"Key '{args.key}' deleted successfully from database '{args.database}'.")
        except KeyError as e:
            print(e)

    elif args.command == 'list':
        try:
            db = db_manager.get_db(args.database)
        except FileNotFoundError as e:
            print(e)
            sys.exit(1)
        keys = db.list_keys()
        if not keys:
            print(f"No keys found in database '{args.database}'.")
        else:
            print(f"Keys in database '{args.database}':")
            for key in keys:
                print(f"- {key}")

    elif args.command == 'query':
        try:
            db = db_manager.get_db(args.database)
        except FileNotFoundError as e:
            print(e)
            sys.exit(1)
        try:
            # Attempt to parse value as JSON (number, string, etc.)
            value = json.loads(args.value)
        except json.JSONDecodeError:
            value = args.value

        results = db.query(args.field, args.operator, value)
        if not results:
            print("No records match the query.")
        else:
            print("Query Results:")
            for k, v in results.items():
                print(f"{k}: {json.dumps(v, indent=4)}")

    else:
        parser.print_help()

if __name__ == '__main__':
    main()
