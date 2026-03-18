from flask import Flask, render_template, request, redirect, url_for, session, abort, send_from_directory, jsonify, Response
from flask_wtf.csrf import CSRFProtect, generate_csrf
from authlib.integrations.flask_client import OAuth

import re
import json
import secrets
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, or_, func, Text, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from contextlib import contextmanager
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from passlib.hash import pbkdf2_sha256
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
import csv  
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import shutil



# Cargar variables de entorno desde .env
load_dotenv()

try:
    from supabase_config import supabase
except Exception as e:
    supabase = None
    print("Advertencia: No se pudo cargar supabase_config. Verifica las variables de entorno.")

app = Flask(__name__)
# secret key para sesiones — DEBE configurarse en .env para producción
_secret = os.environ.get('FLASK_SECRET_KEY')
if not _secret:
    if os.environ.get('FLASK_ENV') == 'production':
        raise RuntimeError("FLASK_SECRET_KEY must be set in production environment!")
    import warnings
    warnings.warn(
        'FLASK_SECRET_KEY no configurada. Usando clave de desarrollo. '
        'Configúrala en .env antes de desplegar a producción.',
        stacklevel=1
    )
    _secret = 'dev-insecure-key-change-me'
app.secret_key = _secret

# --- CSRF Protection ---
csrf = CSRFProtect(app)

# --- OAuth Setup ---
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)


# --- SQLAlchemy setup (SQLite forms.db o MySQL) ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_FILE = os.path.join(BASE_DIR, 'forms.db')
FORMS_DIR = os.environ.get('FORMS_DIR', os.path.join(BASE_DIR, 'formularios'))
VERSIONS_DIR = os.path.join(FORMS_DIR, 'versiones')

# Construcción dinámica de URI de DB
db_url = os.environ.get('DATABASE_URL')
if db_url:
    # Si viene con postgres://, cambiarlo a postgresql:// para SQLAlchemy
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    db_uri = db_url
else:
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_name = os.environ.get('DB_NAME')

    if db_user and db_name:
        db_uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
    else:
        # Fallback a SQLite para desarrollo sin BD MySQL configurada
        db_path = DB_FILE.replace('\\', '/')
        db_uri = f"sqlite:///{db_path}"

engine = create_engine(db_uri, echo=False, future=True)



