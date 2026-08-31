import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import engine, SessionLocal, Base
from app.models.user import User, UserRole
from app.core.security import get_password_hash


def seed():
    print("Creating tables (if not already existing)...")
    # Create tables for models that do not require extensions first
    User.__table__.create(bind=engine, checkfirst=True)
    
    db = SessionLocal()
    try:
        # Check Admin
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            admin = User(
                name="System Administrator",
                email="admin@example.com",
                password_hash=get_password_hash("Admin123!"),
                role=UserRole.admin
            )
            db.add(admin)
            print("Created admin user: admin@example.com / Admin123!")
        else:
            print("Admin user already exists.")

        # Check Support Agent
        agent = db.query(User).filter(User.email == "agent@example.com").first()
        if not agent:
            agent = User(
                name="Support Agent 1",
                email="agent@example.com",
                password_hash=get_password_hash("Agent123!"),
                role=UserRole.support_agent
            )
            db.add(agent)
            print("Created support agent user: agent@example.com / Agent123!")
        else:
            print("Support agent user already exists.")

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding users: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
