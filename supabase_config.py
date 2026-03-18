"""
Configuración de Supabase para Bioergon
Reemplaza la configuración SQLAlchemy en app.py
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

load_dotenv()

class SupabaseConfig:
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.url or not self.key:
            raise RuntimeError("SUPABASE_URL y SUPABASE_SERVICE_KEY deben estar configurados")
        
        self.client: Client = create_client(self.url, self.key)
    
    def get_client(self) -> Client:
        return self.client

# Instancia global
supabase_config = SupabaseConfig()
supabase = supabase_config.get_client()

# Funciones de ayuda para reemplazar SQLAlchemy
def get_user_by_username(username):
    """Obtener usuario por username"""
    try:
        result = supabase.table('users').select('*').eq('username', username).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def get_user_by_id(user_id):
    """Obtener usuario por ID"""
    try:
        result = supabase.table('users').select('*').eq('id', user_id).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error getting user by id: {e}")
        return None

def create_user(username, password_hash, is_admin=False, email=None, google_id=None):
    """Crear nuevo usuario"""
    try:
        user_data = {
            'username': username,
            'password_hash': password_hash,
            'is_admin': is_admin,
            'email': email,
            'google_id': google_id
        }
        result = supabase.table('users').insert(user_data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

def get_all_users():
    """Obtener todos los usuarios"""
    try:
        result = supabase.table('users').select('*').execute()
        return result.data or []
    except Exception as e:
        print(f"Error getting all users: {e}")
        return []

def create_form(name, description, created_by):
    """Crear nuevo formulario"""
    try:
        form_data = {
            'name': name,
            'description': description,
            'created_by': created_by
        }
        result = supabase.table('forms').insert(form_data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error creating form: {e}")
        return None

def get_all_forms():
    """Obtener todos los formularios"""
    try:
        result = supabase.table('forms').select('*').execute()
        return result.data or []
    except Exception as e:
        print(f"Error getting all forms: {e}")
        return []

def get_form_by_id(form_id):
    """Obtener formulario por ID"""
    try:
        result = supabase.table('forms').select('*').eq('id', form_id).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error getting form by id: {e}")
        return None

def create_response(form_id, user_id, response_data):
    """Crear nueva respuesta"""
    try:
        response_record = {
            'form_id': form_id,
            'user_id': user_id,
            'response_data': response_data
        }
        result = supabase.table('responses').insert(response_record).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error creating response: {e}")
        return None

def get_responses_by_form(form_id):
    """Obtener respuestas de un formulario"""
    try:
        result = supabase.table('responses').select('*').eq('form_id', form_id).execute()
        return result.data or []
    except Exception as e:
        print(f"Error getting responses by form: {e}")
        return []

def get_responses_by_user(user_id):
    """Obtener respuestas de un usuario"""
    try:
        result = supabase.table('responses').select('*').eq('user_id', user_id).execute()
        return result.data or []
    except Exception as e:
        print(f"Error getting responses by user: {e}")
        return []

def get_all_responses():
    """Obtener todas las respuestas"""
    try:
        result = supabase.table('responses').select('*').execute()
        return result.data or []
    except Exception as e:
        print(f"Error getting all responses: {e}")
        return []

# Funciones para manejar JSON de formularios en Supabase Storage
def upload_form_json(form_id, filename, form_data):
    """Subir JSON de formulario a Supabase Storage"""
    try:
        storage_path = f"formularios/{form_id}_{filename}"
        json_content = json.dumps(form_data, ensure_ascii=False, indent=2)
        
        supabase.storage.from('forms').upload(
            storage_path,
            json_content,
            {'content-type': 'application/json'}
        )
        return storage_path
    except Exception as e:
        print(f"Error uploading form JSON: {e}")
        return None

def download_form_json(form_id, filename):
    """Descargar JSON de formulario desde Supabase Storage"""
    try:
        storage_path = f"formularios/{form_id}_{filename}"
        result = supabase.storage.from('forms').download(storage_path)
        return json.loads(result.decode('utf-8'))
    except Exception as e:
        print(f"Error downloading form JSON: {e}")
        return None

def list_form_files():
    """Listar todos los archivos de formularios en storage"""
    try:
        result = supabase.storage.from('forms').list('formularios/')
        return result or []
    except Exception as e:
        print(f"Error listing form files: {e}")
        return []
