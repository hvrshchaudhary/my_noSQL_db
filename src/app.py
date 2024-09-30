# src/app.py

from flask import Flask, render_template, request, redirect, url_for, flash
from main import DatabaseManager
import json
import os
import sys

app = Flask(__name__)
app.secret_key = 'your_secure_secret_key'  # Replace with a secure secret key
db_manager = DatabaseManager()

# Home Page: List Databases and Create New Database
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle Create Database Form Submission
        db_name = request.form.get('db_name')
        if db_name:
            try:
                db_manager.create_database(db_name)
                flash(f"Database '{db_name}' created successfully.")
                return redirect(url_for('index'))
            except FileExistsError as e:
                flash(str(e))
        else:
            flash('Database name is required.')
    databases = db_manager.list_databases()
    return render_template('index.html', databases=databases)

# Delete Database from Home Page
@app.route('/delete_database/<db_name>', methods=['POST'])
def delete_database_from_home(db_name):
    try:
        db_manager.delete_database(db_name)
        flash(f"Database '{db_name}' deleted successfully.")
    except FileNotFoundError as e:
        flash(str(e))
    return redirect(url_for('index'))

# Database Interaction Page
@app.route('/database/<db_name>', methods=['GET', 'POST'])
def database(db_name):
    try:
        db = db_manager.get_db(db_name)
    except FileNotFoundError as e:
        flash(str(e))
        return redirect(url_for('index'))

    action = request.args.get('action', 'home')

    if action == 'create':
        if request.method == 'POST':
            key = request.form.get('key')
            value = request.form.get('value')
            if key and value:
                try:
                    value = json.loads(value)
                    db.create(key, value)
                    flash(f"Key '{key}' created successfully in database '{db_name}'.")
                    return redirect(url_for('database', db_name=db_name))
                except json.JSONDecodeError:
                    flash('Invalid JSON value.')
                except KeyError as e:
                    flash(str(e))
            else:
                flash('Both key and value are required.')
        return render_template('create.html', db_name=db_name)

    elif action == 'create_multiple':
        if request.method == 'POST':
            records_text = request.form.get('records')
            if records_text:
                try:
                    records = json.loads(records_text)
                    if isinstance(records, dict):
                        success_count = 0
                        error_messages = []
                        for key, value in records.items():
                            try:
                                db.create(key, value)
                                success_count += 1
                            except KeyError as e:
                                error_messages.append(f"Key '{key}': {str(e)}")
                        if success_count:
                            flash(f"Successfully created {success_count} record(s) in database '{db_name}'.")
                        if error_messages:
                            for msg in error_messages:
                                flash(msg)
                        return redirect(url_for('database', db_name=db_name))
                    else:
                        flash('The input must be a JSON object with key-value pairs.')
                except json.JSONDecodeError:
                    flash('Invalid JSON format.')
            else:
                flash('Records input is required.')
        return render_template('create_multiple.html', db_name=db_name)

    elif action == 'read':
        record = None
        if request.method == 'POST':
            key = request.form.get('key')
            if key:
                record = db.read(key)
                if record is None:
                    flash(f"Key '{key}' not found in database '{db_name}'.")
            else:
                flash('Key is required.')
        return render_template('read.html', db_name=db_name, record=record)

    elif action == 'update':
        if request.method == 'POST':
            key = request.form.get('key')
            new_value = request.form.get('value')
            if key and new_value:
                try:
                    new_value = json.loads(new_value)
                    db.update(key, new_value)
                    flash(f"Key '{key}' updated successfully in database '{db_name}'.")
                    return redirect(url_for('database', db_name=db_name))
                except json.JSONDecodeError:
                    flash('Invalid JSON value.')
                except KeyError as e:
                    flash(str(e))
            else:
                flash('Both key and new value are required.')
        return render_template('update.html', db_name=db_name)

    elif action == 'delete':
        if request.method == 'POST':
            key = request.form.get('key')
            if key:
                try:
                    db.delete(key)
                    flash(f"Key '{key}' deleted successfully from database '{db_name}'.")
                    return redirect(url_for('database', db_name=db_name))
                except KeyError as e:
                    flash(str(e))
            else:
                flash('Key is required.')
        return render_template('delete.html', db_name=db_name)

    elif action == 'list_keys':
        keys = db.list_keys()
        return render_template('list_keys.html', db_name=db_name, keys=keys)

    elif action == 'query':
        results = None
        if request.method == 'POST':
            field = request.form.get('field')
            operator = request.form.get('operator')
            value = request.form.get('value')
            if field and operator and value:
                try:
                    try:
                        # Attempt to parse value as JSON
                        value_parsed = json.loads(value)
                    except json.JSONDecodeError:
                        value_parsed = value
                    results = db.query(field, operator, value_parsed)
                    if not results:
                        flash('No records match the query.')
                except KeyError as e:
                    flash(str(e))
            else:
                flash('All fields are required.')
        return render_template('query.html', db_name=db_name, results=results)

    else:
        # Default Home View within Database
        return render_template('database.html', db_name=db_name)

if __name__ == '__main__':
    app.run(debug=True)