# --- Configuración de subida de imágenes ---
IMG_UPLOADS_DIR = os.path.join(BASE_DIR, 'static', 'uploads', 'form_images')
AVATARS_DIR = os.path.join(BASE_DIR, 'static', 'uploads', 'avatars')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Crear directorios si no existen
os.makedirs(IMG_UPLOADS_DIR, exist_ok=True)
os.makedirs(AVATARS_DIR, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Usuario(Base):
    """Mapea la tabla `Usuario` del esquema SQL proporcionado.
    Columnas: ID, nombre, contraseña, admin, apellidos, correo, c_postal
    """
    __tablename__ = 'Usuario'
    ID = Column('ID', Integer, primary_key=True)
    nombre = Column('nombre', String(50), nullable=False)
    # la columna se llama 'contraseña' en la base original; mapearla a password_hash
    password_hash = Column('contraseña', String(255), nullable=False)
    admin = Column('admin', Integer, nullable=False, default=0)
    apellidos = Column('apellidos', String(100), nullable=True)
    correo = Column('correo', String(320), nullable=True)
    c_postal = Column('c_postal', Integer, nullable=True)


class Formulario(Base):
    __tablename__ = 'Formularios'
    ID = Column('ID', Integer, primary_key=True)
    user_id = Column('user_id', Integer, ForeignKey('Usuario.ID'), nullable=False)
    nombre = Column('nombre', String(100), nullable=False)
    fecha_creado = Column('fecha_creado', String(50), nullable=True)
    fecha_mod = Column('fecha_mod', String(50), nullable=True)
    ruta_form = Column('ruta_form', String(255), nullable=True)
    contenido = Column('contenido', Text, nullable=True)
    visible = Column('visible', Integer, nullable=True, default=1)
    autor = relationship('Usuario', backref='formularios')
    # Relación con Respuesta manejando el borrado en cascada
    respuestas = relationship('Respuesta', cascade="all, delete-orphan", back_populates="formulario")




class Respuesta(Base):
    __tablename__ = 'Respuestas'
    ID = Column('ID', Integer, primary_key=True)
    user_id = Column('user_id', Integer, ForeignKey('Usuario.ID'), nullable=False)
    form_id = Column('form_id', Integer, ForeignKey('Formularios.ID'), nullable=False)
    fecha_envio = Column('fecha_envio', String(50), nullable=True)
    ruta_respuesta = Column('ruta_respuesta', String(255), nullable=True)
    contenido = Column('contenido', Text, nullable=True)
    usuario = relationship('Usuario', backref='respuestas')
    formulario = relationship('Formulario', back_populates='respuestas')




class TipoPregunta(Base):
    """Tabla maestro de tipos de preguntas disponibles"""
    __tablename__ = 'TiposPreguntas'
    ID = Column('ID', Integer, primary_key=True)
    nombre = Column('nombre', String(50), nullable=False, unique=True)
    descripcion = Column('descripcion', String(200), nullable=True)


# Crear tablas si no existen (no sobrescribe tablas existentes)
Base.metadata.create_all(engine)

# Inicializar tipos de preguntas si la tabla está vacía
@contextmanager
def get_db_session():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def _format_date_string(s: str) -> str:
    """Formatea una fecha ISO/string a formato legible en español.
    Función utility compartida por todas las vistas.
    """
    if not s:
        return '—'
    dt = None
    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y'):
            try:
                dt = datetime.strptime(s, fmt)
                break
            except Exception:
                continue
    if not dt:
        return s
    months = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic']
    mon = months[dt.month - 1]
    return f"{dt.day} {mon} {dt.year}, {dt.strftime('%H:%M')}"


def _utcnow_iso() -> str:
    """Devuelve la fecha/hora UTC actual como cadena ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


MIN_PASSWORD_LENGTH = 8


TIPOS_PREGUNTAS_INICIALES = [
    {'nombre': 'short-text', 'descripcion': 'Texto corto (una línea)'},
    {'nombre': 'long-text', 'descripcion': 'Texto largo (múltiples líneas)'},
    {'nombre': 'multiple-choice', 'descripcion': 'Opción múltiple (una sola respuesta)'},
    {'nombre': 'checkbox', 'descripcion': 'Casillas de verificación (múltiples respuestas)'},
    {'nombre': 'dropdown', 'descripcion': 'Lista desplegable'},
    {'nombre': 'rating', 'descripcion': 'Calificación (estrellas)'},
    {'nombre': 'date', 'descripcion': 'Fecha'}
]

with get_db_session() as db_session:
    try:
        any_user = db_session.query(Usuario).first()
    except Exception:
        any_user = None
    if not any_user:
        default_admin_name = os.environ.get('DEFAULT_ADMIN_NAME', 'admin')
        default_admin_pw = os.environ.get('DEFAULT_ADMIN_PASSWORD')
        if not default_admin_pw:
            # Fallback seguro: generar contraseña aleatoria y loguearla
            default_admin_pw = secrets.token_urlsafe(16)
            app.logger.warning(f"!!! NO DEFAULT_ADMIN_PASSWORD SET !!! Created random admin password: {default_admin_pw}")
        
        admin_pw = pbkdf2_sha256.hash(default_admin_pw)
        admin_user = Usuario(nombre=default_admin_name, correo=f'{default_admin_name}@example.com', password_hash=admin_pw, admin=1)
        db_session.add(admin_user)
        db_session.commit()
        app.logger.info(f"Created default admin '{default_admin_name}' in Usuario table")
    
    # Inicializar tipos de preguntas
    try:
        tipos_existentes = db_session.query(TipoPregunta).count()
        if tipos_existentes == 0:
            for tipo_data in TIPOS_PREGUNTAS_INICIALES:
                tipo = TipoPregunta(nombre=tipo_data['nombre'], descripcion=tipo_data['descripcion'])
                db_session.add(tipo)
            db_session.commit()
            app.logger.info("Created 7 question types in TiposPreguntas table")
    except Exception as e:
        app.logger.error(f"Error initializing question types: {e}")



@app.after_request
def set_csrf_cookie(response):
    if response.mimetype == 'text/html':
        response.set_cookie('csrf_token', generate_csrf())
    return response

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/formularios')
def forms():
    q = request.args.get('q', '').strip()
    is_admin = bool(session.get('is_admin', False))
    with get_db_session() as db_session:
        # hacer una única consulta con LEFT OUTER JOIN para traer el nombre del autor
        base_q = db_session.query(Formulario, Usuario.nombre).outerjoin(Usuario, Formulario.user_id == Usuario.ID)
        
        if q:
            base_q = base_q.filter(Formulario.nombre.ilike(f'%{q}%'))
            
        if not is_admin:
            base_q = base_q.filter(Formulario.visible == 1)
        base_q = base_q.order_by(Formulario.fecha_creado.desc())

        rows = base_q.all()

        # construir lista de dicts que la plantilla puede consumir (incluye user_name y fechas formateadas)
        forms_list = []
        for form, user_name in rows:
            raw_creado = getattr(form, 'fecha_creado', None)
            raw_mod = getattr(form, 'fecha_mod', None)
            forms_list.append({
                'ID': getattr(form, 'ID', None),
                'user_id': getattr(form, 'user_id', None),
                'nombre': getattr(form, 'nombre', ''),
                'fecha_creado': _format_date_string(raw_creado),
                'fecha_mod': _format_date_string(raw_mod),
                'ruta_form': getattr(form, 'ruta_form', ''),
                'visible': getattr(form, 'visible', 1),
                'user_name': user_name or '—'
            })

    return render_template('forms.html', forms=forms_list, is_admin=is_admin, q=q, current_page='forms')


@app.route('/respuestas')
def respuestas():
    """Lista de respuestas del usuario autenticado o de todos si es administrador.
    Permite filtrar por formulario, usuario (admin) y rango de fechas.
    """
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    is_admin = bool(session.get('is_admin', False))

    # Obtener parámetros de filtro
    q_form = request.args.get('q_form', '').strip()
    q_user = request.args.get('q_user', '').strip()
    d_from = request.args.get('d_from', '').strip()
    d_to = request.args.get('d_to', '').strip()

    with get_db_session() as db_session:
        # Base query con joins necesarios
        base_q = db_session.query(Respuesta, Formulario.nombre, Usuario.nombre).outerjoin(Formulario, Respuesta.form_id == Formulario.ID).outerjoin(Usuario, Respuesta.user_id == Usuario.ID)
        
        # Filtro de seguridad: usuario normal solo ve sus respuestas
        if not is_admin:
            base_q = base_q.filter(Respuesta.user_id == user_id)
        
        # Aplicar filtros de búsqueda
        if q_form:
            base_q = base_q.filter(Formulario.nombre.ilike(f"%{q_form}%"))
        
        if is_admin and q_user:
            base_q = base_q.filter(Usuario.nombre.ilike(f"%{q_user}%"))
        
        if d_from:
            base_q = base_q.filter(Respuesta.fecha_envio >= d_from)
        
        if d_to:
            # Añadir 23:59:59 para incluir todo el día final
            base_q = base_q.filter(Respuesta.fecha_envio <= f"{d_to}T23:59:59")
        
        rows = base_q.order_by(Respuesta.fecha_envio.desc()).all()

        respuestas_list = []
        for resp, form_name, user_name in rows:
            respuestas_list.append({
                'ID': getattr(resp, 'ID', None),
                'form_name': form_name or '—',
                'ruta_respuesta': getattr(resp, 'ruta_respuesta', ''),
                'fecha_envio': _format_date_string(getattr(resp, 'fecha_envio', None)),
                'user_name': user_name or '—',
                'user_id': getattr(resp, 'user_id', None)
            })

    # Mantener los parámetros en el contexto para el frontend
    args = {
        'q_form': q_form,
        'q_user': q_user,
        'd_from': d_from,
        'd_to': d_to
    }

    return render_template('respuestas.html', respuestas=respuestas_list, is_admin=is_admin, filters=args)


@app.route('/formularios/<int:form_id>/respuestas')
def respuestas_por_formulario(form_id: int):
    """Listar respuestas para un formulario concreto. Solo administradores pueden usar esta vista."""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    is_admin = bool(session.get('is_admin', False))
    if not is_admin:
        abort(403)

    with get_db_session() as db_session:
        # traer respuestas del formulario, y nombre del formulario
        base_q = db_session.query(Respuesta, Usuario.ID, Usuario.nombre, Formulario.nombre).join(Formulario, Respuesta.form_id == Formulario.ID).outerjoin(Usuario, Respuesta.user_id == Usuario.ID).filter(Respuesta.form_id == form_id)
        rows = base_q.order_by(Respuesta.fecha_envio.desc()).all()

        respuestas_list = []
        form_name = None
        for resp, uid, uname, fname in rows:
            form_name = fname or form_name
            respuestas_list.append({
                'ID': getattr(resp, 'ID', None),
                'form_name': fname or '—',
                'ruta_respuesta': getattr(resp, 'ruta_respuesta', ''),
                'fecha_envio': _format_date_string(getattr(resp, 'fecha_envio', None)),
                'user_id': getattr(resp, 'user_id', None)
            })

    return render_template('respuestas.html', respuestas=respuestas_list, is_admin=is_admin, form_filter_name=form_name, form_filter_id=form_id)


def _check_password(stored_pw, candidate):
    """Soporta cadenas en claro o hashes generados por werkzeug.
    Si el valor almacenado parece un hash (contiene ':' o '$'), usa check_password_hash,
    si no, compara texto plano (compatibilidad con DB antigua).
    """
    if not stored_pw:
        return False
    # Primero intentar verificar con passlib (nuestras nuevas hashes)
    try:
        if pbkdf2_sha256.verify(candidate, stored_pw):
            return True
    except Exception:
        # si el formato no es reconocido por passlib, seguimos con fallback
        pass

    # Fallback: compatibilidad con hashes generados por werkzeug u otros
    try:
        if stored_pw.startswith('pbkdf2:') or stored_pw.startswith('$'):
            return check_password_hash(stored_pw, candidate)
    except Exception:
        pass

    # Finalmente comparar texto plano por compatibilidad (no recomendado)
    return stored_pw == candidate


@app.route('/formularios/<int:form_id>/delete', methods=['POST'])
def delete_form(form_id: int):
    """Elimina el formulario con id `form_id`.
    Sólo puede borrar el autor del formulario o un admin.
    """
    user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))

    if not user_id:
        # no autenticado
        return redirect(url_for('index'))

    with get_db_session() as db_session:
        form = db_session.query(Formulario).filter(Formulario.ID == form_id).first()
        if not form:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': 'Form not found'}), 404
            return redirect(url_for('forms'))
        
        if not is_admin:
            abort(403)

        # 1. Eliminar archivos JSON de las respuestas asociadas
        for r in form.respuestas:
            if r.ruta_respuesta and os.path.exists(r.ruta_respuesta):
                try:
                    os.remove(r.ruta_respuesta)
                except Exception as e:
                    app.logger.error(f"Error eliminando archivo de respuesta {r.ID}: {e}")

        # 2. Eliminar archivo JSON del formulario y sus imágenes asociadas
        if form.ruta_form and os.path.exists(form.ruta_form):
            try:
                # Intentar limpiar imágenes de preguntas dentro del JSON
                with open(form.ruta_form, 'r', encoding='utf-8') as f_json:
                    fdata = json.load(f_json)
                    questions = fdata.get('questions', [])
                    for q in questions:
                        img_url = q.get('image')
                        if img_url and 'static/uploads/form_images/' in img_url:
                            img_filename = img_url.split('/')[-1]
                            img_path = os.path.join(IMG_UPLOADS_DIR, img_filename)
                            if os.path.exists(img_path):
                                try:
                                    os.remove(img_path)
                                except: pass

                os.remove(form.ruta_form)
            except Exception as e:
                app.logger.error(f"Error eliminando archivo de formulario {form_id}: {e}")

        # 3. Eliminar registro (el borrado en cascada de la BD se encarga de los registros de Respuesta)
        db_session.delete(form)
        db_session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})

    return redirect(url_for('forms'))


@app.route('/formularios/<int:form_id>/duplicate', methods=['POST'])
def duplicate_form(form_id: int):
    """Crea una copia del formulario (DB y archivo JSON).
    Sólo para administradores.
    """
    user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))

    if not user_id:
        return redirect(url_for('index'))
    if not is_admin:
        abort(403)

    with get_db_session() as db_session:
        original = db_session.query(Formulario).filter(Formulario.ID == form_id).first()
        if not original:
            return redirect(url_for('forms'))

        # 1. Preparar nuevos datos
        nuevo_nombre = f"Copia de {original.nombre}"
        # Generar nombre de archivo único
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        nuevo_filename = f"formulario_copy_{fecha_str}_{secrets.token_hex(4)}.json"
        nueva_ruta = os.path.join(FORMS_DIR, nuevo_filename)

        try:
            # 2. Copiar archivo físico
            if original.ruta_form and os.path.exists(original.ruta_form):
                shutil.copy2(original.ruta_form, nueva_ruta)
            else:
                # Si por algún motivo no hay archivo original, crear uno vacío inicial
                with open(nueva_ruta, 'w', encoding='utf-8') as f:
                    json.dump({"title": nuevo_nombre, "questions": []}, f)
        except Exception as e:
            app.logger.error(f"Error copiando archivo para clonación: {e}")
            return redirect(url_for('forms'))

        # 3. Crear registro en BD
        nuevo_formulario = Formulario(
            nombre=nuevo_nombre,
            ruta_form=nueva_ruta,
            user_id=user_id,
            visible=0, # Por defecto oculto para que el usuario lo revise
            fecha_creado=_utcnow_iso(),
            fecha_mod=_utcnow_iso()
        )
        
        db_session.add(nuevo_formulario)
        db_session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'redirect': url_for('forms')})

    return redirect(url_for('forms'))


@app.route('/formularios/<int:form_id>/toggle_visibility', methods=['POST'])
def toggle_visibility(form_id: int):
    """Alterna la visibilidad del formulario (visible 1 / no visible 0).
    Sólo admin o autor pueden cambiarla.
    """
    user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))

    if not user_id:
        return redirect(url_for('index'))

    with get_db_session() as db_session:
        form = db_session.query(Formulario).filter(Formulario.ID == form_id).first()
        if not form:
            return redirect(url_for('forms'))

        if not is_admin:
            abort(403)

        # toggle
        try:
            form.visible = 0 if (form.visible and int(form.visible) == 1) else 1
        except Exception:
            form.visible = 1

        db_session.add(form)
        db_session.commit()
        visible_status = bool(form.visible)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'visible': visible_status})

    return redirect(url_for('forms'))


@app.route('/formularios/create', methods=['POST'])
def create_form():
    """Crea un nuevo Formulario y su archivo JSON.
    Requiere sesión válida y permisos de admin.
    """
    user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))
    if not user_id:
        return redirect(url_for('index'))
    if not is_admin:
        abort(403)
    
    nombre = (request.form.get('nombre') or '').strip()
    if not nombre:
        return redirect(url_for('forms'))

    now = _utcnow_iso()
    
    # Generar nombre de archivo (slug)
    nombre_archivo = nombre.lower().replace(' ', '_').replace('/', '_')
    ruta_json = os.path.normpath(os.path.join(FORMS_DIR, f'{nombre_archivo}.json'))
    
    # Asegurar que la carpeta existe
    os.makedirs(FORMS_DIR, exist_ok=True)
    
    with get_db_session() as db_session:
        # Crear registro en BD
        nuevo = Formulario(
            user_id=user_id, 
            nombre=nombre, 
            ruta_form=ruta_json,  # Mantenido como metadato histórico
            visible=1, 
            fecha_creado=now, 
            fecha_mod=now
        )
        db_session.add(nuevo)
        db_session.flush()  # Para obtener el ID
        form_id = nuevo.ID
        
        # Guardar JSON en la base de datos en vez del disco duro
        datos_formulario = {
            "id": form_id,
            "nombre": nombre,
            "descripcion": "",
            "preguntas": [],
            "creado": now,
            "modificado": now
        }
        nuevo.contenido = json.dumps(datos_formulario, ensure_ascii=False)
        db_session.commit()

    return redirect(url_for('forms'))


def is_valid_email(value: str) -> bool:
    """Comprueba de forma sencilla si una cadena tiene formato de email.
    Usamos una comprobación práctica (no completa RFC) suficiente para validación de formulario.
    """
    if not value or '@' not in value:
        return False
    # patrón simple: algo@dominio.ext (no admite espacios)
    pattern = r"[^@\s]+@[^@\s]+\.[^@\s]+"
    return re.fullmatch(pattern, value) is not None


@app.route('/login', methods=['POST'])
def login():
    user_input = request.form.get('user', '').strip()
    pwd = request.form.get('password', '')
    if not user_input or not pwd:
        return render_template('index.html', error='Usuario o contraseña inválidos')

    # Si el usuario introducido parece un correo, validar su formato
    if '@' in user_input and not is_valid_email(user_input):
        return render_template('index.html', error='El correo proporcionado no tiene formato válido')

    with get_db_session() as db_session:
        # Buscar usuario de forma case-insensitive tanto por nombre como por correo
        try:
            user = db_session.query(Usuario).filter(
                or_(Usuario.nombre.ilike(user_input), Usuario.correo.ilike(user_input))
            ).first()
        except Exception:
            # Fallback a comparación exacta si ilike no es soportado por el dialecto
            user = db_session.query(Usuario).filter(
                or_(Usuario.nombre == user_input, Usuario.correo == user_input)
            ).first()

        if not user:
            app.logger.debug("Login failed: user not found for input=%s", user_input)
            return render_template('index.html', error='Usuario no encontrado')

        # comprobar contraseña
        if _check_password(user.password_hash, pwd):
            app.logger.debug("Login success: user id=%s", getattr(user, 'ID', 'unknown'))
            # establecer sesión (flask.session)
            session['user_id'] = user.ID
            session['username'] = user.nombre
            session['is_admin'] = bool(user.admin)
            return redirect(url_for('forms'))

        app.logger.debug("Login failed: wrong password for user id=%s", getattr(user, 'ID', 'unknown'))
        return render_template('index.html', error='Contraseña incorrecta')


@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route('/authorize')
def google_authorize():
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            # Fallback if userinfo is not in token structure
            user_info = oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo').json()
            
        email = user_info['email']
        name = user_info.get('name', email.split('@')[0])
        
        with get_db_session() as db_session:
            user = db_session.query(Usuario).filter(Usuario.correo == email).first()
            if not user:
                # Generar una contraseña aleatoria muy segura para cumplir con el modelo
                random_pwd = secrets.token_urlsafe(32)
                pw_hash = pbkdf2_sha256.hash(random_pwd)
                
                user = Usuario(
                    nombre=name,
                    correo=email,
                    password_hash=pw_hash,
                    admin=0
                )
                db_session.add(user)
                db_session.commit()
                db_session.refresh(user)
            
            session['user_id'] = user.ID
            session['username'] = user.nombre
            session['is_admin'] = bool(user.admin)
            
        return redirect(url_for('forms'))
    except Exception as e:
        app.logger.error(f"Error in Google OAuth: {e}")
        return render_template('index.html', error='Error al autenticar con Google')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    nombre = request.form.get('nombre', '').strip()
    apellidos = request.form.get('apellidos', '').strip()
    correo = request.form.get('correo', '').strip()
    password = request.form.get('password', '')
    c_postal = request.form.get('c_postal', None)

    if not nombre or not apellidos or not correo or not password or not c_postal:
        return render_template('register.html', error='Todos los campos son obligatorios')

    if len(password) < MIN_PASSWORD_LENGTH:
        return render_template('register.html', error=f'La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres')

    # Validación del formato del correo
    if not is_valid_email(correo):
        return render_template('register.html', error='El correo proporcionado no tiene formato válido')

    with get_db_session() as db_session:
        existing = db_session.query(Usuario).filter(
            or_(Usuario.nombre == nombre, Usuario.correo == correo)
        ).first()
        if existing:
            return render_template('register.html', error='Nombre o correo ya existentes')

        # hashear contraseña usando passlib
        pw_hash = pbkdf2_sha256.hash(password)
        try:
            c_postal_int = int(c_postal)
        except (ValueError, TypeError):
            return render_template('register.html', error='El código postal debe contener solo dígitos')

        new_user = Usuario(
            nombre=nombre,
            apellidos=apellidos,
            correo=correo,
            password_hash=pw_hash,
            c_postal=c_postal_int
        )
        db_session.add(new_user)
        db_session.commit()
        # iniciar sesión tras registro (flask.session)
        session['user_id'] = new_user.ID
        session['username'] = new_user.nombre
        session['is_admin'] = bool(new_user.admin)

    return redirect(url_for('forms'))


@app.route('/logout')
def logout():
    """Cierra la sesión del usuario y redirige a la página de inicio."""
    session.clear()
    return redirect(url_for('index'))


@app.route('/perfil')
def perfil():
    """Renderiza la página de perfil del usuario (mínimo por ahora).
    Redirige al índice si no hay usuario autenticado."""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    username = session.get('username')
    is_admin = bool(session.get('is_admin', False))
    # obtener datos del usuario desde la base para mostrarlos en el perfil
    user_data = None
    with get_db_session() as db_session:
        try:
            u = db_session.query(Usuario).filter(Usuario.ID == user_id).first()
        except Exception:
            u = None
        if u:
            user_data = {
                'ID': getattr(u, 'ID', None),
                'nombre': getattr(u, 'nombre', ''),
                'apellidos': getattr(u, 'apellidos', ''),
                'correo': getattr(u, 'correo', ''),
                'c_postal': getattr(u, 'c_postal', ''),
                'admin': bool(getattr(u, 'admin', False))
            }

    profile_msg = session.pop('profile_msg', None)
    profile_error = session.pop('profile_error', None)
    return render_template('perfil.html', username=username, is_admin=is_admin, user=user_data, profile_msg=profile_msg, profile_error=profile_error, current_page='perfil')

@app.context_processor
def utility_processor():
    def get_user_avatar(user_id):
        if not user_id:
            return None
        prefix = f"avatar_{user_id}."
        if supabase:
            try:
                files = supabase.storage.from_('avatars').list()
                for f in files:
                    if f['name'].startswith(prefix):
                        return supabase.storage.from_('avatars').get_public_url(f['name'])
            except Exception:
                pass
                
        try:
            for filename in os.listdir(AVATARS_DIR):
                if filename.startswith(prefix):
                    filepath = os.path.join(AVATARS_DIR, filename)
                    mtime = int(os.path.getmtime(filepath))
                    return url_for('static', filename=f'uploads/avatars/{filename}') + f'?v={mtime}'
        except Exception:
            pass
        return None
    return dict(get_user_avatar=get_user_avatar)

@app.route('/perfil/editar', methods=['GET', 'POST'])
def edit_perfil():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))

    with get_db_session() as db_session:
        u = db_session.query(Usuario).filter(Usuario.ID == user_id).first()
        if not u:
            return redirect(url_for('index'))

        if request.method == 'GET':
            return redirect(url_for('perfil'))

        # POST: procesar actualización
        nombre = (request.form.get('nombre') or '').strip()
        apellidos = (request.form.get('apellidos') or '').strip()
        correo = (request.form.get('correo') or '').strip()
        c_postal = request.form.get('c_postal', '').strip()
        new_password = request.form.get('password', '')

        if not nombre or not correo or not c_postal or not apellidos:
            session['profile_error'] = 'Nombre, apellidos, correo y código postal son obligatorios.'
            return redirect(url_for('perfil'))

        if not is_valid_email(correo):
            session['profile_error'] = 'El correo electrónico no tiene un formato válido.'
            return redirect(url_for('perfil'))

        try:
            c_postal_int = int(c_postal)
        except Exception:
            session['profile_error'] = 'El código postal debe ser numérico.'
            return redirect(url_for('perfil'))

        # aplicar cambios
        u.nombre = nombre
        u.apellidos = apellidos
        u.correo = correo
        u.c_postal = c_postal_int
        if new_password:
            try:
                u.password_hash = pbkdf2_sha256.hash(new_password)
            except Exception:
                pass

        # Procesar foto de perfil
        delete_avatar = request.form.get('delete_avatar') == '1'
        avatar_file = request.files.get('avatar')
        
        # Si se marca borrar o se sube uno nuevo, hay que limpiar el anterior
        if delete_avatar or (avatar_file and avatar_file.filename != ''):
            prefix = f"avatar_{user_id}."
            if supabase:
                try:
                    files = supabase.storage.from_('avatars').list()
                    for f in files:
                        if f['name'].startswith(prefix):
                            supabase.storage.from_('avatars').remove([f['name']])
                except: pass
            try:
                for f_name in os.listdir(AVATARS_DIR):
                    if f_name.startswith(prefix):
                        os.remove(os.path.join(AVATARS_DIR, f_name))
            except:
                pass

        # Si se subió un nuevo archivo, guardarlo
        if avatar_file and avatar_file.filename != '':
            if allowed_file(avatar_file.filename):
                ext = avatar_file.filename.rsplit('.', 1)[1].lower()
                new_filename = f"avatar_{user_id}.{ext}"
                if supabase:
                    try:
                        file_bytes = avatar_file.read()
                        supabase.storage.from_('avatars').upload(new_filename, file_bytes, {"content-type": avatar_file.content_type})
                    except Exception as e:
                        app.logger.error(f"Error subiendo avatar a Supabase: {e}")
                else:
                    avatar_file.save(os.path.join(AVATARS_DIR, new_filename))

        db_session.add(u)
        db_session.commit()

    # actualizar nombre en sesión
    session['username'] = nombre
    session['profile_msg'] = 'Perfil actualizado correctamente'
    return redirect(url_for('perfil'))


# ===== API Routes para Form Builder =====

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    """Endpoint para subir imágenes de preguntas (solo admin)"""
    user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))
    if not user_id or not is_admin:
        return jsonify({'error': 'No autorizado'}), 401

    if 'image' not in request.files:
        return jsonify({'error': 'No se ha enviado ninguna imagen'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400
    
    if file and allowed_file(file.filename):
        # Asegurar que el directorio de uploads existe
        os.makedirs(IMG_UPLOADS_DIR, exist_ok=True)
        
        # Generar nombre único para evitar colisiones
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(f"{timestamp}_{file.filename}")
        
        if supabase:
            try:
                file_bytes = file.read()
                supabase.storage.from_('form_images').upload(filename, file_bytes, {"content-type": file.content_type})
                # get_public_url works as long as the bucket is public
                # Wait, Supabase buckets must be configured as public for this to work natively
                file_url = supabase.storage.from_('form_images').get_public_url(filename)
                return jsonify({'url': file_url, 'success': True}), 200
            except Exception as e:
                app.logger.error(f"Error guardando imagen en Supabase: {e}")
                return jsonify({'error': 'Error interno al guardar la imagen'}), 500
        else:
            filepath = os.path.join(IMG_UPLOADS_DIR, filename)
            try:
                file.save(filepath)
                # Retornar la URL estática para que el frontend la use
                file_url = url_for('static', filename=f'uploads/form_images/{filename}')
                return jsonify({'url': file_url, 'success': True}), 200
            except Exception as e:
                app.logger.error(f"Error guardando imagen: {e}")
                return jsonify({'error': 'Error interno al guardar la imagen'}), 500
    
    return jsonify({'error': 'Tipo de archivo no permitido (Soportados: PNG, JPG, JPEG, GIF, WEBP)'}), 400

@app.route("/api/tipos-preguntas", methods=['GET'])
def get_tipos_preguntas():
    """Obtener los tipos de preguntas disponibles"""
    with get_db_session() as db_session:
        tipos = db_session.query(TipoPregunta).all()
        tipos_list = [
            {'id': t.ID, 'nombre': t.nombre, 'descripcion': t.descripcion}
            for t in tipos
        ]
        return jsonify(tipos_list)


@app.route("/api/formularios/<int:form_id>", methods=['GET'])
def get_formulario(form_id):
    """Obtener formulario con sus preguntas desde JSON"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'No autorizado'}), 401
    
    with get_db_session() as db_session:
        formulario = db_session.query(Formulario).filter(Formulario.ID == form_id).first()
        if not formulario:
            return jsonify({'error': 'Formulario no encontrado'}), 404
        
        # Verificar permisos (admin, autor, o responder formulario)
        is_admin = bool(session.get('is_admin', False))
        current_path = request.path
        is_responding = '/responder-formulario' in request.referrer if request.referrer else False
        
        # Si no es admin ni autor, solo puede acceder si está respondiendo el formulario
        if formulario.user_id != user_id and not is_admin:
            # Permitir si está intentando responder el formulario
            if not is_responding:
                return jsonify({'error': 'No tienes permiso'}), 403
    
    # Cargar desde BD (columna JSON)
    try:
        if formulario.contenido:
            datos = json.loads(formulario.contenido)
            
            # Convertir formato JSON al formato que espera el React
            preguntas = []
            for preg_data in datos.get('preguntas', []):
                preg_dict = {
                    'id': preg_data.get('id'),
                    'type': preg_data.get('tipo', 'short-text'),
                    'text': preg_data.get('texto', ''),
                    'required': preg_data.get('requerida', False),
                    'options': preg_data.get('opciones', []),
                    'image': preg_data.get('imagen', None),
                    'dependsOn': preg_data.get('dependsOn'),
                    'dependsValue': preg_data.get('dependsValue')
                }
                preguntas.append(preg_dict)
            
            return jsonify({
                'title': datos.get('nombre', formulario.nombre),
                'description': datos.get('descripcion', ''),
                'theme': datos.get('theme', 'default'),
                'questions': preguntas
            })

        else:
            # Si el JSON no existe, retornar estructura vacía
            return jsonify({
                'title': formulario.nombre,
                'description': '',
                'questions': []
            })
    except Exception as e:
        app.logger.error(f"Error loading JSON: {e}")
        return jsonify({'error': 'Error cargando formulario'}), 500


@app.route("/api/formularios", methods=['POST'])
def create_formulario_api():
    """Crear nuevo formulario y guardarlo en JSON"""
    user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))
    
    if not user_id or not is_admin:
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.get_json()
    titulo = data.get('title', 'Sin título')
    descripcion = data.get('description', '')
    preguntas = data.get('questions', [])
    
    now = _utcnow_iso()
    
    # Generar nombre de archivo (slug)
    nombre_archivo = titulo.lower().replace(' ', '_').replace('/', '_')
    ruta_json = os.path.normpath(os.path.join(FORMS_DIR, f'{nombre_archivo}.json'))
    
    # Asegurar que la carpeta existe
    os.makedirs(FORMS_DIR, exist_ok=True)
    
    with get_db_session() as db_session:
        try:
            nuevo_form = Formulario(
                user_id=user_id,
                nombre=titulo,
                ruta_form=ruta_json,
                visible=1,
                fecha_creado=now,
                fecha_mod=now
            )
            db_session.add(nuevo_form)
            db_session.flush()
            form_id = nuevo_form.ID
            
            # Mapear preguntas al formato unificado (Spanish keys)
            preguntas_mapeadas = []
            for idx, preg in enumerate(preguntas):
                preg_mapped = {
                    'id': preg.get('id'),
                    'tipo': preg.get('type', 'short-text'),
                    'tipo_id': None,
                    'texto': preg.get('text', ''),
                    'requerida': preg.get('required', False),
                    'opciones': preg.get('options', []),
                    'imagen': preg.get('image', None),
                    'orden': idx,
                    'dependsOn': preg.get('dependsOn'),
                    'dependsValue': preg.get('dependsValue')
                }
                preguntas_mapeadas.append(preg_mapped)

            datos_formulario = {
                "id": form_id,
                "nombre": titulo,
                "descripcion": descripcion,
                "theme": data.get('theme', 'default'),
                "preguntas": preguntas_mapeadas,
                "creado": now,
                "modificado": now
            }
            
            nuevo_form.contenido = json.dumps(datos_formulario, ensure_ascii=False)
            db_session.commit()
            
            return jsonify({'form_id': form_id}), 201

        except Exception as e:
            db_session.rollback()
            app.logger.error(f"Error saving JSON in DB: {e}")
            return jsonify({'error': 'Error guardando formulario'}), 500


