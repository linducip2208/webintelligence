# aaPanel Deployment
1. Create site `webintel.example.com` rooted at `/www/wwwroot/web-intelligence`.
2. MySQL 8.x: create db `webintel`, import via SQLAlchemy `create_all` or Alembic.
   `mysql -u root -p < source/python/app/db/schema.sql` (db only; tables via app).
3. Redis from aaPanel App Store (default 127.0.0.1:6379).
4. Copy `.env.example` to `.env`, fill secrets.
5. Run `bash deploy/scripts/deploy_aapanel.sh`.
6. In aaPanel Website settings, reverse-proxy to `127.0.0.1:8000` or use `deploy/nginx/webintel.conf`.
7. Go collector is internal-only; do not expose publicly.
