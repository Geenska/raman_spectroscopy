import os
import re
import pandas as pd
import numpy as np


def _abrir_archivo_texto(ruta_archivo):
    """
    Intenta abrir un archivo de texto con múltiples codificaciones comunes (UTF-8, Latin-1, CP1252).
    """
    for enc in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            with open(ruta_archivo, 'r', encoding=enc) as f:
                return f.readlines()
        except UnicodeDecodeError:
            continue
    with open(ruta_archivo, 'r', encoding='utf-8', errors='replace') as f:
        return f.readlines()


def leer_bwspec_txt(ruta_archivo):
    """
    Lee un archivo de espectroscopia Raman formato BWSpec (B&W Tek .txt/.dat).
    Filtra automáticamente la región Stokes útil (>= 50 cm^-1).
    """
    lines = _abrir_archivo_texto(ruta_archivo)
    metadata = {}
    lineas_datos = []
    en_seccion_datos = False
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
            
        if not en_seccion_datos:
            if ';' in line_str and not line_str.startswith('Pixel;'):
                parts = line_str.split(';')
                key = parts[0].strip().lower()
                val = parts[1].strip() if len(parts) > 1 else ''
                metadata[key] = val
            elif line_str.startswith('Pixel;') or 'Raman Shift' in line_str or 'Pixel\t' in line_str:
                en_seccion_datos = True
        else:
            sep = ';' if ';' in line_str else ('\t' if '\t' in line_str else None)
            if sep:
                parts = [p.strip() for p in line_str.split(sep)]
                if len(parts) >= 2:
                    lineas_datos.append(parts)
                    
    if not lineas_datos or len(lineas_datos) < 20:
        raise ValueError(f"No se detectó estructura BWSpec estándar en {ruta_archivo}")
        
    parsed_rows = []
    for row in lineas_datos:
        try:
            # Reemplazar comas decimales si existieran
            r0 = row[0].replace(',', '.') if len(row) > 0 and row[0] != '' else ''
            r1 = row[1].replace(',', '.') if len(row) > 1 and row[1] != '' else ''
            
            pix = float(r0) if r0 != '' else np.nan
            shift = float(r1) if r1 != '' else np.nan
            
            dark = float(row[2].replace(',', '.')) if len(row) > 2 and row[2] != '' else np.nan
            raw = float(row[3].replace(',', '.')) if len(row) > 3 and row[3] != '' else np.nan
            dark_sub = float(row[4].replace(',', '.')) if len(row) > 4 and row[4] != '' else (raw - dark if not np.isnan(raw) and not np.isnan(dark) else raw)
            
            # Si solo tiene 2 columnas, la 2da es la intensidad
            if len(row) == 2 or np.isnan(dark_sub):
                intensidad = shift if not np.isnan(pix) and len(row) == 2 else raw
            else:
                intensidad = dark_sub
                
            parsed_rows.append({
                'Pixel': pix,
                'Raman_Shift': shift,
                'Dark': dark,
                'Raw': raw,
                'Intensity': intensidad
            })
        except ValueError:
            continue
            
    if not parsed_rows:
        raise ValueError("No se pudieron parsear filas numéricas en BWSpec.")
        
    df = pd.DataFrame(parsed_rows)
    
    # Filtrar solo la región espectral Stokes Raman útil (entre 50 y 4500 cm^-1)
    df_valid = df.dropna(subset=['Raman_Shift']).copy()
    df_valid = df_valid[(df_valid['Raman_Shift'] >= 50.0) & (df_valid['Raman_Shift'] <= 4500.0)].copy()
    
    if len(df_valid) < 20:
        raise ValueError(f"El archivo no contiene suficientes desplazamientos Raman válidos en {ruta_archivo}.")
        
    df_valid = df_valid.sort_values(by='Raman_Shift').reset_index(drop=True)
    
    x = df_valid['Raman_Shift'].values
    y = df_valid['Intensity'].values
    
    # Fallback a Raw si Intensity es no positivo
    if np.max(y) <= 0 and 'Raw' in df_valid.columns:
        valid_raw = df_valid['Raw'].dropna().values
        if len(valid_raw) == len(y) and np.max(valid_raw) > 0:
            y = valid_raw
            
    nombre = os.path.splitext(os.path.basename(ruta_archivo))[0]
    
    return {
        'nombre': nombre,
        'ruta': ruta_archivo,
        'metadata': metadata,
        'df': df_valid,
        'x': x,
        'y': y,
        'formato': 'BWSpec'
    }


