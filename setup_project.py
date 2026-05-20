from pathlib import Path

def create_grooming_bot_structure():
    # Promeni putanju ako želiš drugačije mesto
    base_path = Path.home() / "Desktop" / "GroomingBot-Python"
    
    structure = {
        "bot": {
            "__init__.py": "",
            "bot_instance.py": "",
            "states.py": "",
            "keyboards.py": "",
            "handlers": {
                "__init__.py": "",
                "commands.py": "",
                "booking.py": "",
                "callbacks.py": ""
            }
        },
        "core": {
            "__init__.py": "",
            "config.py": "",
            "logger.py": ""
        },
        "services": {
            "__init__.py": "",
            "sheets_service.py": "",
            "twilio_service.py": "",
            "booking_service.py": ""
        },
        "utils": {
            "__init__.py": ""
        },
        "logs": {},
        "database": {}
    }

    # Kreiranje foldera i fajlova
    base_path.mkdir(parents=True, exist_ok=True)

    def create(struct, current_path):
        for name, content in struct.items():
            path = current_path / name
            if isinstance(content, dict):
                path.mkdir(exist_ok=True)
                create(content, path)
            else:
                path.touch(exist_ok=True)
                if content:
                    path.write_text(content, encoding="utf-8")

    create(structure, base_path)

    # Dodatni root fajlovi
    (base_path / "requirements.txt").touch()
    (base_path / "run.py").touch()
    (base_path / "render.yaml").touch()
    (base_path / ".env").touch()
    (base_path / "README.md").touch()

    print(f"✅ USPEŠNO KREIRANA STRUKTURA!")
    print(f"📍 Lokacija: {base_path.resolve()}")
    print("\nSada možeš otvoriti folder u VS Code ili PyCharm.")

if __name__ == "__main__":
    create_grooming_bot_structure()