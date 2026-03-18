from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import main
from ..models import db, Competency, Module, Progress, User
from ..utils import get_learning_objective


role_display_names = {
    "ai_specialist": "HPC AI Specialist",
    "comp_chem_specialist": "HPC Computational Chemistry Specialist"
}

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main.route('/role_select', methods=['GET', 'POST'])
@login_required
def role_select():
    if request.method == 'POST':
        role = request.form['role']
        if role in ['ai_specialist', 'comp_chem_specialist']:
            current_user.role = role
            db.session.commit()
            return redirect(url_for('main.dashboard'))
        else:
            flash("Invalid role selected.", "danger")
    return render_template('main/role_select.html', role_display_names=role_display_names)

# Map each role to its allowed competencies and modules
ROLE_COMPETENCY_MAP = {
    "ai_specialist": ["A", "B", "C", "D"],  # e.g., only these keys for AI path
    "comp_chem_specialist": ["A", "B", "C", "D"],  # customize as needed
}

ROLE_MODULE_KEYS = {
    "ai_specialist": [
        "A1", "A2",
        "B1", "B2", "B3", "B4", "B5", "B6",
        "C1", "D1", "D2", "D3", 
    ],
    "comp_chem_specialist": [
        "A1", "A2",
        "B1", "B3", "B4", "B5", "B6",
        "C1", "D1", "D2", "D3", 
    ],
}

def get_user_modules(user):
    # Only include modules relevant to the user's role
    allowed_keys = set(ROLE_MODULE_KEYS.get(user.role, []))
    competencies = Competency.query.all()
    data = []
    for comp in competencies:
        # Only include competency if it has at least one relevant module
        modules = Module.query.filter(
            Module.competency_id == comp.id,
            Module.key.in_(allowed_keys)
        ).order_by(Module.order).all()
        if not modules:
            continue
        mod_data = []
        for m in modules:
            prog = Progress.query.filter_by(user_id=user.id, module_id=m.id).first()
            status = prog.status if prog else 'incomplete'
            if prog and prog.learning_level:
                learning_level = prog.learning_level
            else:
                learning_level = get_learning_objective(
                    user.role, m.key, user.current_level
                )
            quiz_passed = prog.quiz_passed if prog else False
            mod_data.append({
                "id": m.id,
                "key": m.key,
                "name": m.name,
                "status": status,
                "quiz_passed": quiz_passed,
                "learning_level": learning_level,
            })
        data.append({
            "competency": comp,
            "modules": mod_data
        })
    return data


# def get_user_modules(user):
#     # Get modules, progress for user, grouped by competency
#     competencies = Competency.query.all()
#     data = []
#     for comp in competencies:
#         modules = Module.query.filter_by(competency_id=comp.id).order_by(Module.order).all()
#         mod_data = []
#         for m in modules:
#             prog = Progress.query.filter_by(user_id=user.id, module_id=m.id).first()
#             status = prog.status if prog else 'incomplete'
            
#             if prog and prog.learning_level:
#                 learning_level = prog.learning_level
#             else:
#                 # Compute learning_level for this user/module based on their role and current_level
#                 learning_level = get_learning_objective(
#                     user.role, m.key, user.current_level
#                 )
            
#             quiz_passed = prog.quiz_passed if prog else False
#             mod_data.append({
#                 "id": m.id,
#                 "key": m.key,
#                 "name": m.name,
#                 "status": status,
#                 "quiz_passed": quiz_passed,
#                 "learning_level": learning_level,
#             })
#         data.append({
#             "competency": comp,
#             "modules": mod_data
#         })
#     return data

@main.route('/dashboard')
@login_required
def dashboard():
    
    modules_data = get_user_modules(current_user)
    # Progress calculation
    total_modules = sum(len(c["modules"]) for c in modules_data)
    completed_modules = sum(1 for c in modules_data for m in c["modules"] if m["status"] == "completed")
    percent_complete = int((completed_modules / total_modules) * 100) if total_modules else 0

    # Current role and level
    role_name = role_display_names.get(current_user.role, current_user.role)
    current_level = current_user.current_level
    active_sessions = 2  # placeholder

    return render_template(
        'main/dashboard.html',
        modules_data=modules_data,
        completed_modules=completed_modules,
        total_modules=total_modules,
        percent_complete=percent_complete,
        role_name=role_name,
        current_level=current_level,
        active_sessions=active_sessions
    )

@main.route('/module/<int:module_id>')
@login_required
def module(module_id):
    module = Module.query.get_or_404(module_id)
    progress = Progress.query.filter_by(user_id=current_user.id, module_id=module.id).first()
    # Determine current learning_level for the user/role/module (from mapping)
    if not progress:
        progress = Progress(user_id=current_user.id, module_id=module.id, status='incomplete', quiz_passed=False, learning_level='remember')
        db.session.add(progress)
        db.session.commit()
    return render_template(
        'main/module.html',
        module=module,
        progress=progress,
    )

@main.route('/mark_complete/<int:module_id>', methods=['POST'])
@login_required
def mark_complete(module_id):
    progress = Progress.query.filter_by(user_id=current_user.id, module_id=module_id).first()
    if progress and progress.quiz_passed:
        progress.status = "completed"
        db.session.commit()
        return '', 204
    return '', 400



