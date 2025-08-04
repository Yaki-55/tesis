# estadisticas.ipynb
Contiene el desglose de alumnos por carrera de primer semestre, el desglose de alumnos por carrera de decimo semestre y una recapitulación final.

# estadisticas2.ipynb
Contiene las graficas y ademas contiene una comparacion de porcentajes entre las generaciones, es decir.
Para la generación 2000 cuanto porcentaje logro llegar a decimo semestre.

# obtenerCSV.py
Hace la conexión con la bd NES para obtener una carpeta que contenga carpetas individuales para todos los periodos registrados, subcarpetas para todas las carreras y finalmente csv con los grupos que existan en dicho periodo
(Para periodos A solo existiran grupos impares, para periodos B solo existiran grupos pares y para periodo V podran existir o no cualquier grupo)

# primerModelo.ipynb
Usa isolation forest para buscar alumnos anomalos (Outliers).
Spoiler: No funcionó, ya que si en un periodo y en un grupo todos reprobaron, el anomalo resulta ser quien no reprobo xd.