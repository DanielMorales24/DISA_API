from fastapi import FastAPI, HTTPException, Query
import pyodbc
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import base64
from typing import Optional, List

app = FastAPI(
    title="API DISA",
    description="API para consultar artículos y categorías de la base de datos DISA",
    version="1.0.0",
    contact={
        "name": "Daniel Morales",
        "email": "danielmorales0924@gmail.com",
    },
)

# Configuración CORS segura para WebFlow
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://distribuidora-industrial-net.webflow.io",  # Tu sitio WebFlow
        "http://localhost:3000",                           # Desarrollo frontend local
        "http://127.0.0.1:3000"                            # Alternativa local
    ],
    allow_methods=["GET"],  # Solo permitimos GET según tu API actual
    allow_headers=[
        "Content-Type",
        "Accept",
        "Origin"
    ],
    allow_credentials=False,  # No necesario para API de solo lectura
    max_age=600  # Cachear configuración CORS por 10 minutos
)

# Configuración de conexión
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DISA68;"
    "DATABASE=Disa;"
    "UID=daniel;"
    "PWD=Web25;"
)

def convertir_campos_binarios(articulo):
    """Convierte campos binarios a Base64 y maneja valores NULL"""
    for field in articulo:
        if isinstance(articulo[field], (bytes, bytearray)):
            articulo[field] = base64.b64encode(articulo[field]).decode('ascii')
        elif articulo[field] is None:
            articulo[field] = None
    return articulo

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API DISA - Bienvenido</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; color: #333; }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            .endpoint { background: #f8f9fa; border-left: 4px solid #3498db; padding: 10px 15px; margin: 15px 0; border-radius: 0 4px 4px 0; }
            a { color: #3498db; text-decoration: none; font-weight: bold; }
            a:hover { text-decoration: underline; }
            .footer { margin-top: 30px; font-size: 0.9em; color: #7f8c8d; }
            code { background: #f0f0f0; padding: 2px 4px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>Bienvenido a la API de DISA</h1>
        <p>Esta API proporciona acceso a los artículos y categorías de la base de datos DISA.</p>
        
        <h2>Endpoints disponibles:</h2>
        
        <div class="endpoint">
            <h3><a href="/articulos" target="_blank">Todos los artículos</a></h3>
            <p><strong>Ruta:</strong> <code>/articulos</code></p>
            <p>Devuelve todos los artículos de la vista Vista_Maestro_Articulo</p>
        </div>
        
        <div class="endpoint">
            <h3><a href="/articulos/1PL" target="_blank">Artículo específico</a></h3>
            <p><strong>Ruta:</strong> <code>/articulos/&#123;id&#125;</code></p>
            <p>Devuelve un artículo específico por su ID (ejemplo con ID=1PL)</p>
        </div>
        
        <div class="endpoint">
            <h3><a href="/articulos/por-categoria/?categoria_id=044" target="_blank">Artículos por categoría</a></h3>
            <p><strong>Ruta:</strong> <code>/articulos/por-categoria/?categoria_id=&#123;id&#125;</code></p>
            <p><strong>O:</strong> <code>/articulos/por-categoria/?categoria_nombre=&#123;nombre&#125;</code></p>
            <p>Devuelve artículos filtrados por ID o nombre de categoría</p>
        </div>
        
        <div class="endpoint">
            <h3><a href="/categorias" target="_blank">Categorías</a></h3>
            <p><strong>Ruta:</strong> <code>/categorias</code></p>
            <p>Devuelve una lista de categorías disponibles</p>
        </div>
        
        <div class="endpoint">
            <h3><a href="/docs" target="_blank">Documentación interactiva</a></h3>
            <p><strong>Ruta:</strong> <code>/docs</code></p>
            <p>Documentación Swagger UI para probar la API interactivamente</p>
        </div>
        
        <div class="footer">
            <p>API desarrollada por Daniel Morales - © 2025</p>
        </div>
    </body>
    </html>
    """

# Endpoints (manteniendo los existentes y agregando el nuevo)
@app.get("/articulos", summary="Obtiene todos los artículos", response_model=List[dict], tags=["Artículos"])
async def get_articulos():
    """Devuelve todos los artículos de la base de datos"""
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Vista_Maestro_Articulo")
            columns = [column[0] for column in cursor.description]
            return [convertir_campos_binarios(dict(zip(columns, row))) for row in cursor.fetchall()]
    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")

@app.get("/articulos/{articulo_id}", summary="Obtiene un artículo específico", response_model=dict, tags=["Artículos"])
async def get_articulo(articulo_id: str):
    """Devuelve un artículo específico por su ID"""
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Vista_Maestro_Articulo WHERE Articulo = ?", articulo_id)
            columns = [column[0] for column in cursor.description]
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Artículo no encontrado")
            return convertir_campos_binarios(dict(zip(columns, row)))
    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")

@app.get("/articulos/por-categoria/", 
        summary="Filtra artículos por categoría", 
        response_model=List[dict],
        tags=["Artículos"])
async def get_articulos_por_categoria(
    categoria_id: Optional[str] = Query(None, description="ID de la categoría"),
    categoria_nombre: Optional[str] = Query(None, description="Nombre de la categoría")
):
    """Filtra artículos por ID o nombre de categoría"""
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM Vista_Maestro_Articulo"
            params = []
            
            if categoria_id:
                query += " WHERE Categoria = ?"
                params.append(categoria_id)
            elif categoria_nombre:
                query += " WHERE Nombre_Categoria = ?"
                params.append(categoria_nombre)
            
            cursor.execute(query, *params)
            columns = [column[0] for column in cursor.description]
            return [convertir_campos_binarios(dict(zip(columns, row))) for row in cursor.fetchall()]
    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")

@app.get("/categorias", summary="Obtiene lista de categorías", response_model=List[dict], tags=["Categorías"])
async def get_categorias():
    """Devuelve todas las categorías disponibles"""
    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT Categoria, Nombre_Categoria FROM Vista_Maestro_Articulo")
            return [{
                "id": row[0],
                "nombre": row[1],
                "url_articulos": f"/articulos/por-categoria/?categoria_id={row[0]}"
            } for row in cursor.fetchall()]
    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")