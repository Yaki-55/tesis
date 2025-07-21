import psycopg2
import pandas as pd
import os
import hashlib

def get_db_connection():
    """
    Establece y devuelve una conexión a la base de datos PostgreSQL.
    """
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="NES",
            user="postgres",
            password="x"
        )
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def generate_grade_csvs(base_output_directory, period_limit=-1):
    """
    Genera archivos CSV de calificaciones por período, carrera y grupo,
    organizados en subcarpetas.

    Args:
        base_output_directory (str): La ruta del directorio base donde se crearán las carpetas de período.
        period_limit (int): Número máximo de períodos a procesar.
                            -1 para procesar todos los períodos.
    """
    conn = get_db_connection()
    if not conn:
        return

    if not os.path.exists(base_output_directory):
        os.makedirs(base_output_directory)
        print(f"Directorio base de salida creado: {base_output_directory}")
    else:
        print(f"Usando directorio base de salida existente: {base_output_directory}")

    try:
        cursor = conn.cursor()

        # 1. Obtener todos los id_periodo distintos de nes_grupos
        cursor.execute("SELECT DISTINCT id_periodo FROM nes_grupos ORDER BY id_periodo;")
        periods = [row[0] for row in cursor.fetchall()]

        if period_limit != -1 and period_limit > 0:
            periods = periods[:period_limit]

        print(f"Procesando {len(periods)} período(s).")

        for id_periodo in periods:
            # Crear subcarpeta para el período
            period_folder_name = f"Periodo_{id_periodo}"
            period_path = os.path.join(base_output_directory, period_folder_name)
            os.makedirs(period_path, exist_ok=True) # exist_ok=True evita errores si la carpeta ya existe

            print(f"\n--- Procesando Período: {id_periodo} (Guardando en: {period_path}) ---")

            # 2. Por cada id_periodo, obtener id_carrera y semestre distintos
            cursor.execute(
                """
                SELECT DISTINCT id_carrera, semestre
                FROM nes_grupos
                WHERE id_periodo = %s
                ORDER BY id_carrera, semestre;
                """,
                (id_periodo,)
            )
            career_semesters = cursor.fetchall()

            if not career_semesters:
                print(f"No se encontraron combinaciones de carrera/semestre para el período {id_periodo}.")
                continue

            for id_carrera, semestre in career_semesters:
                # Crear subcarpeta para la carrera dentro de la carpeta del período
                career_folder_name = f"Carrera_{id_carrera}"
                career_path = os.path.join(period_path, career_folder_name)
                os.makedirs(career_path, exist_ok=True) # exist_ok=True evita errores si la carpeta ya existe

                print(f"  Procesando Carrera: {id_carrera}, Semestre: {semestre} (Guardando en: {career_path})")

                # 3. Obtener todos los id_grupo que compartan id_periodo, id_carrera y semestre
                cursor.execute(
                    """
                    SELECT id_grupo
                    FROM nes_grupos
                    WHERE id_periodo = %s AND id_carrera = %s AND semestre = %s;
                    """,
                    (id_periodo, id_carrera, semestre)
                )
                group_ids = [row[0] for row in cursor.fetchall()]

                if not group_ids:
                    print(f"    No se encontraron grupos para la combinación {id_periodo}-{id_carrera}-{semestre}.")
                    continue

                # Convertir la lista de id_grupo a una tupla para usar con IN en la consulta SQL
                group_ids_tuple = tuple(group_ids)

                # 4. Realizar la búsqueda en nes_calificaciones
                query = f"""
                SELECT
                    nc.matricula,
                    nc.id_grupo,
                    nc.id_materia,
                    nc.p1, nc.p2, nc.p3, nc.o, nc.pf, nc.e1, nc.e2, nc.esp
                FROM
                    nes_calificaciones nc
                JOIN
                    nes_grupos ng ON nc.id_grupo = ng.id_grupo
                JOIN
                    nes_materias nm ON nc.id_materia = nm.id_materia AND nc.id_grupo = nm.id_grupo
                WHERE
                    nc.id_grupo IN %s;
                """
                df = pd.read_sql_query(query, conn, params=(group_ids_tuple,))

                if not df.empty:
                    # Aplicar la función hash a la columna 'matricula'
                    df['matricula_hash'] = df['matricula'].astype(str).apply(
                        lambda x: hashlib.sha256(x.encode('utf-8')).hexdigest()
                    )
                    # Eliminar la columna 'matricula' original para anonimizar
                    df = df.drop(columns=['matricula'])
                    # 5. Guardar la información en un archivo CSV
                    file_name = f"periodo{id_periodo}carrera{id_carrera}semestre{semestre}.csv"
                    # Usar os.path.join para construir la ruta completa incluyendo las subcarpetas
                    full_path = os.path.join(career_path, file_name)
                    df.to_csv(full_path, index=False)
                    print(f"    Archivo '{file_name}' generado exitosamente en '{career_path}' con {len(df)} registros.")
                else:
                    print(f"    No se encontraron calificaciones para la combinación {id_periodo}-{id_carrera}-{semestre}.")

    except Exception as e:
        print(f"Error durante la generación de CSVs: {e}")
    finally:
        if conn:
            conn.close()
            print("Conexión a la base de datos cerrada.")

if __name__ == "__main__":
    num_periodos_a_procesar = -1 # -1 todos, n>0 para cualquier otro numero
    output_folder = r"D:/TesisDB/CSV's"


    print("Iniciando la generación de archivos CSV de calificaciones...")
    generate_grade_csvs(base_output_directory=output_folder, period_limit=num_periodos_a_procesar)
    print("\nProceso de generación de CSVs completado.")