from flask import Flask, g, render_template, request, redirect, url_for, flash, jsonify, Response
import sqlite3
import os
from datetime import datetime

DATABASE = os.path.join(os.path.dirname(__file__), 'data.db')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev')  # defina SECRET_KEY em produção


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def init_db():
    """Inicializa o banco de dados a partir de schema.sql."""
    dirname = os.path.dirname(__file__)
    schema_path = os.path.join(dirname, 'schema.sql')
    conn = sqlite3.connect(DATABASE)
    with open(schema_path, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    # Ensure productions.activity_id column exists for linking to activities
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(productions)")
    cols = [r[1] for r in cur.fetchall()]
    if 'activity_id' not in cols:
        try:
            cur.execute('ALTER TABLE productions ADD COLUMN activity_id INTEGER')
        except Exception:
            # ignore if cannot alter
            pass
    # Ensure activities.goal_points column exists
    cur.execute("PRAGMA table_info(activities)")
    a_cols = [r[1] for r in cur.fetchall()]
    if 'goal_points' not in a_cols:
        try:
            cur.execute('ALTER TABLE activities ADD COLUMN goal_points INTEGER')
        except Exception:
            pass
    conn.commit()
    conn.close()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.context_processor
def inject_activity_progress():
    """Disponibiliza lista de atividades com percentual de meta cumprida para templates (sidebar)."""
    try:
        db = get_db()
        cur = db.execute('''
            SELECT a.id, a.name, a.goal_points, IFNULL(SUM(p.quantity),0) AS completed
            FROM activities a
            LEFT JOIN productions p ON p.activity_id = a.id
            GROUP BY a.id
            ORDER BY a.name
        ''')
        rows = cur.fetchall()
        activities = []
        for r in rows:
            goal = r['goal_points'] if r['goal_points'] is not None else 0
            completed = r['completed'] if r['completed'] is not None else 0
            percent = None
            if goal and goal > 0:
                percent = min(100, int((completed / goal) * 100))
            activities.append({
                'id': r['id'], 'name': r['name'], 'goal_points': goal, 'completed': completed, 'percent': percent
            })
        return {'activities_progress': activities}
    except Exception:
        return {'activities_progress': []}


@app.route('/')
def index():
    # visão geral simples com links
    return render_template('index.html')


# Activities
@app.route('/activities')
def activities_list():
    db = get_db()
    cur = db.execute('''
        SELECT a.id, a.name, a.date, a.description, a.created_at, a.goal_points, IFNULL(SUM(p.quantity),0) AS completed
        FROM activities a
        LEFT JOIN productions p ON p.activity_id = a.id
        GROUP BY a.id
        ORDER BY a.created_at DESC
    ''')
    rows = cur.fetchall()
    activities = []
    for r in rows:
        goal = r['goal_points'] if r['goal_points'] is not None else 0
        completed = r['completed'] if r['completed'] is not None else 0
        percent = None
        if goal and goal > 0:
            percent = min(100, int((completed / goal) * 100))
        activities.append({'id': r['id'], 'name': r['name'], 'date': r['date'], 'description': r['description'], 'created_at': r['created_at'], 'goal_points': goal, 'completed': completed, 'percent': percent})
    return render_template('activities_list.html', activities=activities)


@app.route('/activities/add', methods=['GET', 'POST'])
def activities_add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        date = request.form.get('date', '').strip()
        description = request.form.get('description', '').strip()
        goal_points = request.form.get('goal_points', '').strip()
        if not name:
            flash('Nome da atividade é obrigatório.')
            return redirect(url_for('activities_add'))
        db = get_db()
        try:
            gp = int(goal_points) if goal_points else None
        except ValueError:
            gp = None
        db.execute(
            'INSERT INTO activities (name, date, description, goal_points, created_at) VALUES (?, ?, ?, ?, ?)',
            (name, date, description, gp, datetime.utcnow().isoformat()),
        )
        db.commit()
        flash('Atividade adicionada com sucesso.')
        return redirect(url_for('activities_list'))
    return render_template('activities_add.html')


# Productions
@app.route('/productions')
def productions_list():
    db = get_db()
    cur = db.execute('''
        SELECT p.id, p.title, p.quantity, p.description, p.created_at, p.activity_id, a.name AS activity_name
        FROM productions p
        LEFT JOIN activities a ON p.activity_id = a.id
        ORDER BY p.created_at DESC
    ''')
    prods = cur.fetchall()
    return render_template('productions_list.html', productions=prods)


@app.route('/productions/add', methods=['GET', 'POST'])
def productions_add():
    if request.method == 'POST':
        quantity = request.form.get('quantity', '').strip()
        description = request.form.get('description', '').strip()
        activity_id = request.form.get('activity_id', '').strip()
        
        # activity_id is now required
        if not activity_id:
            flash('Atividade é obrigatória.')
            return redirect(url_for('productions_add'))
        
        try:
            aid = int(activity_id)
        except ValueError:
            flash('Atividade inválida.')
            return redirect(url_for('productions_add'))
        
        try:
            q = int(quantity) if quantity else None
        except ValueError:
            flash('Quantidade deve ser um número inteiro.')
            return redirect(url_for('productions_add'))
        
        db = get_db()
        # Get activity name to use as title
        cur = db.execute('SELECT name FROM activities WHERE id = ?', (aid,))
        activity = cur.fetchone()
        if not activity:
            flash('Atividade não encontrada.')
            return redirect(url_for('productions_add'))
        
        title = activity['name']  # Auto-generate title from activity name
        
        db.execute(
            'INSERT INTO productions (title, quantity, description, activity_id, created_at) VALUES (?, ?, ?, ?, ?)',
            (title, q, description, aid, datetime.utcnow().isoformat()),
        )
        db.commit()
        flash('Produção adicionada com sucesso.')
        return redirect(url_for('productions_list'))
    # pass activities for dropdown
    db = get_db()
    acts = db.execute('SELECT id, name FROM activities ORDER BY name').fetchall()
    return render_template('productions_add.html', activities=acts)


# Edit / Delete for activities
@app.route('/activities/<int:id>/edit', methods=['GET', 'POST'])
def activities_edit(id):
    db = get_db()
    cur = db.execute('SELECT * FROM activities WHERE id = ?', (id,))
    row = cur.fetchone()
    if row is None:
        flash('Atividade não encontrada.')
        return redirect(url_for('activities_list'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        date = request.form.get('date', '').strip()
        description = request.form.get('description', '').strip()
        goal_points = request.form.get('goal_points', '').strip()
        if not name:
            flash('Nome da atividade é obrigatório.')
            return redirect(url_for('activities_edit', id=id))
        try:
            gp = int(goal_points) if goal_points else None
        except ValueError:
            gp = None
        db.execute('UPDATE activities SET name=?, date=?, description=?, goal_points=? WHERE id=?', (name, date, description, gp, id))
        db.commit()
        flash('Atividade atualizada.')
        return redirect(url_for('activities_list'))
    activity = dict(row)
    return render_template('activities_edit.html', activity=activity)


@app.route('/activities/<int:id>')
def activities_show(id):
    db = get_db()
    cur = db.execute('SELECT * FROM activities WHERE id = ?', (id,))
    row = cur.fetchone()
    if row is None:
        flash('Atividade não encontrada.')
        return redirect(url_for('activities_list'))
    activity = dict(row)
    # also list productions linked to this activity
    cur = db.execute('SELECT id, title, quantity, description, created_at FROM productions WHERE activity_id = ? ORDER BY created_at DESC', (id,))
    prods = cur.fetchall()
    # compute completed points and percent
    cur = db.execute('SELECT IFNULL(SUM(quantity),0) AS completed FROM productions WHERE activity_id = ?', (id,))
    completed = cur.fetchone()['completed']
    goal = activity.get('goal_points') or 0
    percent = None
    if goal and goal > 0:
        percent = min(100, int((completed / goal) * 100))
    return render_template('activities_show.html', activity=activity, productions=prods, completed=completed, percent=percent)


@app.route('/activities/<int:id>/mark_complete', methods=['POST'])
def activities_mark_complete(id):
    db = get_db()
    # Get activity name for message
    cur = db.execute('SELECT name FROM activities WHERE id = ?', (id,))
    activity = cur.fetchone()
    if not activity:
        flash('Atividade não encontrada.')
        return redirect(url_for('activities_list'))
    
    activity_name = activity['name']
    
    # Delete all productions for this activity
    db.execute('DELETE FROM productions WHERE activity_id = ?', (id,))
    # Delete the activity itself
    db.execute('DELETE FROM activities WHERE id = ?', (id,))
    db.commit()
    
    flash(f'Atividade "{activity_name}" concluída e removida do banco, junto com suas produções.')
    return redirect(url_for('activities_list'))


@app.route('/activities/<int:id>/reset_progress', methods=['POST'])
def activities_reset_progress(id):
    db = get_db()
    # delete productions for this activity (reset progress)
    db.execute('DELETE FROM productions WHERE activity_id = ?', (id,))
    db.commit()
    flash('Progresso resetado (produções vinculadas removidas).')
    return redirect(url_for('activities_show', id=id))


@app.route('/activities/<int:id>/delete', methods=['POST'])
def activities_delete(id):
    db = get_db()
    db.execute('DELETE FROM activities WHERE id = ?', (id,))
    db.commit()
    flash('Atividade excluída.')
    return redirect(url_for('activities_list'))


# Edit / Delete for productions
@app.route('/productions/<int:id>/edit', methods=['GET', 'POST'])
def productions_edit(id):
    db = get_db()
    cur = db.execute('SELECT * FROM productions WHERE id = ?', (id,))
    row = cur.fetchone()
    if row is None:
        flash('Produção não encontrada.')
        return redirect(url_for('productions_list'))
    if request.method == 'POST':
        quantity = request.form.get('quantity', '').strip()
        description = request.form.get('description', '').strip()
        activity_id = request.form.get('activity_id', '').strip()
        
        # activity_id is now required
        if not activity_id:
            flash('Atividade é obrigatória.')
            return redirect(url_for('productions_edit', id=id))
        
        try:
            aid = int(activity_id)
        except ValueError:
            flash('Atividade inválida.')
            return redirect(url_for('productions_edit', id=id))
        
        try:
            q = int(quantity) if quantity else None
        except ValueError:
            flash('Quantidade deve ser número inteiro.')
            return redirect(url_for('productions_edit', id=id))
        
        # Get activity name to use as title
        cur = db.execute('SELECT name FROM activities WHERE id = ?', (aid,))
        activity = cur.fetchone()
        if not activity:
            flash('Atividade não encontrada.')
            return redirect(url_for('productions_edit', id=id))
        
        title = activity['name']  # Auto-generate title from activity name
        
        db.execute('UPDATE productions SET title=?, quantity=?, description=?, activity_id=? WHERE id=?', (title, q, description, aid, id))
        db.commit()
        flash('Produção atualizada.')
        return redirect(url_for('productions_list'))
    production = dict(row)
    acts = db.execute('SELECT id, name FROM activities ORDER BY name').fetchall()
    return render_template('productions_edit.html', production=production, activities=acts)


@app.route('/productions/<int:id>/delete', methods=['POST'])
def productions_delete(id):
    db = get_db()
    db.execute('DELETE FROM productions WHERE id = ?', (id,))
    db.commit()
    flash('Produção excluída.')
    return redirect(url_for('productions_list'))


# API JSON endpoints
def row_to_dict(row):
    return dict(row) if row is not None else None


@app.route('/api/activities')
def api_activities():
    db = get_db()
    cur = db.execute('''
        SELECT a.id, a.name, a.date, a.description, a.created_at, a.goal_points, IFNULL(SUM(p.quantity),0) AS completed
        FROM activities a
        LEFT JOIN productions p ON p.activity_id = a.id
        GROUP BY a.id
        ORDER BY a.created_at DESC
    ''')
    rows = []
    for r in cur.fetchall():
        goal = r['goal_points'] if r['goal_points'] is not None else 0
        completed = r['completed'] if r['completed'] is not None else 0
        percent = None
        if goal and goal > 0:
            percent = min(100, int((completed / goal) * 100))
        rows.append({'id': r['id'], 'name': r['name'], 'date': r['date'], 'description': r['description'], 'created_at': r['created_at'], 'goal_points': goal, 'completed': completed, 'percent': percent})
    return jsonify(rows)


@app.route('/api/productions')
def api_productions():
    db = get_db()
    cur = db.execute('''
        SELECT p.*, a.name AS activity_name
        FROM productions p
        LEFT JOIN activities a ON p.activity_id = a.id
        ORDER BY p.created_at DESC
    ''')
    rows = cur.fetchall()
    data = [row_to_dict(r) for r in rows]
    return jsonify(data)


@app.route('/api/activities/<int:id>/goal_points', methods=['POST'])
def api_set_goal_points(id):
    """Set goal_points for an activity via API. Expects JSON: {"goal_points": 50}"""
    db = get_db()
    cur = db.execute('SELECT * FROM activities WHERE id = ?', (id,))
    if cur.fetchone() is None:
        return jsonify({'error': 'Activity not found'}), 404
    
    data = request.get_json()
    if not data or 'goal_points' not in data:
        return jsonify({'error': 'Missing goal_points in JSON body'}), 400
    
    try:
        goal_points = int(data['goal_points'])
        if goal_points < 0:
            return jsonify({'error': 'goal_points must be >= 0'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'goal_points must be an integer'}), 400
    
    db.execute('UPDATE activities SET goal_points = ? WHERE id = ?', (goal_points, id))
    db.commit()
    return jsonify({'success': True, 'goal_points': goal_points}), 200


# CSV export endpoints
def generate_csv(rows, columns):
    import csv
    from io import StringIO
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(columns)
    for r in rows:
        writer.writerow([r.get(c) for c in columns])
    return si.getvalue()


@app.route('/export/activities.csv')
def export_activities_csv():
    db = get_db()
    cur = db.execute('''
        SELECT a.id, a.name, a.date, a.description, a.created_at, a.goal_points, IFNULL(SUM(p.quantity),0) AS completed
        FROM activities a
        LEFT JOIN productions p ON p.activity_id = a.id
        GROUP BY a.id
        ORDER BY a.created_at DESC
    ''')
    rows = []
    for r in cur.fetchall():
        goal = r['goal_points'] if r['goal_points'] is not None else 0
        completed = r['completed'] if r['completed'] is not None else 0
        percent = ''
        if goal and goal > 0:
            percent = str(min(100, int((completed / goal) * 100)))
        rows.append({'id': r['id'], 'name': r['name'], 'date': r['date'], 'description': r['description'], 'created_at': r['created_at'], 'goal_points': goal, 'completed': completed, 'percent': percent})
    columns = ['id', 'name', 'date', 'description', 'goal_points', 'completed', 'percent', 'created_at']
    csv_text = generate_csv(rows, columns)
    return Response(csv_text, mimetype='text/csv', headers={
        'Content-Disposition': 'attachment; filename="activities.csv"'
    })


@app.route('/export/productions.csv')
def export_productions_csv():
    db = get_db()
    cur = db.execute('''
        SELECT p.id, p.title, p.quantity, p.description, p.created_at, p.activity_id, a.name AS activity_name
        FROM productions p
        LEFT JOIN activities a ON p.activity_id = a.id
        ORDER BY p.created_at DESC
    ''')
    rows = [row_to_dict(r) for r in cur.fetchall()]
    columns = ['id', 'title', 'quantity', 'description', 'activity_id', 'activity_name', 'created_at']
    csv_text = generate_csv(rows, columns)
    return Response(csv_text, mimetype='text/csv', headers={
        'Content-Disposition': 'attachment; filename="productions.csv"'
    })


if __name__ == '__main__':
    # ensure DB schema and migrations (adds missing columns)
    init_db()
    # Prefer explicit env vars for production. Run on 0.0.0.0 to allow remote access if desired.
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode, host=os.environ.get('HOST', '0.0.0.0'), port=port)
