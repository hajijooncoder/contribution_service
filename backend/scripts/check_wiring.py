#!/usr/bin/env python3
"""
Wiring Audit Script for Contribution Service
Checks if all components are properly connected
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def check_imports():
    """Check if all core modules can be imported"""
    print("=" * 60)
    print("WIRING AUDIT: Contribution Service")
    print("=" * 60)
    
    results = {
        'passed': [],
        'failed': []
    }
    
    # Test 1: Core Module Imports
    print("\n[1] Core Module Imports:")
    print("-" * 60)
    
    tests = [
        ('text_enhancement', 'app.core.text_enhancement', 'LegalTextEnhancer'),
        ('duplicate_detector', 'app.core.duplicate_detector', 'SmartDuplicateDetector'),
        ('audit_ledger', 'app.core.audit_ledger', 'CryptographicAuditLedger'),
        ('fsm_quorum', 'app.core.fsm_quorum', 'QuorumReviewFSM'),
        ('scoring_engine', 'app.core.scoring_engine', 'calculate_submission_quality_score'),
        ('source_validator', 'app.core.source_validator', 'validate_official_legal_source_url'),
    ]
    
    for name, module, obj in tests:
        try:
            mod = __import__(module, fromlist=[obj])
            getattr(mod, obj)
            print(f"  ✅ {name}.{obj}")
            results['passed'].append(f"core.{name}")
        except ImportError as e:
            print(f"  ❌ {name}: ImportError - {e}")
            results['failed'].append(f"core.{name}")
        except AttributeError as e:
            print(f"  ❌ {name}: AttributeError - {e}")
            results['failed'].append(f"core.{name}")
    
    # Test 2: Database Models
    print("\n[2] Database Models:")
    print("-" * 60)
    
    try:
        from app.db.models import Submission, User, Review
        print("  ✅ Models imported")
        
        # Check new fields on Submission
        required_fields = [
            'content_hash',
            'content_fingerprint',
            'auto_extracted_metadata',
            'enhancement_changes',
            'text_quality_score',
            'detected_risk_level'
        ]
        
        # Get actual columns
        from sqlalchemy import inspect
        mapper = inspect(Submission)
        actual_columns = [col.key for col in mapper.columns]
        
        for field in required_fields:
            if field in actual_columns:
                print(f"    ✅ Submission.{field}")
                results['passed'].append(f"model.{field}")
            else:
                print(f"    ❌ Submission.{field} MISSING")
                results['failed'].append(f"model.{field}")
        
    except Exception as e:
        print(f"  ❌ Models: {e}")
        results['failed'].append('models')
    
    # Test 3: Schemas
    print("\n[3] API Schemas:")
    print("-" * 60)
    
    schema_tests = [
        ('EnhancedSubmissionRequest', 'app.schemas.submission'),
        ('EnhancedSubmissionResponse', 'app.schemas.submission'),
        ('EnhancedTextPreview', 'app.schemas.submission'),
        ('DuplicateCheckResult', 'app.schemas.submission'),
        ('TextChangeSchema', 'app.schemas.submission'),
        ('ExtractedMetadataSchema', 'app.schemas.submission'),
    ]
    
    for schema, module in schema_tests:
        try:
            mod = __import__(module, fromlist=[schema])
            getattr(mod, schema)
            print(f"  ✅ {schema}")
            results['passed'].append(f"schema.{schema}")
        except Exception as e:
            print(f"  ❌ {schema}: {e}")
            results['failed'].append(f"schema.{schema}")
    
    # Test 4: API Router
    print("\n[4] API Router Endpoints:")
    print("-" * 60)
    
    try:
        from app.api.v1 import contribution
        router = contribution.router

        # Collect all route paths from the router (routes have prefix stripped)
        routes = {}
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                path = route.path
                methods = list(route.methods) if route.methods else []
                routes[path] = methods

        print(f"  Total routes: {len(routes)}")
        print(f"  Registered paths: {sorted(routes.keys())}")

        # Routes are stored with full prefix (e.g. /contribution/upload)
        # because APIRouter prefix="/contribution" is baked into route.path
        critical_endpoints = [
            ('/contribution/upload', ['POST']),
            ('/contribution/submit', ['POST']),
            ('/contribution/submit/enhanced', ['POST']),
            ('/contribution/stats', ['GET']),
            ('/contribution/history', ['GET']),
        ]

        for path, expected_methods in critical_endpoints:
            if path in routes:
                actual_methods = routes[path]
                if set(expected_methods).issubset(set(actual_methods)):
                    print(f"  ✅ {path} {expected_methods}")
                    results['passed'].append(f"route{path}")
                else:
                    print(f"  ⚠️  {path} has {actual_methods}, expected {expected_methods}")
                    results['failed'].append(f"route{path}")
            else:
                print(f"  ❌ {path} NOT FOUND in router routes")
                results['failed'].append(f"route{path}")

    except Exception as e:
        print(f"  ❌ Router: {e}")
        results['failed'].append('router')
    
    # Test 5: Main App
    print("\n[5] FastAPI App Wiring:")
    print("-" * 60)

    try:
        from app.main import app
        print("  ✅ FastAPI app imported")

        total_routes = len(app.routes)
        print(f"  ✅ Total routes: {total_routes}")

        # Collect paths safely — some route objects (Mount) have no 'path' or 'methods'
        all_paths = []
        for route in app.routes:
            p = getattr(route, 'path', None)
            if p:
                all_paths.append(p)

        contribution_paths = [p for p in all_paths if 'contribution' in p]

        if contribution_paths:
            print(f"  ✅ Contribution routes in app: {len(contribution_paths)}")
            for p in sorted(contribution_paths):
                print(f"    - {p}")
            results['passed'].append('app.wiring')
        else:
            # FastAPI sometimes flattens routes differently; check via openapi schema
            try:
                openapi = app.openapi()
                contrib_paths = [p for p in openapi.get('paths', {}) if 'contribution' in p]
                if contrib_paths:
                    print(f"  ✅ Contribution routes via OpenAPI: {len(contrib_paths)}")
                    for p in sorted(contrib_paths):
                        print(f"    - {p}")
                    results['passed'].append('app.wiring')
                else:
                    print("  ❌ No contribution routes found in app")
                    results['failed'].append('app.wiring')
            except Exception as oe:
                print(f"  ❌ OpenAPI check failed: {oe}")
                results['failed'].append('app.wiring')

    except Exception as e:
        print(f"  ❌ Main app: {e}")
        results['failed'].append('app.main')
    
    # Test 6: Dependencies
    print("\n[6] External Dependencies:")
    print("-" * 60)
    
    deps = [
        'pydantic',
        'pydantic_settings',
        'sqlalchemy',
        'fastapi',
        'uvicorn',
    ]
    
    for dep in deps:
        try:
            __import__(dep)
            print(f"  ✅ {dep}")
            results['passed'].append(f"dep.{dep}")
        except ImportError:
            print(f"  ❌ {dep} NOT INSTALLED")
            results['failed'].append(f"dep.{dep}")
    
    # Summary
    print("\n" + "=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {len(results['passed'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    
    if results['failed']:
        print("\nFailed Components:")
        for item in results['failed']:
            print(f"  - {item}")
        return 1
    else:
        print("\n🎉 All components are properly wired!")
        return 0


if __name__ == '__main__':
    sys.exit(check_imports())
