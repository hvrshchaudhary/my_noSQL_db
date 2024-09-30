# src/app.py

from flask import Flask, render_template, request, redirect, url_for, flash, session
from main import DatabaseManager
import json
import os
from urllib.parse import urlparse, urljoin

app = Flask(__name__)
app.secret_key = 'your_secure_secret_key'  # Replace with a secure secret key
db_manager = DatabaseManager()

def is_safe_url(target):
    """Check if the URL is safe for redirection to prevent open redirects."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (
        test_url.scheme in ('http', 'https') and
        ref_url.netloc == test_url.netloc
    )

@app.context_processor
def inject_current_url():
    """Make the current URL available in all templates."""
    return {'current_url': request.url}

# Home Page: List Databases and Create New Database
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle Create Database Form Submission
        db_name = request.form.get('db_name')
        if db_name:
            try:
                db_manager.create_database(db_name)
                flash(f"Database '{db_name}' created successfully.", 'success')
                return redirect(url_for('index'))
            except FileExistsError as e:
                flash(str(e), 'danger')
        else:
            flash('Database name is required.', 'warning')
    databases = db_manager.list_databases()
    return render_template('index.html', databases=databases)

# Delete Database from Home Page
@app.route('/delete_database/<db_name>', methods=['POST'])
def delete_database_from_home(db_name):
    try:
        db_manager.delete_database(db_name)
        flash(f"Database '{db_name}' deleted successfully.", 'success')
    except FileNotFoundError as e:
        flash(str(e), 'danger')
    return redirect(url_for('index'))

# Database Interaction Page
@app.route('/database/<db_name>', methods=['GET', 'POST'])
def database(db_name):
    # Retrieve transaction state from session
    in_transaction = session.get('in_transaction', False)
    transaction_store = session.get('transaction_store', None)

    try:
        db = db_manager.get_db(db_name, in_transaction, transaction_store)
        session['db_name'] = db_name  # Store current db_name in session
    except FileNotFoundError as e:
        flash(str(e), 'danger')
        return redirect(url_for('index'))

    action = request.args.get('action', 'home')
    next_url = request.args.get('next')

    if action in ['begin_transaction', 'commit', 'rollback']:
        # Validate the next_url
        if next_url and not is_safe_url(next_url):
            flash('Invalid redirection URL.', 'danger')
            next_url = url_for('database', db_name=db_name)

        if action == 'begin_transaction':
            if in_transaction:
                flash('A transaction is already in progress.', 'warning')
            else:
                try:
                    db.begin_transaction()
                    # Update session with transaction state
                    session['in_transaction'] = db.in_transaction
                    session['transaction_store'] = db.transaction_store
                    flash(f"Transaction started on database '{db_name}'.", 'info')
                except Exception as e:
                    flash(str(e), 'danger')
        elif action == 'commit':
            if not in_transaction:
                flash('No active transaction to commit.', 'warning')
            else:
                try:
                    db.commit()
                    # Update session with transaction state
                    session['in_transaction'] = db.in_transaction
                    session['transaction_store'] = None
                    flash(f"Transaction committed on database '{db_name}'.", 'success')
                except Exception as e:
                    flash(str(e), 'danger')
        elif action == 'rollback':
            if not in_transaction:
                flash('No active transaction to rollback.', 'warning')
            else:
                try:
                    db.rollback()
                    # Update session with transaction state
                    session['in_transaction'] = db.in_transaction
                    session['transaction_store'] = None
                    flash(f"Transaction rolled back on database '{db_name}'.", 'info')
                except Exception as e:
                    flash(str(e), 'danger')

        # Redirect back to the next_url or to the current page
        if next_url:
            return redirect(next_url)
        else:
            return redirect(url_for('database', db_name=db_name))

    elif action == 'create':
        if request.method == 'POST':
            if not in_transaction:
                flash('Please start a transaction first.', 'warning')
                return redirect(url_for('database', db_name=db_name))
            key = request.form.get('key')
            value = request.form.get('value')
            if key and value:
                try:
                    value = json.loads(value)
                    db.create(key, value)
                    session['transaction_store'] = db.transaction_store  # Update transaction_store in session
                    flash(f"Key '{key}' created successfully in database '{db_name}' (pending commit).", 'success')
                    return redirect(url_for('database', db_name=db_name, action='create'))
                except json.JSONDecodeError:
                    flash('Invalid JSON value.', 'danger')
                except KeyError as e:
                    flash(str(e), 'danger')
            else:
                flash('Both key and value are required.', 'warning')
        return render_template('create.html', db_name=db_name, in_transaction=in_transaction)

    elif action == 'create_multiple':
        if request.method == 'POST':
            if not in_transaction:
                flash('Please start a transaction first.', 'warning')
                return redirect(url_for('database', db_name=db_name))
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
                            flash(f"Successfully created {success_count} record(s) in database '{db_name}' (pending commit).", 'success')
                        if error_messages:
                            for msg in error_messages:
                                flash(msg, 'danger')
                        session['transaction_store'] = db.transaction_store  # Update transaction_store in session
                        return redirect(url_for('database', db_name=db_name, action='create_multiple'))
                    else:
                        flash('The input must be a JSON object with key-value pairs.', 'warning')
                except json.JSONDecodeError:
                    flash('Invalid JSON format.', 'danger')
            else:
                flash('Records input is required.', 'warning')
        return render_template('create_multiple.html', db_name=db_name, in_transaction=in_transaction)

    elif action == 'read':
        record = None
        if request.method == 'POST':
            key = request.form.get('key')
            if key:
                record = db.read(key)
                if record is None:
                    flash(f"Key '{key}' not found in database '{db_name}'.", 'warning')
            else:
                flash('Key is required.', 'warning')
        return render_template('read.html', db_name=db_name, record=record, in_transaction=in_transaction)

    elif action == 'update':
        if request.method == 'POST':
            if not in_transaction:
                flash('Please start a transaction first.', 'warning')
                return redirect(url_for('database', db_name=db_name))
            key = request.form.get('key')
            new_value = request.form.get('value')
            if key and new_value:
                try:
                    new_value = json.loads(new_value)
                    db.update(key, new_value)
                    session['transaction_store'] = db.transaction_store  # Update transaction_store in session
                    flash(f"Key '{key}' updated successfully in database '{db_name}' (pending commit).", 'warning')
                    return redirect(url_for('database', db_name=db_name, action='update'))
                except json.JSONDecodeError:
                    flash('Invalid JSON value.', 'danger')
                except KeyError as e:
                    flash(str(e), 'danger')
            else:
                flash('Both key and new value are required.', 'warning')
        return render_template('update.html', db_name=db_name, in_transaction=in_transaction)

    elif action == 'delete':
        if request.method == 'POST':
            if not in_transaction:
                flash('Please start a transaction first.', 'warning')
                return redirect(url_for('database', db_name=db_name))
            key = request.form.get('key')
            if key:
                try:
                    db.delete(key)
                    session['transaction_store'] = db.transaction_store  # Update transaction_store in session
                    flash(f"Key '{key}' deleted successfully from database '{db_name}' (pending commit).", 'danger')
                    return redirect(url_for('database', db_name=db_name, action='delete'))
                except KeyError as e:
                    flash(str(e), 'danger')
            else:
                flash('Key is required.', 'warning')
        return render_template('delete.html', db_name=db_name, in_transaction=in_transaction)

    elif action == 'list_keys':
        keys = db.list_keys()
        return render_template('list_keys.html', db_name=db_name, keys=keys, in_transaction=in_transaction)

    elif action == 'query':
        results = None
        if request.method == 'POST':
            field = request.form.get('field')
            operator = request.form.get('operator')
            value = request.form.get('value')
            if field and operator and value:
                try:
                    try:
                        value_parsed = json.loads(value)
                    except json.JSONDecodeError:
                        value_parsed = value
                    results = db.query(field, operator, value_parsed)
                    if not results:
                        flash('No records match the query.', 'info')
                except KeyError as e:
                    flash(str(e), 'danger')
            else:
                flash('All fields are required.', 'warning')
        return render_template('query.html', db_name=db_name, results=results, in_transaction=in_transaction)

    else:
        # Default Home View within Database
        return render_template('database.html', db_name=db_name, in_transaction=in_transaction)

if __name__ == '__main__':
    app.run(debug=True)
