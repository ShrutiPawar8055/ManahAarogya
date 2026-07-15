from sqlmodel import Session, select
from app.database.db import engine
from app.database.models import User, Therapist

def make_therapist(email):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            print(f"User with email {email} not found.")
            return
            
        user.role = "therapist"
        
        # Check if therapist record exists
        therapist = session.exec(select(Therapist).where(Therapist.user_id == user.id)).first()
        if not therapist:
            therapist = Therapist(
                name=user.name or "Dr. Therapist",
                specialty="General Counseling",
                region="Global",
                institution=user.organization or "Private Practice",
                languages="English",
                session_duration=60,
                rating=5.0,
                years_experience=5,
                is_verified=True,
                user_id=user.id
            )
            session.add(therapist)
            print("Created a Therapist profile for the user.")
        else:
            therapist.is_verified = True
            session.add(therapist)
            print("Updated existing Therapist profile.")
            
        session.add(user)
        session.commit()
        print(f"User {email} is now a verified therapist.")

if __name__ == "__main__":
    make_therapist("mohdanasdharar@gmail.com")
