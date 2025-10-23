import pandas as pd
import unicodedata
import re

file_path = "./sql/materias_sin_clasificacion.csv"
try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    print(f"ERROR: No se encontró el archivo en la ruta: {file_path}")
    print("Asegúrate de que la ruta al archivo CSV sea correcta.")
    exit()

def normalizar(texto):
    if not isinstance(texto, str):
        return ""
    texto = texto.lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    texto = re.sub(r"[^a-z0-9\s]", "", texto)
    return texto.strip()

df["materia_normalizada"] = df["materia"].apply(normalizar)

def clasificar(materia):
    m = materia

    if re.search(r"administracion|gestion|direccion|liderazgo|calidad|compras|inventarios|recursos humanos|mercadotecnia|mercados|ventas|financiera|costos|presupuestos|empresarial", m):
        return "Administración y Gestión"

    if re.search(r"calculo|algebra|estadistica|probabilidad|numerico|matematic|vectorial|convexo|funcional|fourier|analisis", m):
        return "Matemáticas y Estadística"

    if re.search(r"programacion|algoritmos|computacion|base de datos|compilador|software|arquitectura de computadoras|sistemas operativos|redes|inteligencia artificial|informatica|computadora", m):
        return "Programación y Computación"

    if re.search(r"electronica|circuitos|control|potencia|microcontrolador|senal|instrumentacion|telecomunicacion", m):
        return "Electrónica y Control"

    if re.search(r"vibraciones|mecanica|cinematica|dinamica|termofluid|estructuras|mantenimiento|manufactura", m):
        return "Ingeniería Mecánica"

    if re.search(r"materiales|procesos|balance de materia|energia|quimica de alimentos|biotecnologia|analisis de alimentos|inocuidad", m):
        return "Materiales y Procesos"

    if re.search(r"fisica|quimica|termodinamica|optica|electromagnetismo|celdas de combustible", m):
        return "Física y Química"

    if re.search(r"etica|comunicacion|sociedad|humanidades|desarrollo humano|psicologia|responsabilidad social", m):
        return "Humanidades y Comunicación"

    if re.search(r"finanzas|economia|mercado|costos|presupuesto|contabilidad", m):
        return "Economía y Finanzas"

    if re.search(r"automatizacion|robotica|automa|plc|sistemas embebidos", m):
        return "Automatización y Robótica"

    if re.search(r"dibujo|cimentacion|diseno|arquitectura|maquetas|planos", m):
        return "Diseño y Arquitectura"
    
    return "Otra"

df["categoria"] = df["materia_normalizada"].apply(clasificar)

df_unicas = df[['id_materia', 'categoria']].drop_duplicates().reset_index(drop=True)

print("\n" + "="*50)
print("     Estadísticas de Clasificación (Materias Únicas)     ")
print("="*50)

stats = df_unicas['categoria'].value_counts()
print(stats)

print("-" * 50)
print(f"Total de materias únicas clasificadas: {len(df_unicas)}")
print("="*50 + "\n")
df_unicas.to_csv("materias_clasificadas.csv", index=False, encoding="utf-8")

print("Archivo 'materias_clasificadas.csv' generado con éxito.")