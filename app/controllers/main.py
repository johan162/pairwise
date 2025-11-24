from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from app.models.project import Project
import os

bp = Blueprint('main', __name__)

# Global variable to hold the current project state in memory
current_project = None
DATA_DIR = os.path.join(os.getcwd(), 'data')
STATE_FILE = os.path.join(DATA_DIR, 'current_state.json')

@bp.route('/')
def index():
    global current_project
    if current_project is None:
        if os.path.exists(STATE_FILE):
            try:
                current_project = Project.load_state(STATE_FILE)
                flash("Resumed previous session", "info")
            except Exception:
                pass
    return render_template('index.html', project=current_project)

@bp.route('/new', methods=['POST'])
def new_project():
    global current_project
    name = request.form.get('name')
    description = request.form.get('description')
    file = request.files['file']
    
    if file and file.filename and name:
        filename = secure_filename(file.filename)
        filepath = os.path.join(DATA_DIR, filename)
        file.save(filepath)
        current_project = Project(name, description or "", filepath)
        current_project.save_state(STATE_FILE)
        return redirect(url_for('main.compare'))
    
    return redirect(url_for('main.index'))

@bp.route('/compare')
def compare():
    global current_project
    project = current_project
    if project is None:
        return redirect(url_for('main.index'))
        
    engine = project.get_current_engine()
    if engine is None:
        return redirect(url_for('main.index'))

    pair = engine.get_next_pair()
    
    if not pair:
        flash("Ranking complete for this dimension!", "success")
        return redirect(url_for('main.results'))
        
    task1 = next(t for t in project.tasks if t['id'] == pair[0])
    task2 = next(t for t in project.tasks if t['id'] == pair[1])
    
    progress = engine.get_progress()
    tau = engine.get_kendall_tau()
    inconsistency = engine.get_inconsistency_level()
    
    return render_template('compare.html', 
                           task1=task1, 
                           task2=task2, 
                           progress=progress, 
                           tau=tau,
                           inconsistency=inconsistency,
                           dimension=project.current_dimension)

@bp.route('/vote', methods=['POST'])
def vote():
    global current_project
    project = current_project
    if project is None:
        return redirect(url_for('main.index'))
        
    winner_id = request.form.get('winner')
    loser_id = request.form.get('loser')
    
    engine = project.get_current_engine()
    if engine is None:
        return redirect(url_for('main.index'))

    if winner_id and loser_id:
        engine.update(winner_id, loser_id)
        project.save_state(STATE_FILE)
    
    return redirect(url_for('main.compare'))

@bp.route('/results')
def results():
    global current_project
    project = current_project
    if project is None:
        return redirect(url_for('main.index'))
        
    if project.complexity_engine is None or project.value_engine is None:
        return redirect(url_for('main.index'))

    # Get rankings for both dimensions
    complexity_ranking = project.complexity_engine.get_ranking()
    value_ranking = project.value_engine.get_ranking()
    
    # Create a combined data structure
    results = []
    for task in project.tasks:
        tid = task['id']
        c_rank = complexity_ranking.index(tid) + 1
        v_rank = value_ranking.index(tid) + 1
        c_score = project.complexity_engine.mu[tid]
        v_score = project.value_engine.mu[tid]
        
        results.append({
            'id': tid,
            'description': task['description'],
            'complexity_rank': c_rank,
            'value_rank': v_rank,
            'complexity_score': c_score,
            'value_score': v_score
        })
        
    return render_template('results.html', results=results, project=project)

@bp.route('/switch_dimension/<dimension>')
def switch_dimension(dimension):
    global current_project
    project = current_project
    if project and dimension in ['complexity', 'value']:
        project.current_dimension = dimension
        project.save_state(STATE_FILE)
    return redirect(url_for('main.compare'))

@bp.route('/reset')
def reset():
    global current_project
    current_project = None
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    return redirect(url_for('main.index'))
