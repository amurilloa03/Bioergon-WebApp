#!/usr/bin/env python3
"""
Migración vía SDK (HTTPS): SQLite -> Supabase REST API (Dinámico)
Este script evita errores de "No such column" detectando qué hay en tu SQLite.
"""

import os
import sqlite3
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import sys

# Cargar variables (.env)
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
DB_PATH = 'forms.db'

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Faltan SUPABASE_URL o SUPABASE_SERVICE_KEY en el .env")
    sys.exit(1)

# Conectar a Supabase vía HTTPS
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def migrate_table(cursor_local, table_name):
    print(f"📦 Procesando tabla: {table_name}...")
    
    # 1. Obtener columnas reales de tu SQLite local
    try:
        cursor_local.execute(f"PRAGMA table_info(\"{table_name}\")")
        columns_info = cursor_local.fetchall()
        if not columns_info:
            print(f"  ⚠️ La tabla {table_name} no existe en SQLite. Saltando.")
            return
        
        col_names = [c[1] for c in columns_info]
        # Crear consulta segura (ignorando columnas que no existan)
        query = f"SELECT {', '.join([f'\"{c}\"' for c in col_names])} FROM \"{table_name}\""
        cursor_local.execute(query)
        rows = cursor_local.fetchall()

        if not rows:
            print(f"  ℹ️ La tabla {table_name} está vacía.")
            return

        # 2. Subir cada fila a Supabase
        count = 0
        for row in rows:
            # Crear diccionario dinámico: {"ID": 1, "nombre": "...", ...}
            data = {col_names[i]: row[i] for i in range(len(col_names))}
            
            # Limpiar datos para evitar conflictos (ej: admin 0/1 boolean)
            if "admin" in data and data["admin"] is not None:
                data["admin"] = int(data["admin"])
            
            # Subir a Supabase
            try:
                supabase.table(table_name).upsert(data).execute()
                count += 1
            except Exception as e:
                print(f"  ❌ Error en fila de {table_name} (ID {data.get('ID')}): {e}")

        print(f"  ✅ {count} registros sincronizados en {table_name}.")

    except Exception as e:
        print(f"  ❌ Fallo crítico al procesar {table_name}: {e}")

def run_migration():
    if not os.path.exists(DB_PATH):
        print(f"❌ No se encontró {DB_PATH}")
        return

    print("🚀 Iniciando migración dinámica vía SDK (HTTPS)...")
    
    conn_local = sqlite3.connect(DB_PATH)
    cursor_local = conn_local.cursor()

    try:
        # Migramos en el orden correcto por las referencias
        migrate_table(cursor_local, "Usuario")
        migrate_table(cursor_local, "TiposPreguntas")
        migrate_table(cursor_local, "Formularios")
        migrate_table(cursor_local, "Respuestas")
        
        print("\n🎉 ¡DATOS LOCALES MIGRADOS EXITOSAMENTE!")
        print("Tu web en Render ya puede mostrar toda la información.")

    except Exception as e:
        print(f"\n❌ Error catastrófico: {e}")
    finally:
        conn_local.close()

if __name__ == "__main__":
    run_migration()
