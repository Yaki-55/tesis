import os
import re
import pandas as pd
from collections import defaultdict

def analyze_student_graduation(root_directory):
    """
    Analiza los registros de estudiantes para identificar a aquellos que han completado
    los 10 semestres de su carrera dentro de un plazo de tiempo tolerable,
    considerando la estructura de carpetas 'Periodo_<num>/Carrera_<num>'.

    Args:
        root_directory (str): La ruta al directorio que contiene las carpetas de los periodos.
    """
    # --- CONFIGURACIÓN INICIAL ---
    period_order = [35, 36, 40, 39, 42, 43, 41, 46, 47, 44, 49, 50, 48, 53, 54, 51, 52, 56, 55, 58, 59, 57, 61]
    period_order_name = [
        "2017-2018A", "2017-2018B", "2017-2018V", "2018-2019A", "2018-2019B", "2018-2019V",
        "2019-2020A", "2019-2020B", "2019-2020V", "2020-2021A", "2020-2021B", "2020-2021V",
        "2021-2022A", "2021-2022B", "2021-2022V", "2022-2023A", "2022-2023B", "2022-2023V",
        "2023-2024A", "2023-2024B", "2023-2024V", "2024-2025A", "2024-2025B"
    ]
    period_map = dict(zip(period_order, period_order_name))

    # Estructura para guardar el progreso: {matricula: {carrera: {semestre: primer_periodo}}}
    student_progress = defaultdict(lambda: defaultdict(dict))

    # Patrones de REGEX actualizados
    # Para extraer el ID de la carpeta de la carrera
    career_folder_pattern = re.compile(r'Carrera_(\d+)')
    # Para extraer información del nombre del archivo
    file_pattern = re.compile(r'periodo(\d+)carrera(\d+)semestre(\d+)\.csv')

    print("Iniciando el procesamiento de archivos...")

    # --- 1. RECOPILACIÓN DE DATOS ---
    for root, _, files in os.walk(root_directory):
        # Intentamos extraer el ID de la carrera desde la ruta de la carpeta actual
        career_match = career_folder_pattern.search(root)
        
        # Solo procesamos archivos si estamos dentro de una carpeta 'Carrera_<numero>'
        if career_match:
            career_id = int(career_match.group(1))
            
            for file in files:
                if file.endswith('.csv'):
                    file_match = file_pattern.match(file)
                    if file_match:
                        period_id = int(file_match.group(1))
                        semester = int(file_match.group(3))
                        
                        file_path = os.path.join(root, file)
                        try:
                            df = pd.read_csv(file_path)
                            if 'matricula_hash' not in df.columns:
                                print(f"ADVERTENCIA: El archivo {file_path} no tiene la columna 'matricula_hash'. Omitiendo.")
                                continue

                            students_in_file = df['matricula_hash'].unique()

                            for student_hash in students_in_file:
                                if semester not in student_progress[student_hash][career_id]:
                                    student_progress[student_hash][career_id][semester] = period_id

                        except Exception as e:
                            print(f"Error al procesar el archivo {file_path}: {e}")

    print("Procesamiento de archivos completado. Analizando trayectorias...")

    # --- 2. ANÁLISIS Y FILTRADO ---
    graduated_students = []
    
    MAX_REGULAR_PERIODS_ALLOWED = 10 + 4 # 10 periodos ideales + 2 años (4 periodos) de tolerancia

    for student_hash, careers_data in student_progress.items():
        for career_id, semester_data in careers_data.items():
            
            # Regla 1: ¿Completó todos los semestres del 1 al 10?
            if set(semester_data.keys()).issuperset(set(range(1, 11))):
                
                try:
                    start_period = semester_data[1]
                    end_period = semester_data[10]

                    start_index = period_order.index(start_period)
                    end_index = period_order.index(end_period)
                    
                    if start_index > end_index: continue

                    # Regla 2: ¿Terminó dentro de la tolerancia de tiempo?
                    relevant_period_names = period_order_name[start_index : end_index + 1]
                    regular_periods_count = sum(
                        1 for name in relevant_period_names if name.endswith('A') or name.endswith('B')
                    )

                    if regular_periods_count <= MAX_REGULAR_PERIODS_ALLOWED:
                        graduated_students.append(student_hash)
                        break
                
                except (ValueError, KeyError) as e:
                    print(f"ADVERTENCIA: Dato inconsistente para alumno {student_hash}. Error: {e}")

    # --- 3. RESULTADO FINAL ---
    print("\n--- Análisis Finalizado ---")
    print(f"✅ Total de alumnos identificados como graduados: {len(graduated_students)}")

    output_file = 'graduados.txt'
    with open(output_file, 'w') as f:
        for student_hash in graduated_students:
            f.write(f"{student_hash}\n")

    print(f"La lista de matrículas ha sido guardada en '{output_file}'")
    return graduated_students


# --- INSTRUCCIONES DE USO ---
# 1. Guarda este script en un archivo, por ejemplo, `analizar_graduados.py`.
# 2. Asegúrate de tener la librería pandas instalada (`pip install pandas`).
# 3. Organiza tus datos con la estructura de carpetas especificada.
# 4. Cambia el valor de 'ruta_a_tus_datos' a la ruta de la carpeta principal.

if __name__ == '__main__':
    # MODIFICAR ESTA LÍNEA con la ruta al directorio que contiene las carpetas de periodos.
    # Ejemplo de estructura de carpetas esperada:
    # ./datos_universidad/
    #   ├── Periodo_35/
    #   │   ├── Carrera_2/
    #   │   │   └── periodo35carrera2semestre1.csv
    #   │   └── Carrera_3/
    #   │       └── periodo35carrera3semestre1.csv
    #   └── Periodo_36/
    #       └── ...
    
    ruta_a_tus_datos = r"D:/TesisDB/CSV's"

    if not os.path.isdir(ruta_a_tus_datos):
        print(f"❌ ERROR: El directorio especificado '{ruta_a_tus_datos}' no existe.")
        print("Por favor, actualiza la variable 'ruta_a_tus_datos' con la ruta correcta.")
    else:
        lista_graduados = analyze_student_graduation(ruta_a_tus_datos)