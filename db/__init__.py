# db/__init__.py
from . import users
from . import trainings
from . import training_types
from . import membership


# Теперь извне можно будет вызывать методы как db.users.register(...)