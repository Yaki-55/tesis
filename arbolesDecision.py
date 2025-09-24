import pandas as pd
import numpy as np
import re
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import confusion_matrix, roc_auc_score
import os
import joblib
import warnings

warnings.filterwarnings('ignore')

def cargar_y_limpiar_datos(ruta_datos, archivo_graduados):
    """Carga los datos y limpia las calificaciones inválidas (menores a 0)."""
    print("Cargando etiquetas de graduados...")
    with open(archivo_graduados, 'r') as f:
        graduados = set(line.strip() for line in f)
    
    print("Cargando y limpiando archivos CSV de calificaciones...")
    todos_los_datos = []
    file_pattern = re.compile(r'periodo(\d+)carrera(\d+)semestre(\d+)\.csv')
    columnas_calificaciones = ['p1', 'p2', 'p3', 'o', 'pf', 'e1', 'e2', 'esp']
    
    for root, _, files in os.walk(ruta_datos):
        for file in files:
            if file.endswith('.csv'):
                match = file_pattern.match(file)
                if match:
                    try:
                        df = pd.read_csv(os.path.join(root, file))
                        for col in columnas_calificaciones:
                            if col in df.columns:
                                df[col] = df[col].apply(lambda x: np.nan if x < 0 else x)
                        df['semestre'] = int(match.group(3))
                        df['periodo'] = int(match.group(1))
                        todos_los_datos.append(df)
                    except Exception as e:
                        print(f"Error leyendo el archivo {file}: {e}")

    if not todos_los_datos:
        raise ValueError("No se encontraron o no se pudieron leer archivos CSV. Verifica la ruta y el contenido de las carpetas.")
    
    full_df = pd.concat(todos_los_datos, ignore_index=True)
    return full_df, graduados

