# db/__init__.py
from . import users
from . import trainings

# Теперь извне можно будет вызывать методы как db.users.register(...)