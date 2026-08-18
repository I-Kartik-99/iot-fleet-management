from app.database import SessionLocal
from app.models.user import User
from app.auth.auth import hash_password


db = SessionLocal()


user = User(
    username="admin",
    hashed_password=hash_password("admin123")
)


db.add(user)
db.commit()

print("User created")


db.close()