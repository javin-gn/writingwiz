# WritingWiz

A PSLE English composition practice site: browse Continuous and Situational Writing questions with model answers, learn vocabulary and phrases by theme, watch guided videos, and grade your own essays with a rule-based checker.

## Stack

- Django 4.2
- Postgres (Supabase) in production via `dj-database-url`; falls back to local SQLite when `DATABASE_URL` is unset
- WhiteNoise for static files
- django-allauth for Google sign-in
- Deployed on Vercel (zero-config Python/Django detection, no `vercel.json` needed)

## Running locally

```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # fill in SECRET_KEY, leave DATABASE_URL unset to use SQLite

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The app runs at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

## Deploying

Push to the branch connected on Vercel. Set `DATABASE_URL` (and any allauth/Google OAuth env vars) in the Vercel project settings — see `.env.example` for the full list.
