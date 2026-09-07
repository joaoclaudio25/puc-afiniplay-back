# Importa a extensão SQLAlchemy do Flask, que facilita trabalhar com bancos relacionais
from flask_sqlalchemy import SQLAlchemy

# Cria uma instância global de SQLAlchemy.
# Ela será inicializada com a aplicação Flask lá no app.py (db.init_app(app))
db = SQLAlchemy()
