import json
import os
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any

import pandas as pd

from .ranking import RankingEngine

class Project:
    DIMENSIONS = ('complexity', 'value')

    def __init__(self, name: str, description: str, tasks_file: Optional[str] = None, state_file: Optional[str] = None, created_at: Optional[str] = None):
        self.name = name
        self.description = description
        self.tasks_file = tasks_file
        self.state_file = state_file
        self.tasks: List[Dict[str, Any]] = []
        self.complexity_engine: Optional[RankingEngine] = None
        self.value_engine: Optional[RankingEngine] = None
        self.current_dimension = 'complexity' # or 'value'
        self.created_at = created_at if created_at else datetime.now().isoformat()
        
        if tasks_file:
            self.load_tasks(tasks_file)

    def load_tasks(self, filepath: str):
        df = pd.read_csv(filepath)
        normalized_cols = {col.strip().lower(): col for col in df.columns}
        if 'id' in normalized_cols and 'description' in normalized_cols:
            df = df.rename(columns={
                normalized_cols['id']: 'id',
                normalized_cols['description']: 'description'
            })
        else:
            # Fallback for CSV files without headers (or with unexpected labels)
            df = pd.read_csv(filepath, header=None, names=['id', 'description'], usecols=[0, 1])

        df['id'] = df['id'].astype(str).str.strip()
        df['description'] = df['description'].astype(str).str.strip()
        df = df[df['id'] != '']
        df = df[df['description'] != '']

        self.tasks = df.to_dict('records') # type: ignore
        if not self.tasks:
            raise ValueError(f"No tasks found in CSV file: {filepath}")

        task_ids = [str(t['id']) for t in self.tasks]
        self.complexity_engine = RankingEngine(task_ids)
        self.value_engine = RankingEngine(task_ids)

    def get_engine_for_dimension(self, dimension: str) -> Optional[RankingEngine]:
        if dimension == 'value':
            return self.value_engine
        return self.complexity_engine

    def get_current_engine(self) -> Optional[RankingEngine]:
        return self.get_engine_for_dimension(self.current_dimension)

    def get_other_dimension(self, dimension: str) -> str:
        return 'value' if dimension == 'complexity' else 'complexity'

    def get_dimension_summary(self, dimension: str) -> Dict[str, Any]:
        engine = self.get_engine_for_dimension(dimension)
        if engine is None:
            return {
                'progress': 0.0,
                'complete': False,
                'comparisons': 0,
                'total': 0
            }

        total = engine.total_comparisons()
        return {
            'progress': engine.get_progress(),
            'complete': engine.is_complete(),
            'comparisons': len(engine.comparisons),
            'total': total
        }

    def get_pending_dimensions(self) -> List[str]:
        pending = []
        for dimension in self.DIMENSIONS:
            engine = self.get_engine_for_dimension(dimension)
            if engine and not engine.is_complete():
                pending.append(dimension)
        return pending

    def all_dimensions_complete(self) -> bool:
        return len(self.get_pending_dimensions()) == 0

    def is_dimension_complete(self, dimension: str) -> bool:
        engine = self.get_engine_for_dimension(dimension)
        return bool(engine and engine.is_complete())

    def save_state(self, filepath: str = None):
        if filepath is None:
            filepath = self.state_file
        if filepath is None:
            raise ValueError("No filepath provided for saving state")
            
        complexity_engine = self.complexity_engine
        value_engine = self.value_engine

        if complexity_engine is None or value_engine is None:
            return

        state = {
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'tasks': self.tasks,
            'current_dimension': self.current_dimension,
            'complexity_state': {
                'mu': complexity_engine.mu,
                'sigma': complexity_engine.sigma,
                'comparisons': complexity_engine.comparisons
            },
            'value_state': {
                'mu': value_engine.mu,
                'sigma': value_engine.sigma,
                'comparisons': value_engine.comparisons
            }
        }
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=4)

    @classmethod
    def load_state(cls, filepath: str):
        with open(filepath, 'r') as f:
            state = json.load(f)
            
        project = cls(state['name'], state['description'], state_file=filepath)
        if 'created_at' in state:
            project.created_at = state['created_at']
        project.tasks = state['tasks']
        project.current_dimension = state.get('current_dimension', 'complexity')
        
        task_ids = [str(t['id']) for t in project.tasks]
        
        project.complexity_engine = RankingEngine(task_ids)
        if project.complexity_engine:
            project.complexity_engine.mu = state['complexity_state']['mu']
            project.complexity_engine.sigma = state['complexity_state']['sigma']
            project.complexity_engine.comparisons = state['complexity_state']['comparisons']
        
        project.value_engine = RankingEngine(task_ids)
        if project.value_engine:
            project.value_engine.mu = state['value_state']['mu']
            project.value_engine.sigma = state['value_state']['sigma']
            project.value_engine.comparisons = state['value_state']['comparisons']
        
        return project

    def save_to_db(self, db_path: str):
        complexity_engine = self.complexity_engine
        value_engine = self.value_engine

        if complexity_engine is None or value_engine is None:
            return

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS projects
                     (name text, description text, created_at text, data json)''')
        
        # Serialize full state to JSON for storage
        # In a real app, we might normalize this into tables (Tasks, Comparisons, etc.)
        # But for R36 "persisted on disk in a SQLite DB", storing the JSON blob is a valid simple approach
        # or we can make it more relational. Given the requirements, a JSON blob in SQLite is flexible.
        
        state_json = json.dumps({
            'tasks': self.tasks,
            'complexity_state': {
                'mu': complexity_engine.mu,
                'sigma': complexity_engine.sigma,
                'comparisons': complexity_engine.comparisons
            },
            'value_state': {
                'mu': value_engine.mu,
                'sigma': value_engine.sigma,
                'comparisons': value_engine.comparisons
            }
        })
        
        c.execute("INSERT OR REPLACE INTO projects (name, description, created_at, data) VALUES (?, ?, ?, ?)",
                  (self.name, self.description, self.created_at, state_json))
        conn.commit()
        conn.close()
