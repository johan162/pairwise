import pytest
from app.models.ranking import RankingEngine

def test_ranking_initialization():
    items = ['A', 'B', 'C']
    engine = RankingEngine(items)
    assert len(engine.mu) == 3
    assert engine.mu['A'] == 25.0
    assert engine.sigma['A'] == 8.333

def test_ranking_update():
    items = ['A', 'B']
    engine = RankingEngine(items)
    
    # A wins against B
    engine.update('A', 'B')
    
    assert engine.mu['A'] > 25.0
    assert engine.mu['B'] < 25.0
    assert engine.sigma['A'] < 8.333
    assert engine.sigma['B'] < 8.333

def test_get_next_pair():
    items = ['A', 'B', 'C']
    engine = RankingEngine(items)
    
    pair = engine.get_next_pair()
    assert pair is not None
    assert len(pair) == 2
    assert pair[0] in items
    assert pair[1] in items
    assert pair[0] != pair[1]

def test_ranking_order():
    items = ['A', 'B']
    engine = RankingEngine(items)
    engine.update('A', 'B')
    
    ranking = engine.get_ranking()
    assert ranking[0] == 'A'
    assert ranking[1] == 'B'
