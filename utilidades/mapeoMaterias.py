import pandas as pd
import numpy as np
import re
import unicodedata
import warnings

warnings.filterwarnings('ignore')

def normalize_text(text):
    """
    Quita acentos y convierte a minúsculas para normalizar el texto.
    """
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8')
    return text

def asignar_categoria(materia_nombre):
    """
    Asigna una categoría basada en palabras clave.
    """
    categorias_map = {
        'Ciencias Básicas (STEM)': [
            'calculo', 'fisica', 'quimica', 'algebra', 'ecuaciones', 
            'matematicas', 'probabilidad', 'estadistica', 'termodinamica',
            'metodos numericos', 'geometria'
        ],
        'Computación y Software': [
            'programacion', 'software', 'base de datos', 'redes', 'web', 
            'sistemas', 'computacion', 'algoritmos', 'inteligencia artificial',
            'sistemas operativos', 'graficacion', 'ciberseguridad', 
            'arquitectura de computadoras', 'lenguajes y automatas', 
            'sistemas programables', 'lenguajes de interfaz',
            'estructura de datos', 'teoria general de sistemas', 'simulacion'
        ],
        'Economía y Administración': [
            'contabilidad', 'finanzas', 'economia', 'administracion', 
            'empresa', 'costos', 'mercadotecnia', 'proyectos', 'gestion',
            'recursos humanos', 'taller de administracion', 
            'formulacion y evaluacion de proyectos', 'ingenieria economica'
        ],
        'Ingeniería Aplicada': [
            'electrica', 'electronica', 'circuitos', 'mecanica', 'industrial',
            'dibujo', 'maquinas', 'control', 'telecomunicaciones', 'procesos',
            'automatizacion', 'manufactura', 'instrumentacion', 'mecanismos',
            'principios de electronica', 'ingenieria de control'
        ],
        'Formación General y Humanidades': [
            'etica', 'investigacion', 'desarrollo sustentable', 'ingles', 
            'comunicacion', 'expresion oral', 'humanidades', 'sociedad',
            'cultura', 'taller de expresion', 'fundamentos de investigacion',
            'comunicacion humana', 'desarrollo humano'
        ]
    }
    
    materia_normalized = normalize_text(materia_nombre)
    
    if not materia_normalized:
        return 'Por Clasificar'
    
    for categoria, keywords in categorias_map.items():
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', materia_normalized):
                return categoria
    
    return 'Especialidad / Otra'

if __name__ == '__main__':
    input_file = './sql/materias_sin_clasificacion.csv'
    output_file = 'mapeo_materias.csv'
    
    try:
        print(f"Cargando archivo de entrada: {input_file}...")
        df = pd.read_csv(input_file)
        
        if 'materia' in df.columns:
            print("Aplicando categorización...")
            df['categoria'] = df['materia'].apply(asignar_categoria)
            
            df_final_mapeo = df[['id_materia', 'categoria']].drop_duplicates().reset_index(drop=True)
            
            df_final_mapeo.to_csv(output_file, index=False)
            
            print("\n¡ÉXITO!")
            print(f"Archivo '{output_file}' creado en la misma carpeta.")
            print(f"El mapeo final contiene {len(df_final_mapeo)} materias únicas.")
            print("\nConteo de materias por categoría:")
            print(df_final_mapeo['categoria'].value_counts())
        else:
            print("Error: El archivo CSV no contiene la columna 'materia'.")
            
    except FileNotFoundError:
        print(f"ERROR: No se encontró el archivo '{input_file}'.")
        print("Asegúrate de que el script esté en la misma carpeta que tu CSV.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")