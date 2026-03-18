#!/usr/bin/env python3
"""
Script para migrar datos de SQLite a Supabase
"""

import json
import os
import sqlite3
from supabase import create_client, Client
from dotenv import load_dotenv
import sys

load_dotenv()

# Configuración
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
DB_PATH = 'forms.db'

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Configura SUPABASE_URL y SUPABASE_SERVICE_KEY en .env")
    sys.exit(1)

# Conectar a Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_tables():
    """Crear tablas en Supabase si no existen"""
    print("🔧 Creando tablas en Supabase...")
    
    # Tabla de usuarios
    users_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin BOOLEAN DEFAULT FALSE,
        email TEXT,
        google_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Tabla de formularios
    forms_sql = """
    CREATE TABLE IF NOT EXISTS forms (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        created_by INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Tabla de respuestas
    responses_sql = """
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY,
        form_id INTEGER REFERENCES forms(id),
        user_id INTEGER REFERENCES users(id),
        response_data JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        supabase.rpc('exec_sql', {'sql': users_sql}).execute()
        supabase.rpc('exec_sql', {'sql': forms_sql}).execute()
        supabase.rpc('exec_sql', {'sql': responses_sql}).execute()
        print("✅ Tablas creadas exitosamente")
    except Exception as e:
        print(f"⚠️  Las tablas podrían ya existir: {e}")

def migrate_users():
    """Migrar usuarios de SQLite a Supabase"""
    print("👥 Migrando usuarios...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, username, password_hash, is_admin, email, google_id FROM users")
        users = cursor.fetchall()
        
        for user in users:
            user_data = {
                'id': user[0],
                'username': user[1],
                'password_hash': user[2],
                'is_admin': bool(user[3]),
                'email': user[4],
                'google_id': user[5]
            }
            
            try:
                supabase.table('users').insert(user_data).execute()
                print(f"  ✅ Usuario {user[1]} migrado")
            except Exception as e:
                print(f"  ⚠️  Usuario {user[1]} podría ya existir: {e}")
                
    except sqlite3.Error as e:
        print(f"❌ Error leyendo usuarios: {e}")
    finally:
        conn.close()

def migrate_forms():
    """Migrar formularios JSON a Supabase"""
    print("📋 Migrando formularios...")
    
    forms_dir = 'formularios'
    if not os.path.exists(forms_dir):
        print("⚠️  Directorio 'formularios' no encontrado")
        return
    
    # Leer usuarios para mapear created_by
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users")
    user_map = {username: id for id, username in cursor.fetchall()}
    conn.close()
    
    for filename in os.listdir(forms_dir):
        if filename.endswith('.json') and filename != 'versiones':
            filepath = os.path.join(forms_dir, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                form_data = json.load(f)
            
            # Extraer información del formulario
            form_name = form_data.get('title', filename.replace('.json', ''))
            form_description = form_data.get('description', '')
            
            # Intentar determinar el creador (por defecto admin)
            created_by = 1  # ID del admin por defecto
            
            form_record = {
                'name': form_name,
                'description': form_description,
                'created_by': created_by
            }
            
            try:
                result = supabase.table('forms').insert(form_record).execute()
                form_id = result.data[0]['id']
                print(f"  ✅ Formulario '{form_name}' migrado con ID {form_id}")
                
                # Guardar JSON completo en Supabase Storage
                upload_form_json(form_id, filename, form_data)
                
            except Exception as e:
                print(f"  ❌ Error migrando formulario {filename}: {e}")

def upload_form_json(form_id, filename, form_data):
    """Subir JSON del formulario a Supabase Storage"""
    try:
        # Crear bucket si no existe
        storage_path = f"formularios/{form_id}_{filename}"
        
        # Subir archivo JSON
        json_content = json.dumps(form_data, ensure_ascii=False, indent=2)
        supabase.storage.from_('forms').upload(
            storage_path,
            json_content,
            {'content-type': 'application/json'}
        )
        print(f"    📁 JSON subido a storage: {storage_path}")
        
    except Exception as e:
        print(f"    ⚠️  Error subiendo JSON: {e}")

def migrate_responses():
    """Migrar respuestas de SQLite a Supabase"""
    print("📝 Migrando respuestas...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, form_id, user_id, response_data, created_at FROM responses")
        responses = cursor.fetchall()
        
        for response in responses:
            response_data = {
                'id': response[0],
                'form_id': response[1],
                'user_id': response[2],
                'response_data': json.loads(response[3]) if response[3] else {},
                'created_at': response[4]
            }
            
            try:
                supabase.table('responses').insert(response_data).execute()
                print(f"  ✅ Respuesta {response[0]} migrada")
            except Exception as e:
                print(f"  ⚠️  Respuesta {response[0]} podría ya existir: {e}")
                
    except sqlite3.Error as e:
        print(f"❌ Error leyendo respuestas: {e}")
    finally:
        conn.close()

def main():
    """Función principal de migración"""
    print("🚀 Iniciando migración a Supabase...")
    
    if not os.path.exists(DB_PATH):
        print("❌ Error: No se encuentra forms.db")
        sys.exit(1)
    
    try:
        # 1. Crear tablas
        create_tables()
        
        # 2. Migrar usuarios
        migrate_users()
        
        # 3. Migrar formularios
        migrate_forms()
        
        # 4. Migrar respuestas
        migrate_responses()
        
        print("\n✅ ¡Migración completada exitosamente!")
        print("\n📋 Próximos pasos:")
        print("1. Configura las variables de entorno en Render")
        print("2. Verifica los datos en el dashboard de Supabase")
        print("3. Actualiza app.py para usar Supabase")
        
    except Exception as e:
        print(f"\n❌ Error en migración: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
