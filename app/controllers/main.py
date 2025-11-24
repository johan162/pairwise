from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from app.models.project import Project
import os

bp = Blueprint('main', __name__)

# Global variable to hold the current project state in memory
current_project = None
DATA_DIR = os.path.join(os.getcwd(), 'data')
STATE_FILE = os.path.join(DATA_DIR, 'current_state.json')
DIMENSION_LABELS = {
    'complexity': 'Technical Complexity',
    'value': 'Business Value'
}

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

    dimension_status = None
    if current_project:
        dimension_status = {
            dimension: current_project.get_dimension_summary(dimension)
            for dimension in Project.DIMENSIONS
        }

    return render_template(
        'index.html',
        project=current_project,
        dimension_status=dimension_status,
        dimension_labels=DIMENSION_LABELS,
    )

@bp.route('/new', methods=['POST'])
def new_project():
    global current_project
    name = request.form.get('name')
    description = request.form.get('description')
    file = request.files['file']
    
    if file and file.filename and name:
        os.makedirs(DATA_DIR, exist_ok=True)
        filename = secure_filename(file.filename)
        filepath = os.path.join(DATA_DIR, filename)
        file.save(filepath)
        current_project = Project(name, description or "", filepath)
        current_project.save_state(STATE_FILE)
        flash("Project created. Choose a dimension to begin comparisons.", "success")
        return redirect(url_for('main.index'))
    
    flash("Please provide a project name and CSV file.", "warning")
    return redirect(url_for('main.index'))

@bp.route('/compare')
def compare():
    global current_project
    project = current_project
    if project is None:
        return redirect(url_for('main.index'))
        
    engine = project.get_current_engine()
    if engine is None:
        flash("Select a dimension to start comparing tasks.", "info")
        return redirect(url_for('main.index'))

    if engine.is_complete():
        return _handle_dimension_completion(project)

    pair = engine.get_next_pair()
    
    if not pair:
        return _handle_dimension_completion(project)
        
    task1 = next(t for t in project.tasks if t['id'] == pair[0])
    task2 = next(t for t in project.tasks if t['id'] == pair[1])
    
    progress = engine.get_progress()
    tau = engine.get_kendall_tau()
    inconsistency = engine.get_inconsistency_level()
    
    return render_template(
        'compare.html',
        task1=task1,
        task2=task2,
        progress=progress,
        tau=tau,
        inconsistency=inconsistency,
        dimension=project.current_dimension,
        dimension_label=DIMENSION_LABELS.get(project.current_dimension, project.current_dimension.title()),
    )

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
    
    dimension_status = {
        dimension: project.get_dimension_summary(dimension)
        for dimension in Project.DIMENSIONS
    }

    pending_dimension = request.args.get('pending')
    if pending_dimension not in Project.DIMENSIONS:
        pending_dimension = None
    elif project.is_dimension_complete(pending_dimension):
        pending_dimension = None
    
    return render_template(
        'results.html',
        results=results,
        project=project,
        dimension_status=dimension_status,
        pending_dimension=pending_dimension,
        dimension_labels=DIMENSION_LABELS,
    )


def _handle_dimension_completion(project: Project):
    completed_dimension = project.current_dimension
    alternate_dimension = project.get_other_dimension(completed_dimension)
    alternate_engine = project.get_engine_for_dimension(alternate_dimension)

    if alternate_engine and not alternate_engine.is_complete():
        flash(
            f"{DIMENSION_LABELS.get(completed_dimension, completed_dimension.title())} ranking complete. Continue {DIMENSION_LABELS.get(alternate_dimension, alternate_dimension.title())} next.",
            "info",
        )
        return redirect(url_for('main.results', pending=alternate_dimension))

    flash("All comparisons are complete. Review the final rankings.", "success")
    return redirect(url_for('main.results'))

@bp.route('/switch_dimension/<dimension>')
def switch_dimension(dimension):
    global current_project
    project = current_project
    if project and dimension in Project.DIMENSIONS:
        project.current_dimension = dimension
        project.save_state(STATE_FILE)

    target = request.args.get('target', 'compare')
    allowed_targets = {'compare', 'index', 'results'}
    if target not in allowed_targets:
        target = 'compare'

    return redirect(url_for(f'main.{target}'))

@bp.route('/reset')
def reset():
    global current_project
    current_project = None
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    return redirect(url_for('main.index'))