def leer_csv_ascii_raman(ruta_archivo):
    """
    Lee archivos espectrales Raman de 2 columnas en texto plano (CSV/TSV/TXT/ASC/DAT).
    Soporta cabeceras de texto previas, separadores dinámicos y coma/punto decimal.
    """
    lines = _abrir_archivo_texto(ruta_archivo)
    
    parsed_pairs = []
    
    for line in lines:
        line_str = line.strip()
        if not line_str or line_str.startswith('#') or line_str.startswith('//') or line_str.startswith('%'):
            continue
            
        # Detectar delimitador: tab, punto y coma, coma, o espacios
        if '\t' in line_str:
            tokens = [t.strip() for t in line_str.split('\t') if t.strip()]
        elif ';' in line_str:
            tokens = [t.strip() for t in line_str.split(';') if t.strip()]
        elif ',' in line_str and line_str.count(',') == 1:
            # Caso CSV estándar x,y
            tokens = [t.strip() for t in line_str.split(',') if t.strip()]
        else:
            tokens = re.split(r'\s+', line_str)
            
        if len(tokens) >= 2:
            try:
                # Normalizar coma decimal europea/latina (1086,5 -> 1086.5)
                val_x = float(tokens[0].replace(',', '.'))
                val_y = float(tokens[1].replace(',', '.'))
                parsed_pairs.append((val_x, val_y))
            except ValueError:
                # Era una línea de encabezado o texto descriptivo, continuar
                continue
                
    if len(parsed_pairs) < 25:
        raise ValueError(f"El archivo {ruta_archivo} no contiene suficientes puntos espectrales numéricos (mínimo 25).")
        
    x_vals = np.array([p[0] for p in parsed_pairs], dtype=float)
    y_vals = np.array([p[1] for p in parsed_pairs], dtype=float)
    
    # Filtrar región Stokes útil (50 a 4500 cm^-1)
    mask = (x_vals >= 50.0) & (x_vals <= 4500.0)
    if np.sum(mask) >= 20:
        x_vals = x_vals[mask]
        y_vals = y_vals[mask]
        
    sort_idx = np.argsort(x_vals)
    x_vals = x_vals[sort_idx]
    y_vals = y_vals[sort_idx]
    
    nombre = os.path.splitext(os.path.basename(ruta_archivo))[0]
    
    return {
        'nombre': nombre,
        'ruta': ruta_archivo,
        'metadata': {},
        'df': pd.DataFrame({'Raman_Shift': x_vals, 'Intensity': y_vals}),
        'x': x_vals,
        'y': y_vals,
        'formato': 'ASCII/CSV'
    }


def cargar_espectro_raman(ruta_archivo):
    """
    Función autodetectora para cargar un espectro Raman (.txt, .csv, .asc, .dat, .tsv).
    """
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"El archivo {ruta_archivo} no existe.")
        
    base = os.path.basename(ruta_archivo).lower()
    if base.startswith('.') or base.startswith('~'):
        raise ValueError("Archivo temporal u oculto ignorado.")
        
    try:
        res = leer_bwspec_txt(ruta_archivo)
        if len(res['x']) >= 20:
            return res
    except Exception:
        pass
        
    try:
        return leer_csv_ascii_raman(ruta_archivo)
    except Exception as e:
        raise ValueError(f"No se pudo cargar como espectro Raman: {e}")


def reinterpolar_espectros_a_grilla_comun(espectros, num_puntos=2048):
    """
    Toma una lista de espectros con ejes x potencialmente ligeramente distintos
    y los interpola a un eje x uniforme común (rango de superposición).
    """
    if not espectros:
        return np.array([]), []
        
    min_x = max(np.min(s['x']) for s in espectros)
    max_x = min(np.max(s['x']) for s in espectros)
    
    x_comun = np.linspace(min_x, max_x, num_puntos)
    y_interpolados = []
    
    for s in espectros:
        y_interp = np.interp(x_comun, s['x'], s['y'])
        y_interpolados.append(y_interp)
        
    return x_comun, y_interpolados


def cargar_directorio_raman(dir_path):
    """
    Carga todos los espectros Raman soportados en un directorio y sus subdirectorios de muestras,
    ignorando carpetas de sistema. Genera automáticamente los espectros de muestra, PROMEDIO y SUMA.
    """
    if not os.path.isdir(dir_path):
        return []
        
    espectros = []
    extensiones = ('.txt', '.csv', '.asc', '.tsv', '.dat', '.prn', '.spc')
    carpetas_ignoradas = {'.git', '__pycache__', '.venv', 'venv_win', '.idea', '.vscode', '.system_generated'}
    
    rutas_encontradas = []
    
    for root, dirs, files in os.walk(dir_path):
        # Excluir carpetas del sistema
        dirs[:] = [d for d in dirs if d.lower() not in carpetas_ignoradas and not d.startswith('.')]
        
        for f in sorted(files):
            f_lower = f.lower()
            if f.startswith('.') or f.startswith('~'):
                continue
            if f_lower.endswith(extensiones):
                rutas_encontradas.append(os.path.join(root, f))
                
    for ruta_completa in rutas_encontradas:
        try:
            spec = cargar_espectro_raman(ruta_completa)
            # Evitar añadir duplicados exactos
            if not any(e['ruta'] == spec['ruta'] for e in espectros):
                espectros.append(spec)
        except Exception:
            # Ignorar archivos no espectrales sin detener el proceso
            continue
            
    if not espectros:
        return []
        
    try:
        x_comun, y_interp_list = reinterpolar_espectros_a_grilla_comun(espectros)
        if len(y_interp_list) > 1:
            y_arr = np.array(y_interp_list)
            y_suma = np.sum(y_arr, axis=0)
            y_prom = np.mean(y_arr, axis=0)
            
            espectros.append({
                'nombre': '--- ESPECTRO PROMEDIO ---',
                'ruta': dir_path,
                'metadata': {'tipo': 'PROMEDIO_GRUPO', 'num_muestras': len(y_interp_list)},
                'df': pd.DataFrame({'Raman_Shift': x_comun, 'Intensity': y_prom}),
                'x': x_comun,
                'y': y_prom,
                'formato': 'PROMEDIO'
            })
            
            espectros.append({
                'nombre': '--- ESPECTRO SUMA ---',
                'ruta': dir_path,
                'metadata': {'tipo': 'SUMA_GRUPO', 'num_muestras': len(y_interp_list)},
                'df': pd.DataFrame({'Raman_Shift': x_comun, 'Intensity': y_suma}),
                'x': x_comun,
                'y': y_suma,
                'formato': 'SUMA'
            })
    except Exception as e:
        print(f"[Advertencia] No se pudo calcular espectro suma/promedio: {e}")
        
    return espectros