def crear_dataset_snapshots(df, graduados, period_order, period_order_name):
    """Crea un dataset con 'instantáneas' del progreso de cada alumno por semestre."""
    print("Creando dataset de 'instantáneas' por semestre...")
    period_index_map = {period: i for i, period in enumerate(period_order)}
    snapshot_list = []
    
    grouped = df.groupby('matricula_hash')
    
    for student_hash, data in grouped:
        resultado_final = 1 if student_hash in graduados else 0
        data = data.sort_values(by=['semestre', 'periodo']).reset_index(drop=True)
        
        start_period_idx = period_index_map.get(data['periodo'].min())
        if start_period_idx is None: continue

        for semestre_cursado in sorted(data['semestre'].unique()):
            snapshot_data = data[data['semestre'] <= semestre_cursado]
            
            ideal_regular_periods = semestre_cursado
            last_period_in_snapshot = snapshot_data['periodo'].max()
            current_period_idx = period_index_map.get(last_period_in_snapshot)
            if current_period_idx is None: continue

            actual_regular_periods = sum(1 for p_name in period_order_name[start_period_idx : current_period_idx + 1] if p_name.endswith('A') or p_name.endswith('B'))
            semestres_recursados = max(0, (actual_regular_periods - ideal_regular_periods) // 2)

            snapshot_features = {
                'semestre_actual': semestre_cursado, 'promedio_p1': snapshot_data['p1'].mean(),
                'promedio_p2': snapshot_data['p2'].mean(), 'promedio_p3': snapshot_data['p3'].mean(),
                'promedio_final': snapshot_data['pf'].mean(), 'promedio_e1': snapshot_data['e1'].mean(),
                'promedio_e2': snapshot_data['e2'].mean(), 'promedio_esp': snapshot_data['esp'].mean(),
                'semestres_recursados': semestres_recursados, 'resultado_final': resultado_final
            }
            snapshot_list.append(snapshot_features)
            
    snapshot_df = pd.DataFrame(snapshot_list).fillna(0)
    return snapshot_df

def entrenar_modelo_con_kfolds(snapshot_df, num_splits=5):
    """Entrena y evalúa un Árbol de Decisión usando Stratified K-Fold Cross-Validation."""
    print("\n--- Iniciando Entrenamiento con Árbol de Decisión y K-Folds ---")
    X = snapshot_df.drop('resultado_final', axis=1)
    y = snapshot_df['resultado_final']
    
    n_splits = num_splits
    kf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    auc_scores = []
    total_conf_matrix = np.zeros((2, 2))
    
    # --- CAMBIO DE MODELO ---
    # Usamos DecisionTreeClassifier. max_depth limita la complejidad para evitar sobreajuste.
    model = DecisionTreeClassifier(max_depth=10, random_state=42)
    
    for fold, (train_idx, val_idx) in enumerate(kf.split(X, y)):
        print(f"Procesando Fold {fold + 1}/{n_splits}...")
        
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        # Aunque los árboles no requieren escalado, es buena práctica mantenerlo en el pipeline
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        model.fit(X_train_scaled, y_train)
        
        probas = model.predict_proba(X_val_scaled)[:, 1]
        preds = model.predict(X_val_scaled)
        
        auc_scores.append(roc_auc_score(y_val, probas))
        total_conf_matrix += confusion_matrix(y_val, preds)
        
    print("\n--- Resultados de la Validación Cruzada (Árbol de Decisión) ---")
    print(f"AUC Score Promedio: {np.mean(auc_scores):.4f} (Desv. Estándar: {np.std(auc_scores):.4f})")
    print("\nMatriz de Confusión Acumulada (Total de todas las validaciones):")
    print("                 Predicción: Desertor | Predicción: Graduado")
    print(f"Real: Desertor        {int(total_conf_matrix[0, 0]):<15} | {int(total_conf_matrix[0, 1]):<15}")
    print(f"Real: Graduado        {int(total_conf_matrix[1, 0]):<15} | {int(total_conf_matrix[1, 1]):<15}")
    
    print("\nEntrenando modelo final con todos los datos...")
    final_scaler = StandardScaler().fit(X)
    X_scaled = final_scaler.transform(X)
    model.fit(X_scaled, y)
    
    joblib.dump(model, 'modelo_decision_tree_final.pkl')
    joblib.dump(final_scaler, 'scaler_decision_tree_final.pkl')
    print("Modelo de Árbol de Decisión y escalador finales guardados.")
    
    return model, final_scaler

def predecir_semaforo(datos_estudiante, model, scaler):
    """Predice la probabilidad de graduación y asigna un semáforo de riesgo."""
    df_estudiante = pd.DataFrame([datos_estudiante])
    estudiante_scaled = scaler.transform(df_estudiante)
    prob_graduarse = model.predict_proba(estudiante_scaled)[0, 1]
    
    if prob_graduarse >= 0.70:
        semaforo = "Verde 🟢"
    elif prob_graduarse >= 0.40:
        semaforo = "Amarillo 🟡"
    else:
        semaforo = "Rojo 🔴"
        
    return semaforo, prob_graduarse

# --- EJECUCIÓN PRINCIPAL ---
if __name__ == '__main__':
    ruta_a_tus_datos = r"D:/TesisDB/CSV's"
    archivo_graduados = './graduados.txt'
    
    period_order = [35, 36, 40, 39, 42, 43, 41, 46, 47, 44, 49, 50, 48, 53, 54, 51, 52, 56, 55, 58, 59, 57, 61]
    period_order_name = ["2017-2018A", "2017-2018B", "2017-2018V", "2018-2019A", "2018-2019B", "2018-2019V", "2019-2020A", "2019-2020B", "2019-2020V", "2020-2021A", "2020-2021B", "2020-2021V", "2021-2022A", "2021-2022B", "2021-2022V", "2022-2023A", "2022-2023B", "2022-2023V", "2023-2024A", "2023-2024B", "2023-2024V", "2024-2025A", "2024-2025B"]

    try:
        full_data, graduated_list = cargar_y_limpiar_datos(ruta_a_tus_datos, archivo_graduados)
        snapshot_dataset = crear_dataset_snapshots(full_data, graduated_list, period_order, period_order_name)
        modelo_final, scaler_final = entrenar_modelo_con_kfolds(snapshot_dataset, num_splits = 50)
        
        print("\n--- Cotejando Predicciones del Modelo Final (Árbol de Decisión) ---")

        estudiante_bueno = {'semestre_actual': 4, 'promedio_p1': 8.5, 'promedio_p2': 8.1, 'promedio_p3': 7.8, 'promedio_final': 8.2, 'promedio_e1': 0.0, 'promedio_e2': 0.0, 'promedio_esp': 0.0, 'semestres_recursados': 0}
        estudiante_en_riesgo = {'semestre_actual': 4, 'promedio_p1': 6.2, 'promedio_p2': 5.5, 'promedio_p3': 5.1, 'promedio_final': 5.6, 'promedio_e1': 6.0, 'promedio_e2': 0.0, 'promedio_esp': 0.0, 'semestres_recursados': 1}
        estudiante_perfecto = {'semestre_actual': 4, 'promedio_p1': 10.0, 'promedio_p2': 10.0, 'promedio_p3': 10.0, 'promedio_final': 10.0, 'promedio_e1': 0.0, 'promedio_e2': 0.0, 'promedio_esp': 0.0, 'semestres_recursados': 0}

        casos = {
            "Estudiante con Buen Desempeño": estudiante_bueno,
            "Estudiante en Riesgo": estudiante_en_riesgo,
            "Estudiante 'Perfecto' (Atípico)": estudiante_perfecto
        }

        for nombre_caso, datos_estudiante in casos.items():
            semaforo, prob = predecir_semaforo(datos_estudiante, modelo_final, scaler_final)
            print(f"\nCaso: {nombre_caso}")
            print(f"Resultado: {semaforo} (Probabilidad de graduarse: {prob:.2%})")

    except FileNotFoundError:
        print(f"ERROR: No se encontró la ruta '{ruta_a_tus_datos}' o el archivo '{archivo_graduados}'. Por favor, verifica que las rutas son correctas.")
    except ValueError as ve:
        print(f"ERROR: {ve}")