from app.config import get_settings
settings = get_settings()
print(f"Loaded Token from settings: '{settings.GITHUB_TOKEN}'")