@app.route("/api/formularios/<int:form_id>", methods=['PUT'])
def update_formulario_api(form_id):
    """Actualizar formulario: guardar preguntas en JSON"""
    user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))
    
    if not user_id or not is_admin:
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.get_json()
    titulo = data.get('title', 'Sin título')
    descripcion = data.get('description', '')
    preguntas = data.get('questions', [])
    
    with get_db_session() as db_session:
        formulario = db_session.query(Formulario).filter(Formulario.ID == form_id).first()
        if not formulario:
            return jsonify({'error': 'Formulario no encontrado'}), 404
        
        # Verificar permisos
        if formulario.user_id != user_id and not is_admin:
            return jsonify({'error': 'No tienes permiso'}), 403
        
        # Actualizar fecha de modificación
        formulario.nombre = titulo
        formulario.fecha_mod = _utcnow_iso()
        # Extraer la ruta antes de cerrar la sesión para evitar DetachedInstanceError
        ruta_form_str = formulario.ruta_form
        db_session.commit()
    
    # 0. Crear copia de seguridad (Versión) antes de actualizar
    try:
        filename = os.path.basename(ruta_form_str)
        ruta_json = os.path.join(FORMS_DIR, filename)
        if os.path.exists(ruta_json):
            # Carpeta específica para versiones de este formulario
            form_versions_dir = os.path.join(VERSIONS_DIR, str(form_id))
            os.makedirs(form_versions_dir, exist_ok=True)
            
            # Nombre: v_YYYYMMDD_HHMMSS_nombre.json
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            nombre_version = f"v_{timestamp}_{secure_filename(titulo)}.json"
            ruta_version = os.path.join(form_versions_dir, nombre_version)
            
            shutil.copy2(ruta_json, ruta_version)
            app.logger.info(f"Versión guardada: {ruta_version}")
    except Exception as e:
        app.logger.error(f"Error al crear versión de seguridad: {e}")

    # Guardar en BD (todas las preguntas con sus datos)
    try:
        # Convertir formato React al formato JSON
        preguntas_json = []
        for idx, preg in enumerate(preguntas):
            preg_json = {
                'id': preg.get('id'),
                'tipo': preg.get('type', 'short-text'),
                'tipo_id': None,  # Se puede usar para referencias futuras
                'texto': preg.get('text', ''),
                'requerida': preg.get('required', False),
                'opciones': preg.get('options', []),
                'imagen': preg.get('image', None),
                'orden': idx,
                'dependsOn': preg.get('dependsOn'),
                'dependsValue': preg.get('dependsValue')
            }
            preguntas_json.append(preg_json)
        
        datos_formulario = {
            "id": form_id,
            "nombre": titulo,
            "descripcion": descripcion,
            "theme": data.get('theme', 'default'),
            "preguntas": preguntas_json,
            "creado": formulario.fecha_creado,
            "modificado": formulario.fecha_mod
        }

        with get_db_session() as db_session:
            formulario_update = db_session.query(Formulario).filter(Formulario.ID == form_id).first()
            formulario_update.contenido = json.dumps(datos_formulario, ensure_ascii=False)
            db_session.commit()
        
        return jsonify({'form_id': form_id}), 200
    except Exception as e:
        app.logger.error(f"Error saving JSON in DB: {e}")
        return jsonify({'error': 'Error guardando formulario'}), 500


