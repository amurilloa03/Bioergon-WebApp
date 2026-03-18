import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import Base, Usuario, Formulario, Respuesta, TipoPregunta
from dotenv import load_dotenv

load_dotenv()

# --- 1. Definir conexiones ---
# Bases de datos origen (SQLite)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_FILE = os.path.join(BASE_DIR, 'forms.db')
sqlite_uri = f"sqlite:///{DB_FILE.replace('\\', '/')}"

# Bases de datos destino (MySQL)
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_host = os.environ.get('DB_HOST', 'localhost')
db_name = os.environ.get('DB_NAME')

if not db_user or not db_name:
    print("ERROR: Por favor, configura DB_USER y DB_NAME en tu archivo .env antes de migrar.")
    exit(1)

mysql_uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"

print(f"Migrando desde SQLite ({DB_FILE}) a MySQL ({db_user}@{db_host}/{db_name})...")

# Crear engines y sesiones
engine_sqlite = create_engine(sqlite_uri)
SessionSqlite = sessionmaker(bind=engine_sqlite)

engine_mysql = create_engine(mysql_uri)
SessionMysql = sessionmaker(bind=engine_mysql)

# --- 2. Crear las tablas en MySQL (si no existen) ---
# Esto solo crea la estructura basada en los modelos de SQLAlchemy
Base.metadata.create_all(engine_mysql)

def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        return instance

# --- 3. Ejecutar Migración ---
from sqlalchemy import text
def migrate():
    source_session = SessionSqlite()
    dest_session = SessionMysql()

    try:
        dest_session.execute(text("SET FOREIGN_KEY_CHECKS=0;"))
        
        # Migrar TipoPregunta
        print("Migrando TipoPregunta...")
        tipos = source_session.query(TipoPregunta).all()
        for t in tipos:
            dest_obj = get_or_create(dest_session, TipoPregunta, ID=t.ID)
            dest_obj.nombre = t.nombre
            dest_obj.descripcion = t.descripcion
        dest_session.commit()

        # Migrar Usuario
        print("Migrando Usuario...")
        usuarios = source_session.query(Usuario).all()
        for u in usuarios:
            dest_obj = get_or_create(dest_session, Usuario, ID=u.ID)
            dest_obj.nombre = u.nombre
            dest_obj.password_hash = u.password_hash
            dest_obj.admin = u.admin
            dest_obj.apellidos = u.apellidos
            dest_obj.correo = u.correo
            dest_obj.c_postal = u.c_postal
        # Desactivar temporalmente los foreign keys para evitar problemas de orden de inserción no es necesario si mantenemos los IDs
        dest_session.commit()

        # Migrar Formulario
        print("Migrando Formulario...")
        forms = source_session.query(Formulario).all()
        for f in forms:
            dest_obj = get_or_create(dest_session, Formulario, ID=f.ID)
            dest_obj.user_id = f.user_id
            dest_obj.nombre = f.nombre
            dest_obj.fecha_creado = f.fecha_creado
            dest_obj.fecha_mod = f.fecha_mod
            dest_obj.ruta_form = f.ruta_form
            dest_obj.visible = f.visible
        dest_session.commit()

        # Migrar Respuesta
        print("Migrando Respuesta...")
        respuestas = source_session.query(Respuesta).all()
        for r in respuestas:
            dest_obj = get_or_create(dest_session, Respuesta, ID=r.ID)
            dest_obj.user_id = r.user_id
            dest_obj.form_id = r.form_id
            dest_obj.fecha_envio = r.fecha_envio
            dest_obj.ruta_respuesta = r.ruta_respuesta
        dest_session.commit()

        print("¡Migración completada con éxito!")

    except Exception as e:
        print(f"Error durante la migración: {e}")
        dest_session.rollback()
    finally:
        dest_session.execute(text("SET FOREIGN_KEY_CHECKS=1;"))
        source_session.close()
        dest_session.close()

if __name__ == "__main__":
    migrate()
