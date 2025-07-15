import sys
import os
import tempfile
import json
import shutil
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from epub_extractor.context_manager import TranslationContextManager

def test_context_save_and_load():
    with tempfile.TemporaryDirectory() as tmp_dir:
        manager = TranslationContextManager('테스트책', tmp_dir)
        # context 저장
        manager.context['characters']['Raistlin'] = {
            'original': 'Raistlin', 'korean': '라이스틸', 'description': '마법사'
        }
        manager.save_context()
        # 새 인스턴스에서 로드
        manager2 = TranslationContextManager('테스트책', tmp_dir)
        assert 'Raistlin' in manager2.context['characters']
        assert manager2.context['characters']['Raistlin']['korean'] == '라이스틸'

def test_update_context():
    with tempfile.TemporaryDirectory() as tmp_dir:
        manager = TranslationContextManager('테스트책', tmp_dir)
        analysis_result = {
            'characters': [
                {'name': 'Raistlin', 'description': '마법사'}
            ],
            'places': [
                {'name': 'Shoikan Grove', 'description': '숲'}
            ],
            'terms': [
                {'name': 'Soulforge', 'category': '마법', 'description': '마법 도구'}
            ],
            'relationships': [
                {'character1': 'Raistlin', 'character2': 'Caramon', 'relationship': '형제'}
            ]
        }
        manager.update_context(analysis_result)
        assert 'Raistlin' in manager.context['characters']
        assert 'Shoikan Grove' in manager.context['places']
        assert 'Soulforge' in manager.context['terms']
        assert {'character1': 'Raistlin', 'character2': 'Caramon', 'relationship': '형제'} in manager.context['relationships']
        # 저장 후 재로드
        manager.save_context()
        manager2 = TranslationContextManager('테스트책', tmp_dir)
        assert 'Raistlin' in manager2.context['characters'] 