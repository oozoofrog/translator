#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
번역 컨텍스트 매니저

각 EPUB의 고유명사, 인물관계, 설정을 자동으로 추출하고 
번역 과정에서 일관성을 유지하도록 도와주는 시스템
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Set
import hashlib

class TranslationContextManager:
    """번역 컨텍스트 관리 클래스"""
    
    def __init__(self, book_title: str, work_dir: str):
        """
        Args:
            book_title: 책 제목
            work_dir: 작업 디렉토리
        """
        self.book_title = book_title
        self.work_dir = Path(work_dir)
        self.context_file = self.work_dir / "translation_context.json"
        
        # 컨텍스트 데이터
        self.context = {
            "book_info": {
                "title": book_title,
                "analyzed_chunks": 0,
                "last_updated": None
            },
            "characters": {},      # 인물명: {"original": "", "korean": "", "description": ""}
            "places": {},          # 지명: {"original": "", "korean": "", "description": ""}
            "terms": {},           # 용어: {"original": "", "korean": "", "category": ""}
            "relationships": [],   # 인물관계: {"character1": "", "character2": "", "relationship": ""}
            "world_setting": {},   # 세계관: {"aspect": "", "description": ""}
            "translation_rules": [] # 특별 번역 규칙
        }
        
        # 기존 컨텍스트 로드
        self.load_context()
    
    def load_context(self):
        """기존 컨텍스트 파일 로드"""
        if self.context_file.exists():
            try:
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    saved_context = json.load(f)
                    self.context.update(saved_context)
                print(f"✅ 기존 번역 컨텍스트 로드: {len(self.context['characters'])}명 인물, {len(self.context['places'])}개 지명")
            except Exception as e:
                print(f"⚠️  컨텍스트 로드 실패: {e}")
    
    def save_context(self):
        """컨텍스트를 파일에 저장"""
        try:
            self.work_dir.mkdir(parents=True, exist_ok=True)
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(self.context, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  컨텍스트 저장 실패: {e}")
    
    def analyze_text_for_context(self, text: str, translator) -> Dict:
        """텍스트에서 고유명사와 설정 추출"""
        try:
            analysis_prompt = f"""다음 텍스트를 분석하여 소설의 컨텍스트 정보를 JSON 형태로 추출해주세요.

텍스트:
{text[:1500]}

다음 형식으로 응답해주세요:
{{
  "characters": [
    {{"name": "인물명", "description": "간단한 설명"}}
  ],
  "places": [
    {{"name": "지명", "description": "간단한 설명"}}
  ],
  "terms": [
    {{"name": "특수용어", "category": "마법/종족/기술 등", "description": "설명"}}
  ],
  "relationships": [
    {{"character1": "인물1", "character2": "인물2", "relationship": "관계"}}
  ]
}}

고유명사와 중요한 설정만 추출하고, JSON 형식을 정확히 지켜주세요."""

            response = translator.client.chat(
                model=translator.model_name,
                messages=[{"role": "user", "content": analysis_prompt}],
                options={
                    "temperature": 0.1,
                    "top_p": 0.8
                }
            )
            
            result_text = response['message']['content'].strip()
            
            # JSON 추출 시도
            try:
                # ```json 블록이 있으면 추출
                if "```json" in result_text:
                    start = result_text.find("```json") + 7
                    end = result_text.find("```", start)
                    result_text = result_text[start:end].strip()
                elif "```" in result_text:
                    start = result_text.find("```") + 3
                    end = result_text.find("```", start)
                    result_text = result_text[start:end].strip()
                
                analysis_result = json.loads(result_text)
                return analysis_result
                
            except json.JSONDecodeError:
                print("⚠️  컨텍스트 분석 결과를 JSON으로 파싱할 수 없음")
                return {}
                
        except Exception as e:
            print(f"⚠️  컨텍스트 분석 실패: {e}")
            return {}
    
    def update_context(self, analysis_result: Dict):
        """분석 결과로 컨텍스트 업데이트"""
        # 인물 추가
        for char in analysis_result.get('characters', []):
            name = char.get('name', '').strip()
            if name and name not in self.context['characters']:
                self.context['characters'][name] = {
                    "original": name,
                    "korean": "",  # 번역은 나중에
                    "description": char.get('description', '')
                }
        
        # 지명 추가
        for place in analysis_result.get('places', []):
            name = place.get('name', '').strip()
            if name and name not in self.context['places']:
                self.context['places'][name] = {
                    "original": name,
                    "korean": "",
                    "description": place.get('description', '')
                }
        
        # 용어 추가
        for term in analysis_result.get('terms', []):
            name = term.get('name', '').strip()
            if name and name not in self.context['terms']:
                self.context['terms'][name] = {
                    "original": name,
                    "korean": "",
                    "category": term.get('category', ''),
                    "description": term.get('description', '')
                }
        
        # 관계 추가
        for rel in analysis_result.get('relationships', []):
            if rel not in self.context['relationships']:
                self.context['relationships'].append(rel)
        
        # 분석된 청크 수 증가
        self.context['book_info']['analyzed_chunks'] += 1
        
        # 저장
        self.save_context()
    
    def get_context_for_translation(self) -> str:
        """번역에 사용할 컨텍스트 정보 생성"""
        context_text = ""
        
        # 주요 인물
        if self.context['characters']:
            context_text += "\n🎭 주요 인물:\n"
            for name, info in list(self.context['characters'].items())[:10]:  # 상위 10명만
                korean = info.get('korean', '')
                if korean:
                    context_text += f"- {name} → {korean}\n"
                else:
                    context_text += f"- {name} (번역 필요)\n"
        
        # 주요 지명
        if self.context['places']:
            context_text += "\n🌍 주요 지명:\n"
            for name, info in list(self.context['places'].items())[:5]:  # 상위 5개만
                korean = info.get('korean', '')
                if korean:
                    context_text += f"- {name} → {korean}\n"
                else:
                    context_text += f"- {name} (번역 필요)\n"
        
        # 특수 용어
        if self.context['terms']:
            context_text += "\n⚔️ 특수 용어:\n"
            for name, info in list(self.context['terms'].items())[:5]:  # 상위 5개만
                korean = info.get('korean', '')
                category = info.get('category', '')
                if korean:
                    context_text += f"- {name} → {korean} ({category})\n"
                else:
                    context_text += f"- {name} ({category})\n"
        
        return context_text.strip()
    
    def suggest_translations(self, text: str) -> Dict[str, str]:
        """텍스트에서 발견된 고유명사의 번역 제안"""
        suggestions = {}
        
        # 기존 번역된 용어들 검색
        for category in ['characters', 'places', 'terms']:
            for original, info in self.context[category].items():
                if original in text and info.get('korean'):
                    suggestions[original] = info['korean']
        
        return suggestions
    
    def apply_context_corrections(self, original_text: str, translated_text: str) -> str:
        """번역 결과에 컨텍스트 정보를 적용하여 일관성 개선"""
        corrected_text = translated_text
        
        # 고유명사 일관성 적용
        for category in ['characters', 'places', 'terms']:
            for original, info in self.context[category].items():
                korean = info.get('korean', '').strip()
                if korean and original in original_text:
                    # 원문에 있는 고유명사가 번역문에서도 일관되게 사용되도록
                    import re
                    # 단어 경계를 고려한 치환
                    pattern = r'\b' + re.escape(original) + r'\b'
                    if re.search(pattern, original_text):
                        corrected_text = re.sub(pattern, korean, corrected_text)
        
        return corrected_text
    
    def update_translation_from_user(self, original: str, korean: str, category: str = "terms"):
        """사용자가 수정한 번역을 컨텍스트에 반영"""
        if category in ['characters', 'places', 'terms']:
            if original not in self.context[category]:
                self.context[category][original] = {
                    "original": original,
                    "korean": "",
                    "description": ""
                }
            
            self.context[category][original]['korean'] = korean
            self.save_context()
            print(f"✅ 번역 업데이트: {original} → {korean}")
    
    def get_untranslated_terms(self) -> Dict[str, List[str]]:
        """아직 번역되지 않은 용어들 목록 반환"""
        untranslated = {
            "characters": [],
            "places": [],
            "terms": []
        }
        
        for category in ['characters', 'places', 'terms']:
            for original, info in self.context[category].items():
                if not info.get('korean', '').strip():
                    untranslated[category].append(original)
        
        return untranslated
    
    def review_and_update_context(self, chunk_file: str = None):
        """컨텍스트 검토 및 업데이트 인터페이스"""
        print("\n" + "="*50)
        print("📋 번역 컨텍스트 검토 및 업데이트")
        print("="*50)
        
        # 미번역 용어 표시
        untranslated = self.get_untranslated_terms()
        total_untranslated = sum(len(terms) for terms in untranslated.values())
        
        if total_untranslated == 0:
            print("✅ 모든 용어가 번역되었습니다.")
            return
        
        print(f"\n📊 미번역 용어: {total_untranslated}개")
        
        for category, terms in untranslated.items():
            if terms:
                category_name = {"characters": "인물", "places": "지명", "terms": "용어"}[category]
                print(f"\n🔸 {category_name} ({len(terms)}개):")
                for i, term in enumerate(terms[:10], 1):  # 최대 10개만 표시
                    desc = self.context[category][term].get('description', '')
                    desc_text = f" - {desc}" if desc else ""
                    print(f"  {i}. {term}{desc_text}")
                
                if len(terms) > 10:
                    print(f"  ... 외 {len(terms) - 10}개")
        
        print(f"\n💡 컨텍스트 파일 위치: {self.context_file}")
        print("   이 파일을 직접 편집하여 번역을 추가할 수 있습니다.")
        
    def retranslate_with_context(self, original_text: str, translator) -> str:
        """컨텍스트 정보를 반영하여 재번역"""
        context_info = self.get_context_for_translation()
        
        if not context_info:
            print("⚠️  적용할 컨텍스트 정보가 없습니다.")
            return translator.translate_text(original_text)
        
        # 컨텍스트 정보를 포함한 번역
        enhanced_text = f"""=== 번역 컨텍스트 정보 ==={context_info}

=== 원본 텍스트 ===
{original_text}"""
        
        translated = translator.translate_text(enhanced_text)
        
        # 컨텍스트 정보를 적용한 후처리
        corrected = self.apply_context_corrections(original_text, translated)
        
        return corrected