#!/usr/bin/env python3
"""
Offline User Role Promotion CLI.
Used by system administrators to promote contributors to reviewer or admin roles
out-of-band without exposing public role assignment endpoints.

Usage:
    python scripts/promote_user.py <email> <reviewer|admin|contributor>
"""

import sys
from pathlib import Path

# Add contribution_service root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal, init_db
from app.db.models import User
from app.core.security import UserRole

def promote_user(email: str, new_role: str):
    init_db()
    db = SessionLocal()
    try:
        valid_roles = [UserRole.CONTRIBUTOR, UserRole.REVIEWER, UserRole.ADMIN]
        if new_role not in valid_roles:
            print(f"Error: Invalid role '{new_role}'. Choose from: {valid_roles}")
            sys.exit(1)

        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"Error: User with email '{email}' not found.")
            sys.exit(1)

        old_role = user.role
        user.role = new_role
        db.commit()
        print(f"Success: Promoted user '{email}' ({user.full_name}) from '{old_role}' to '{new_role}'.")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/promote_user.py <email> <reviewer|admin|contributor>")
        sys.exit(1)
    promote_user(sys.argv[1], sys.argv[2])