@app.route("/api/respuestas/<int:form_id>", methods=['POST'])
def guardar_respuestas(form_id):
    """Guardar respuestas de un formulario en JSON y BD"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.get_json()
    respuestas = data.get('respuestas', {})
    
    with get_db_session() as db_session:
        formulario = db_session.query(Formulario).filter(Formulario.ID == form_id).first()
        if not formulario:
            return jsonify({'error': 'Formulario no encontrado'}), 404
        
        # Crear nombre para el archivo de respuesta
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"formulario_{form_id}_{user_id}_{timestamp}.json"
        
        # Ruta donde guardar las respuestas
        respuestas_dir = os.path.join(BASE_DIR, "respuestas")
        os.makedirs(respuestas_dir, exist_ok=True)
        
        ruta_respuesta = os.path.normpath(os.path.join(respuestas_dir, nombre_archivo))
      
        
        
        # Estructura de datos de la respuesta
        datos_respuesta = {
            "id_formulario": form_id,
            "id_usuario": user_id,
            "nombre_formulario": formulario.nombre,
            "respuestas": respuestas,
            "fecha_respuesta": _utcnow_iso(),
            "ip_usuario": request.remote_addr
        }
        
        try:
            # Guardar en BD con la nueva columna 'contenido'
            nueva_respuesta = Respuesta(
                user_id=user_id,
                form_id=form_id,
                fecha_envio=_utcnow_iso(),
                ruta_respuesta=ruta_respuesta,
                contenido=json.dumps(datos_respuesta, ensure_ascii=False)
            )
            db_session.add(nueva_respuesta)
            db_session.commit()
            
            return jsonify({'success': True, 'mensaje': 'Respuestas guardadas correctamente'}), 200
        except Exception as e:
            db_session.rollback()
            app.logger.error(f"Error saving responses: {e}")
            return jsonify({'error': 'Error guardando respuestas'}), 500


@app.route("/api/respuestas/archivo/<path:filepath>", methods=['GET'])
def obtener_respuesta_json(filepath):
    """Obtener contenido de un archivo JSON de respuesta con el formulario completo"""
    user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))
    
    if not user_id:
        return jsonify({'error': 'No autorizado'}), 401
    
    # Sanitizar el nombre de archivo para prevenir path traversal
    safe_filename = secure_filename(os.path.basename(filepath))
    if not safe_filename or safe_filename != os.path.basename(filepath):
        return jsonify({'error': 'Nombre de archivo no válido'}), 400
    
    respuestas_dir = os.path.join(BASE_DIR, "respuestas")
    ruta_completa = os.path.join(respuestas_dir, safe_filename)
    
    # Verificar que la ruta está dentro del directorio permitido
    if not os.path.abspath(ruta_completa).startswith(os.path.abspath(respuestas_dir)):
        return jsonify({'error': 'Acceso denegado'}), 403
    
    try:
        with open(ruta_completa, 'r', encoding='utf-8') as f:
            respuesta_data = json.load(f)
        
        # Verificar que el usuario es propietario de esta respuesta o es administrador
        if respuesta_data.get('id_usuario') != user_id and not is_admin:
            return jsonify({'error': 'No autorizado para ver esta respuesta'}), 403
        
        # Obtener el formulario original para mostrar junto con las respuestas
        form_id = respuesta_data.get('id_formulario')
        with get_db_session() as db_session:
            formulario = db_session.query(Formulario).filter(Formulario.ID == form_id).first()
            ruta_json = None
            if formulario:
                filename = os.path.basename(formulario.ruta_form)
                ruta_json = os.path.join(FORMS_DIR, filename)

            if formulario and ruta_json and os.path.exists(ruta_json):
                with open(ruta_json, 'r', encoding='utf-8') as f:
                    form_data = json.load(f)
                
                # Convertir preguntas al formato que espera React
                preguntas = []
                for preg_data in form_data.get('preguntas', []):
                    preg_dict = {
                        'id': preg_data.get('id'),
                        'type': preg_data.get('tipo', 'short-text'),
                        'text': preg_data.get('texto', ''),
                        'required': preg_data.get('requerida', False),
                        'options': preg_data.get('opciones', []),
                        'image': preg_data.get('imagen'),
                        'dependsOn': preg_data.get('dependsOn'),
                        'dependsValue': preg_data.get('dependsValue')
                    }
                    preguntas.append(preg_dict)
                
                # Devolver formulario con respuestas
                return jsonify({
                    'title': form_data.get('nombre', 'Formulario'),
                    'description': form_data.get('descripcion', ''),
                    'questions': preguntas,
                    'respuestas': respuesta_data.get('respuestas', {}),
                    'fecha_respuesta': respuesta_data.get('fecha_respuesta'),
                    'readonly': True
                }), 200
        
        # Si no se puede cargar el formulario, devolver solo las respuestas
        return jsonify(respuesta_data), 200
    except FileNotFoundError:
        return jsonify({'error': 'Archivo no encontrado'}), 404
    except Exception as e:
        app.logger.error(f"Error reading response file: {e}")
        return jsonify({'error': 'Error al leer el archivo'}), 500


@app.route("/form-builder")
def form_builder():
    """Renderizar el form builder (verificar sesión primero)"""
    user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))
    
    if not user_id or not is_admin:
        return redirect(url_for('index'))
    
    return send_from_directory("form_builder/build", "index.html")

@app.route("/form-builder/static/<path:filename>")
def form_builder_static(filename):
    return send_from_directory("form_builder/build/static", filename)

@app.route("/form-builder/<path:filename>")
def form_builder_files(filename):
    return send_from_directory("form_builder/build", filename)

@app.route("/responder-formulario")
def responder_formulario():
    """Renderizar la página para responder un formulario"""
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(url_for('login'))
    
    form_id = request.args.get('form_id')
    if not form_id:
        return redirect(url_for('formularios'))
    
    return send_from_directory("form_builder/build", "index.html")

@app.route("/responder-formulario/static/<path:filename>")
def responder_static(filename):
    return send_from_directory("form_builder/build/static", filename)

@app.route("/responder-formulario/<path:filename>")
def responder_files(filename):
    return send_from_directory("form_builder/build", filename)


@app.route("/estadisticas-formulario")
def estadisticas_formulario():
    """Renderizar el dashboard de estadísticas"""
    user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))
    
    if not user_id:
        return redirect(url_for('login'))
        
    return send_from_directory("form_builder/build", "index.html")

@app.route("/estadisticas-formulario/static/<path:filename>")
def estadisticas_static(filename):
    return send_from_directory("form_builder/build/static", filename)

@app.route("/estadisticas-formulario/<path:filename>")
def estadisticas_files(filename):
    return send_from_directory("form_builder/build", filename)

@app.route('/exportar-csv/<int:form_id>')
def exportar_csv(form_id):
    """Exportar todas las respuestas de un formulario a CSV"""
    user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))
    
    if not user_id or not is_admin:
        abort(403)

    # 1. Obtener el formulario de la BD para sacar su ruta_form
    with get_db_session() as db_session:
        formulario = db_session.query(Formulario).filter(Formulario.ID == form_id).first()
        if not formulario:
            return "Formulario no encontrado", 404

    # 2. Leer el JSON original del formulario de la BD para mapear los ID con los Textos de las preguntas
    mapa_preguntas = {}
    if formulario.contenido:
        form_data = json.loads(formulario.contenido)
        for preg in form_data.get('preguntas', []):
            mapa_preguntas[str(preg.get('id'))] = preg.get('texto', f"Pregunta {preg.get('id')}")

    # 3. Buscar las respuestas de este formulario en BD
    with get_db_session() as db_session:
        respuestas_db = db_session.query(Respuesta).filter(Respuesta.form_id == form_id).all()
        
    if not respuestas_db:
        return "No hay respuestas para este formulario", 404

    # 4. Procesar todas las respuestas JSON y construir las filas del CSV
    datos_csv = []
    columnas_dinamicas = set()

    for r_entry in respuestas_db:
        if not r_entry.contenido:
            continue
        try:
            data = json.loads(r_entry.contenido)
            
            # Columnas fijas base
            fila = {
                "ID Usuario": data.get("id_usuario", "Desconocido"),
                "Fecha y Hora": data.get("fecha_respuesta", ""),
                "IP": data.get("ip_usuario", "")
            }
            
            # Columnas dinámicas (las respuestas a cada pregunta)
            respuestas_usuario = data.get("respuestas", {})
            for q_id, respuesta in respuestas_usuario.items():
                # Usar el texto de la pregunta real (o un texto genérico si la pregunta fue borrada)
                titulo_columna = mapa_preguntas.get(str(q_id), f"Preg. Borrada ({q_id})")
                columnas_dinamicas.add(titulo_columna)
                
                if isinstance(respuesta, list):
                    fila[titulo_columna] = " | ".join(str(r) for r in respuesta)
                else:
                    fila[titulo_columna] = str(respuesta)
            
            datos_csv.append(fila)
        except Exception as e:
            app.logger.error(f"Error leyendo respuesta {r_entry.ID}: {e}")

    # 5. Generar archivo CSV en memoria
    output = io.StringIO()
    output.write('\ufeff') # BOM para que Excel lea los acentos y las 'ñ' correctamente
    
    # Ordenar columnas: Primero las fijas, luego las dinámicas ordenadas alfabéticamente
    todas_columnas = ["ID Usuario", "Fecha y Hora", "IP"] + sorted(list(columnas_dinamicas))
    
    escritor = csv.DictWriter(output, fieldnames=todas_columnas)
    escritor.writeheader()
    escritor.writerows(datos_csv)

    # 6. Devolver el archivo descargable
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={formulario.nombre.replace(' ', '_')}_Respuestas.csv"}
    )


@app.route("/api/formularios/<int:form_id>/stats", methods=['GET'])
def get_form_stats(form_id):
    """Obtener estadísticas agregadas de las respuestas de un formulario"""
    user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))
    
    if not user_id:
        return jsonify({'error': 'No autorizado'}), 401
        
    with SessionLocal() as db_session:
        formulario = db_session.query(Formulario).filter(Formulario.ID == form_id).first()
        if not formulario:
            return jsonify({'error': 'Formulario no encontrado'}), 404
            
        # Solo admin o el dueño pueden ver estadísticas
        if not is_admin and formulario.user_id != user_id:
            return jsonify({'error': 'Acceso prohibido'}), 403
            
        # Cargar definición del formulario desde BBDD
        if not formulario.contenido:
            return jsonify({'error': 'Definición de formulario vacía'}), 404
            
        form_def = json.loads(formulario.contenido)
        preguntas = form_def.get('preguntas', [])
        
        # Obtener parámetros de filtro
        d_from = request.args.get('d_from')
        d_to = request.args.get('d_to')
        
        # Obtener todas las respuestas con filtro opcional de fecha
        query = db_session.query(Respuesta).filter(Respuesta.form_id == form_id)
        
        if d_from:
            query = query.filter(Respuesta.fecha_envio >= d_from)
        if d_to:
            # Añadir T23:59:59 para incluir todo el día de fin
            query = query.filter(Respuesta.fecha_envio <= f"{d_to}T23:59:59")
            
        respuestas_db = query.all()
        total_respuestas = len(respuestas_db)
        
        # Inicializar estructura de estadísticas
        stats = {
            'total_responses': total_respuestas,
            'questions': []
        }
        
        # Preparar contenedores para agregación
        agregaciones = {}
        for q in preguntas:
            q_id = str(q.get('id'))
            q_tipo = q.get('tipo', '')
            agregaciones[q_id] = {
                'id': q_id,
                'title': q.get('texto', ''),
                'type': q_tipo,
                'counts': {}, # Para opciones
                'rating_sum': 0,
                'rating_counts': {}, # Para estrellas 1-5
                'text_responses': [], # Para respuestas abiertas
                'total_answered': 0
            }
            # Pre-poblar opciones si existen
            opciones = q.get('opciones', [])
            if opciones:
                for opt in opciones:
                    agregaciones[q_id]['counts'][opt] = 0

        # Procesar cada archivo de respuesta
        respuestas_dir = os.path.join(BASE_DIR, "respuestas")
        for r_entry in respuestas_db:
            filename_resp = os.path.basename(r_entry.ruta_respuesta)
            ruta_resp_real = os.path.join(respuestas_dir, filename_resp)
            if not os.path.exists(ruta_resp_real):
                continue
            
            try:
                with open(ruta_resp_real, 'r', encoding='utf-8') as f:
                    r_data = json.load(f)
                    res_usuario = r_data.get('respuestas', {})
                    
                    for q_id, val in res_usuario.items():
                        q_id = str(q_id)
                        if q_id not in agregaciones:
                            continue
                            
                        agg = agregaciones[q_id]
                        
                        # Validar si hay contenido (no nulo/vacío)
                        if val is None or val == "":
                            continue
                            
                        agg['total_answered'] += 1
                        
                        # Agregación según tipo
                        if agg['type'] in ['multiple-choice', 'dropdown']:
                            # val es un string
                            agg['counts'][val] = agg['counts'].get(val, 0) + 1
                        elif agg['type'] in ['checkboxes', 'checkbox', 'muscle-map', 'hand-map']:
                            # val es una lista (para checkbox y mapas)
                            if isinstance(val, list):
                                for item in val:
                                    if item:
                                        agg['counts'][item] = agg['counts'].get(item, 0) + 1
                            elif isinstance(val, str) and val:
                                agg['counts'][val] = agg['counts'].get(val, 0) + 1
                        elif agg['type'] == 'rating':
                            # val es un int
                            try:
                                score = int(val)
                                agg['rating_sum'] += score
                                agg['rating_counts'][score] = agg['rating_counts'].get(score, 0) + 1
                            except: pass
                        elif agg['type'] in ['short-text', 'long-text', 'email', 'number', 'phone', 'date']:
                            # Guardar las últimas 10 respuestas de texto
                            if len(agg['text_responses']) < 10:
                                agg['text_responses'].append(val)
            except Exception as e:
                app.logger.error(f"Error procesando respuesta {r_entry.ID}: {e}")

        # Formatear para el frontend
        for q_id, agg in agregaciones.items():
            formatted_q = {
                'id': agg['id'],
                'title': agg['title'],
                'type': agg['type'],
                'total_answered': agg['total_answered']
            }
            
            if agg['type'] in ['multiple-choice', 'dropdown', 'checkboxes', 'checkbox', 'muscle-map', 'hand-map']:
                formatted_q['data'] = agg['counts']
            elif agg['type'] == 'rating':
                formatted_q['average'] = round(agg['rating_sum'] / agg['total_answered'], 2) if agg['total_answered'] > 0 else 0
                formatted_q['distribution'] = agg['rating_counts']
            elif agg['type'] in ['short-text', 'long-text', 'email', 'number', 'phone', 'date']:
                formatted_q['responses'] = agg['text_responses']
                
            stats['questions'].append(formatted_q)
            
        return jsonify(stats)


@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    enviado = False
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        mensaje = request.form.get('mensaje')
        
        app.logger.info(f"Nuevo mensaje de contacto — Nombre: {nombre} | Email: {email}")
        app.logger.debug(f"Mensaje: {mensaje}")
        
        enviado = True
    return render_template('contacto.html', enviado=enviado, current_page='contacto')


@app.route('/api/exportar-gmail/<int:form_id>', methods=['POST'])
def exportar_gmail(form_id):
    """Enviar respuestas del formulario por Gmail"""
    user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))
    
    if not user_id or not is_admin:
        return jsonify({'error': 'No autorizado'}), 403

    recipient_email = request.json.get('email')
    if not recipient_email or not is_valid_email(recipient_email):
        return jsonify({'error': 'Email de destino no válido'}), 400

    # 1. Obtener datos (mismo proceso que CSV)
    with get_db_session() as db_session:
        formulario = db_session.query(Formulario).filter(Formulario.ID == form_id).first()
        if not formulario:
            return jsonify({'error': 'Formulario no encontrado'}), 404

    # 2. Buscar respuestas
    with get_db_session() as db_session:
        respuestas_db = db_session.query(Respuesta).filter(Respuesta.form_id == form_id).all()
    
    if not respuestas_db:
        return jsonify({'error': 'No hay respuestas para enviar'}), 404

    # 3. Construir cuerpo del mensaje (resumen simple)
    cuerpo = f"Resumen de respuestas para el formulario: {formulario.nombre}\n\n"
    cuerpo += f"Total de respuestas: {len(respuestas_db)}\n\n"
    cuerpo += "Para ver el detalle completo, por favor consulte el panel de administración."

    # 4. Enviar Email
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.environ.get('GMAIL_USER')
    sender_password = os.environ.get('GMAIL_APP_PASSWORD')

    if not sender_email or not sender_password:
        return jsonify({'error': 'Configuración de Gmail faltante en .env (GMAIL_USER, GMAIL_APP_PASSWORD)'}), 500

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"Respuestas Formulario: {formulario.nombre}"
        msg.attach(MIMEText(cuerpo, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        return jsonify({'success': True, 'message': 'Email enviado correctamente'}), 200
    except Exception as e:
        app.logger.error(f"Error enviando email: {e}")
        return jsonify({'error': f'Error al enviar el email: {str(e)}'}), 500


@app.route("/api/formularios/<int:form_id>/versiones", methods=['GET'])
def get_form_versions(form_id):
    """Listar todas las versiones guardadas de un formulario"""
    user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))
    
    if not user_id or not is_admin:
        return jsonify({'error': 'No autorizado'}), 401
        
    form_versions_dir = os.path.join(VERSIONS_DIR, str(form_id))
    if not os.path.exists(form_versions_dir):
        return jsonify([])
        
    versiones = []
    for f in os.listdir(form_versions_dir):
        if f.startswith('v_') and f.endswith('.json'):
            path = os.path.join(form_versions_dir, f)
            stats = os.stat(path)
            # Extraer fecha del nombre del archivo v_YYYYMMDD_HHMMSS_...
            try:
                date_str = f.split('_')[1] + '_' + f.split('_')[2]
                fecha_obj = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                fecha_formateada = fecha_obj.strftime("%d/%m/%Y %H:%M:%S")
            except:
                fecha_formateada = datetime.fromtimestamp(stats.st_mtime).strftime("%d/%m/%Y %H:%M:%S")
                
            versiones.append({
                'filename': f,
                'fecha': fecha_formateada,
                'size': stats.st_size
            })
            
    # Ordenar por más reciente
    versiones.sort(key=lambda x: x['filename'], reverse=True)
    return jsonify(versiones)


@app.route("/api/formularios/<int:form_id>/restaurar", methods=['POST'])
def restore_form_version(form_id):
    """Restaurar una versión específica de un formulario"""
    user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))
    
    if not user_id or not is_admin:
        return jsonify({'error': 'No autorizado'}), 401
        
    data = request.get_json()
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': 'Nombre de archivo no proporcionado'}), 400
        
    # Validar que el archivo pertenece a este formulario y no es path traversal
    safe_filename = secure_filename(filename)
    ruta_version = os.path.join(VERSIONS_DIR, str(form_id), safe_filename)
    
    if not os.path.exists(ruta_version):
        return jsonify({'error': 'Versión no encontrada'}), 404
        
    with get_db_session() as db_session:
        formulario = db_session.query(Formulario).filter(Formulario.ID == form_id).first()
        if not formulario:
            return jsonify({'error': 'Formulario no encontrado'}), 404
            
        try:
            # Restaurar: copiar el archivo de versión sobre el original
            filename = os.path.basename(formulario.ruta_form)
            ruta_json = os.path.join(FORMS_DIR, filename)
            shutil.copy2(ruta_version, ruta_json)
            
            # Actualizar fecha de modificación en BD
            formulario.fecha_mod = _utcnow_iso()
            db_session.commit()
            
            return jsonify({'success': True, 'mensaje': 'Versión restaurada correctamente'})

        except Exception as e:
            app.logger.error(f"Error restaurando versión: {e}")
            return jsonify({'error': 'Error al restaurar la versión'}), 500


@app.route("/api/formularios/<int:form_id>/versiones", methods=['DELETE'])
def delete_form_versions(form_id):
    """Limpiar todo el historial de versiones de un formulario"""
    user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))
    
    if not user_id or not is_admin:
        return jsonify({'error': 'No autorizado'}), 401
        
    form_versions_dir = os.path.join(VERSIONS_DIR, str(form_id))
    if os.path.exists(form_versions_dir):
        try:
            shutil.rmtree(form_versions_dir)
            return jsonify({'success': True, 'mensaje': 'Historial limpiado correctamente'})
        except Exception as e:
            app.logger.error(f"Error limpiando historial de versiones: {e}")
            return jsonify({'error': 'Error al limpiar el historial'}), 500
    else:
        return jsonify({'success': True, 'mensaje': 'No hay historial que limpiar'})

@app.route("/admin/mantenimiento")
def admin_mantenimiento():
    """Herramienta para detectar y limpiar archivos huérfanos (Forms y Respuestas)"""
    user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))
    
    if not user_id or not is_admin:
        return redirect(url_for('index'))

    do_delete = request.args.get('confirm_delete') == 'true'
    
    orphans_forms = []
    orphans_resps = []
    errors = []
    deleted_count = 0

    with get_db_session() as db_session:
        # 1. Obtener todas las rutas válidas de la BD (adaptado para ser portable)
        db_forms_paths = set()
        for f in db_session.query(Formulario.ruta_form).all():
            if f.ruta_form:
                fname = os.path.basename(f.ruta_form)
                db_forms_paths.add(os.path.normpath(os.path.join(FORMS_DIR, fname)))
        db_resps_paths = set()
        resp_dir_base = os.path.join(BASE_DIR, "respuestas")
        for r in db_session.query(Respuesta.ruta_respuesta).all():
            if r.ruta_respuesta:
                fname = os.path.basename(r.ruta_respuesta)
                db_resps_paths.add(os.path.normpath(os.path.join(resp_dir_base, fname)))

        # 2. Escanear carpeta de formularios
        if os.path.exists(FORMS_DIR):
            for filename in os.listdir(FORMS_DIR):
                if filename.endswith(".json"):
                    full_path = os.path.normpath(os.path.join(FORMS_DIR, filename))
                    if full_path not in db_forms_paths:
                        orphans_forms.append(full_path)
        
        # 3. Escanear carpeta de respuestas
        respuestas_dir = os.path.join(BASE_DIR, "respuestas")
        if os.path.exists(respuestas_dir):
            for filename in os.listdir(respuestas_dir):
                if filename.endswith(".json"):
                    full_path = os.path.normpath(os.path.join(respuestas_dir, filename))
                    if full_path not in db_resps_paths:
                        orphans_resps.append(full_path)

        # 4. Escanear Avatares Huérfanos (ID no existe en DB)
        orphans_avatars = []
        db_user_ids = {u.ID for u in db_session.query(Usuario.ID).all()}
        if os.path.exists(AVATARS_DIR):
            for filename in os.listdir(AVATARS_DIR):
                if filename.startswith("avatar_"):
                    try:
                        # Extraer ID: avatar_7.jpg -> 7
                        parts = filename.split('_')
                        if len(parts) > 1:
                            uid_str = parts[1].split('.')[0]
                            uid = int(uid_str)
                            if uid not in db_user_ids:
                                orphans_avatars.append(os.path.normpath(os.path.join(AVATARS_DIR, filename)))
                    except:
                        orphans_avatars.append(os.path.normpath(os.path.join(AVATARS_DIR, filename)))

        # 5. Escanear Imágenes de Formulario Huérfanas (No usadas en ningún JSON de formulario)
        orphans_images = []
        used_images = set()
        
        # Primero leer todos los JSON registrados para ver qué imágenes usan
        for f_path in db_forms_paths:
            if os.path.exists(f_path):
                try:
                    with open(f_path, 'r', encoding='utf-8') as f_json:
                        fdata = json.load(f_json)
                        for q in fdata.get('questions', []):
                            img_url = q.get('image')
                            if img_url and 'static/uploads/form_images/' in img_url:
                                used_images.add(img_url.split('/')[-1])
                except: pass

        if os.path.exists(IMG_UPLOADS_DIR):
            for filename in os.listdir(IMG_UPLOADS_DIR):
                if filename not in used_images:
                    orphans_images.append(os.path.normpath(os.path.join(IMG_UPLOADS_DIR, filename)))

        # 6. Ejecutar borrado si se solicitó
        if do_delete:
            for p in orphans_forms + orphans_resps + orphans_avatars + orphans_images:
                try:
                    if os.path.exists(p):
                        os.remove(p)
                        deleted_count += 1
                except Exception as e:
                    errors.append(f"Error borrando {os.path.basename(p)}: {str(e)}")

    return render_template('mantenimiento.html', 
                          orphans_forms=[os.path.basename(p) for p in orphans_forms],
                          orphans_resps=[os.path.basename(p) for p in orphans_resps],
                          orphans_avatars=[os.path.basename(p) for p in orphans_avatars],
                          orphans_images=[os.path.basename(p) for p in orphans_images],
                          deleted_count=deleted_count,
                          errors=errors,
                          is_admin=is_admin)

@app.route('/usuarios')
def usuarios():
    """Panel de administración de usuarios"""
    user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))
    
    if not user_id or not is_admin:
        return redirect(url_for('index'))

    # Parámetro de búsqueda
    q = request.args.get('q', '').strip()
        
    with get_db_session() as db_session:
        # Consulta para obtener usuarios y contar sus formularios y respuestas
        # Contamos usando subqueries para evitar multiplicaciones cartesianas
        from sqlalchemy import literal_column
        
        subq_forms = db_session.query(
            Formulario.user_id, 
            func.count(Formulario.ID).label('num_formularios')
        ).group_by(Formulario.user_id).subquery()
        
        subq_resps = db_session.query(
            Respuesta.user_id, 
            func.count(Respuesta.ID).label('num_respuestas')
        ).group_by(Respuesta.user_id).subquery()

        users_query = db_session.query(
            Usuario,
            func.coalesce(subq_forms.c.num_formularios, 0).label('forms_count'),
            func.coalesce(subq_resps.c.num_respuestas, 0).label('resps_count')
        ).outerjoin(subq_forms, Usuario.ID == subq_forms.c.user_id)\
         .outerjoin(subq_resps, Usuario.ID == subq_resps.c.user_id)

        if q:
            users_query = users_query.filter(
                or_(
                    Usuario.nombre.ilike(f"%{q}%"),
                    Usuario.correo.ilike(f"%{q}%")
                )
            )

        users_query = users_query.order_by(Usuario.ID.asc())
         
        users_data = users_query.all()
        
        # Formatear para template
        user_list = []
        for user_obj, f_count, r_count in users_data:
            user_list.append({
                'ID': user_obj.ID,
                'nombre': user_obj.nombre,
                'correo': user_obj.correo or '—',
                'admin': user_obj.admin,
                'formularios_count': f_count,
                'respuestas_count': r_count
            })

    return render_template('usuarios.html', usuarios=user_list, current_user_id=user_id, current_page='usuarios', q=q)


@app.route('/api/usuarios/<int:target_user_id>/toggle-admin', methods=['POST'])
def toggle_admin(target_user_id):
    """Activar/desactivar privilegios de administrador para un usuario"""
    current_user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))
    
    if not current_user_id or not is_admin:
        return jsonify({'error': 'No autorizado'}), 401
        
    # Impedir que un admin se quite los permisos a sí mismo por error
    if current_user_id == target_user_id:
        return jsonify({'error': 'No puedes modificar tus propios permisos de administrador.'}), 400
        
    with get_db_session() as db_session:
        usuario = db_session.query(Usuario).filter(Usuario.ID == target_user_id).first()
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
            
        # Toggle
        nuevo_estado = 0 if usuario.admin == 1 else 1
        usuario.admin = nuevo_estado
        db_session.commit()
        
        return jsonify({'success': True, 'nuevo_estado': nuevo_estado, 'mensaje': 'Privilegios actualizados'})

@app.route('/api/usuarios/<int:target_user_id>/delete', methods=['POST'])
def delete_user(target_user_id):
    """Eliminar un usuario del sistema (solo admin)"""
    current_user_id = session.get('user_id')
    is_admin = bool(session.get('is_admin', False))
    
    if not current_user_id or not is_admin:
        return jsonify({'error': 'No autorizado'}), 401
        
    if current_user_id == target_user_id:
        return jsonify({'error': 'No puedes eliminarte a ti mismo.'}), 400
        
    with get_db_session() as db_session:
        usuario = db_session.query(Usuario).filter(Usuario.ID == target_user_id).first()
        if not usuario:
            return jsonify({'error': 'Usuario no encontrado'}), 404
            
        try:
            # 1. Eliminar archivos de respuestas de este usuario
            from sqlalchemy import and_
            resps = db_session.query(Respuesta).filter(Respuesta.user_id == target_user_id).all()
            for r in resps:
                if r.ruta_respuesta:
                    fname = os.path.basename(r.ruta_respuesta)
                    ruta = os.path.join(BASE_DIR, "respuestas", fname)
                    if os.path.exists(ruta):
                        try:
                            os.remove(ruta)
                        except:
                            pass

            # 2. Eliminar archivos de formularios de este usuario
            forms_user = db_session.query(Formulario).filter(Formulario.user_id == target_user_id).all()
            for f in forms_user:
                if f.ruta_form:
                    fname = os.path.basename(f.ruta_form)
                    ruta = os.path.join(FORMS_DIR, fname)
                    if os.path.exists(ruta):
                        try:
                            os.remove(ruta)
                        except:
                            pass
                # Limpiar carpetas de versiones si existen
                v_dir = os.path.join(VERSIONS_DIR, str(f.ID))
                if os.path.exists(v_dir):
                    try:
                        shutil.rmtree(v_dir)
                    except:
                        pass
            
            # 3. Eliminar Avatar si existe
            prefix = f"avatar_{target_user_id}."
            try:
                for f in os.listdir(AVATARS_DIR):
                    if f.startswith(prefix):
                        os.remove(os.path.join(AVATARS_DIR, f))
            except:
                pass

            # 4. Eliminar de la base de datos (cascada manual o DB)
            # Como usamos relationships con backrefs/back_populates pero sin cascada explicativa en delete-orphan para todo, 
            # nos aseguramos de limpiar lo asociado si la DB no lo hace
            # En Usuario no definimos cascade, así que lo hacemos explícito para mayor seguridad si no hay FK restrictoras
            
            # Borrar respuestas y formularios primero (si no hay cascade en motor DB)
            db_session.query(Respuesta).filter(Respuesta.user_id == target_user_id).delete()
            db_session.query(Formulario).filter(Formulario.user_id == target_user_id).delete()
            
            db_session.delete(usuario)
            db_session.commit()
            
            return jsonify({'success': True, 'mensaje': f'Usuario {usuario.nombre} eliminado correctamente'})
        except Exception as e:
            db_session.rollback()
            app.logger.error(f"Error eliminando usuario: {e}")
            return jsonify({'error': 'Error interno al eliminar el usuario'}), 500

if __name__ == '__main__':
    app.run(debug=True)
