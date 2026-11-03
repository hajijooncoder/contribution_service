"""
Static, versioned read-only projection of canonical legal references.
This provides reference codes and authorities to contributors and reviewers
WITHOUT providing any direct or live access to the internal Neo4j Knowledge Graph.
"""

from typing import List, Dict

LEGAL_AUTHORITIES: List[Dict[str, str]] = [
    {"id": "auth-parliament", "name": "مجلس شورای اسلامی", "type": "legislative"},
    {"id": "auth-expediency", "name": "مجمع تشخیص مصلحت نظام", "type": "legislative_oversight"},
    {"id": "auth-cabinet", "name": "هیأت وزیران", "type": "executive"},
    {"id": "auth-supreme-court", "name": "دیوان عالی کشور", "type": "judicial"},
    {"id": "auth-admin-court", "name": "دیوان عدالت اداری", "type": "judicial_administrative"},
    {"id": "auth-guardian-council", "name": "شورای نگهبان", "type": "constitutional"},
    {"id": "auth-judiciary-chief", "name": "ریاست قوه قضائیه", "type": "judicial_regulatory"},
]

CANONICAL_LAW_CODES: List[Dict[str, str]] = [
    {"code_id": "CIVIL_CODE", "title": "قانون مدنی", "year": "1307", "authority": "مجلس شورای اسلامی"},
    {"code_id": "PENAL_CODE", "title": "قانون مجازات اسلامی", "year": "1392", "authority": "مجلس شورای اسلامی"},
    {"code_id": "CIVIL_PROCEDURE", "title": "قانون آیین دادرسی دادگاه‌های عمومی و انقلاب در امور مدنی", "year": "1379", "authority": "مجلس شورای اسلامی"},
    {"code_id": "CRIMINAL_PROCEDURE", "title": "قانون آیین دادرسی کیفری", "year": "1392", "authority": "مجلس شورای اسلامی"},
    {"code_id": "COMMERCIAL_CODE", "title": "قانون تجارت", "year": "1311", "authority": "مجلس شورای اسلامی"},
    {"code_id": "LABOR_CODE", "title": "قانون کار", "year": "1369", "authority": "مجمع تشخیص مصلحت نظام"},
    {"code_id": "ADMIN_COURT_ACT", "title": "قانون تشکیلات و آیین دادرسی دیوان عدالت اداری", "year": "1392", "authority": "مجلس شورای اسلامی"},
]

def get_legal_authorities() -> List[Dict[str, str]]:
    return LEGAL_AUTHORITIES

def get_canonical_law_codes() -> List[Dict[str, str]]:
    return CANONICAL_LAW_CODES
