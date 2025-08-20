#!/usr/bin/env python
"""
Django management script to fix current session and semester flags.
This script ensures only one Session and one Semester have the is_current flag set to True.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Session, Semester

def fix_current_flags():
    """Fix the current session and semester flags to ensure only one of each is set."""
    
    print("🔧 Fixing current session and semester flags...")
    
    # Fix Session objects
    sessions = Session.objects.filter(is_current_session=True)
    if sessions.count() > 1:
        print(f"⚠️  Found {sessions.count()} sessions with is_current_session=True")
        # Keep only the first one, unset the others
        first_session = sessions.first()
        for session in sessions.exclude(id=first_session.id):
            session.is_current_session = False
            session.save()
            print(f"   - Unset current flag from session: {session.session}")
        print(f"✅ Kept session '{first_session.session}' as current")
    elif sessions.count() == 1:
        print(f"✅ Current session: {sessions.first().session}")
    else:
        print("⚠️  No current session found")
        # Set the first session as current if any exist
        first_session = Session.objects.first()
        if first_session:
            first_session.is_current_session = True
            first_session.save()
            print(f"✅ Set session '{first_session.session}' as current")
    
    # Fix Semester objects
    semesters = Semester.objects.filter(is_current_semester=True)
    if semesters.count() > 1:
        print(f"⚠️  Found {semesters.count()} semesters with is_current_semester=True")
        # Keep only the first one, unset the others
        first_semester = semesters.first()
        for semester in semesters.exclude(id=first_semester.id):
            semester.is_current_semester = False
            semester.save()
            print(f"   - Unset current flag from semester: {semester.semester}")
        print(f"✅ Kept semester '{first_semester.semester}' as current")
    elif semesters.count() == 1:
        print(f"✅ Current semester: {semesters.first().semester}")
    else:
        print("⚠️  No current semester found")
        # Set the first semester as current if any exist
        first_semester = Semester.objects.first()
        if first_semester:
            first_semester.is_current_semester = True
            first_semester.save()
            print(f"✅ Set semester '{first_semester.semester}' as current")
    
    print("\n🎉 Database cleanup completed!")
    
    # Show final status
    print("\n📊 Final Status:")
    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(is_current_semester=True).first()
    
    if current_session:
        print(f"   Session: {current_session.session} (ID: {current_session.id})")
    else:
        print("   Session: None")
    
    if current_semester:
        print(f"   Semester: {current_semester.semester} (ID: {current_semester.id})")
    else:
        print("   Semester: None")

if __name__ == "__main__":
    try:
        fix_current_flags()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
