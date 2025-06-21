python3 -m venv venv

source venv/bin/activate
venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate

python manage.py createsuperuser

pip freeze > requirements.txt"
