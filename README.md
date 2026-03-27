# web-collector-expert
Automated data collection system using Python, FastAPI, and PostgreSQL, fully containerized with Docker


### 🛠️ Bug Fixes & Troubleshooting (March 26, 2026)
- **Fixed:** `ModuleNotFoundError: No module named 'app.models'`.
  - *Solution:* Created physical `models.py` file to define SQLAlchemy schemas.
- **Fixed:** `OperationalError: could not translate host name "db"`.
  - *Solution:* Switched database URL to `localhost` for local development outside the Docker network.
- **Fixed:** `git-lfs` pre-push hook error in Codespaces.
  - *Solution:* Removed the `.git/hooks/pre-push` file to allow standard git pushes without LFS overhead.