import bcrypt

admin_hash = b"$2b$12$GjF79FWNuuNfl4VWOA28iOk4ubZWWd5OltSsAiZ5TgaWPz5UtAZpu"

words = ["admin123", "admin", "admin@123", "password123", "admin1234"]

for w in words:
    try:
        if bcrypt.checkpw(w.encode(), admin_hash):
            print(f"Match: {w}")
    except:
        pass
