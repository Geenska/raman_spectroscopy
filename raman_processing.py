"""
Módulo de Procesamiento Numérico Avanzado para Espectroscopia Raman.
Incluye:
- Despiking (Filtro de Rayos Cósmicos)
- Sustracción de Línea Base (ALS, AIRPLS, SNIP, Polinomial)
- Suavizado y Detección de Picos
- Cálculo de FWHM (Directo por interpolación y Ajuste de Perfil Gauss/Lorentz/Voigt)
- Normalización espectral
"""

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
from scipy.signal import find_peaks, savgol_filter
from scipy.optimize import curve_fit


# ==============================================================================
# 1. REMOCIÓN DE RAYOS CÓSMICOS (DESPIKING)
# ==============================================================================

def despike_spectrum(y, threshold=6.0, window_size=5):
    """
    Elimina artefactos estrechos de alta intensidad (rayos cósmicos CCD)
    utilizando el método Z-Score modificado sobre la diferencia espectral (Whitaker & Hayes, 2018).
    """
    y_arr = np.asarray(y, dtype=float)
    n = len(y_arr)
    if n < window_size:
        return y_arr.copy()
        
    y_clean = y_arr.copy()
    d = np.diff(y_clean)
    
    median_d = np.median(d)
    mad_d = np.median(np.abs(d - median_d))
    if mad_d < 1e-12:
        mad_d = 1e-6
    s = 0.6745 * (d - median_d) / mad_d
    
    spikes = np.where(np.abs(s) > threshold)[0]
    if len(spikes) == 0:
        return y_clean
        
    half_w = window_size // 2
    for idx in spikes:
        idx_pt = min(idx + 1, n - 1)
        i_start = max(0, idx_pt - half_w)
        i_end = min(n, idx_pt + half_w + 1)
        # Tomar los vecinos excluyendo el punto con el rayo cósmico
        mask_neighbors = np.ones(i_end - i_start, dtype=bool)
        if 0 <= (idx_pt - i_start) < len(mask_neighbors):
            mask_neighbors[idx_pt - i_start] = False
        neighbors = y_clean[i_start:i_end][mask_neighbors]
        if len(neighbors) > 0:
            y_clean[idx_pt] = np.median(neighbors)
            
    return y_clean


# ==============================================================================
# 2. ALGORITMOS DE LÍNEA BASE (BASELINE CORRECTION)
# ==============================================================================

def baseline_als(y, lam=1e5, p=0.01, max_iter=20):
    """
    Algoritmo Asymmetric Least Squares (ALS) para estimar la línea base Raman (Eilers & Boelens, 2005).
    """
    y = np.asarray(y, dtype=float)
    L = len(y)
    D = sparse.diags([1, -2, 1], [0, -1, -2], shape=(L, L - 2), dtype=float)
    w = np.ones(L)
    
    for _ in range(max_iter):
        W = sparse.spdiags(w, 0, L, L)
        Z = (W + lam * D.dot(D.transpose())).tocsc()
        z = spsolve(Z, w * y)
        w_new = p * (y > z) + (1 - p) * (y <= z)
        if np.all(w == w_new):
            break
        w = w_new
        
    return z


def baseline_airpls(y, lam=1e5, porder=1, max_iter=30):
    """
    Adaptive Iterative Reweighted Partial Least Squares (AIRPLS) (Zhang et al., 2010).
    """
    y = np.asarray(y, dtype=float)
    m = len(y)
    E = sparse.eye(m, format='csc', dtype=float)
    
    for i in range(porder):
        E = E[1:] - E[:-1]
        
    D = E.T
    w = np.ones(m)
    z = y.copy()
    
    for i in range(1, max_iter + 1):
        W = sparse.diags(w, 0, shape=(m, m), dtype=float)
        Z = (W + lam * (D.dot(E))).tocsc()
        z = spsolve(Z, w * y)
        d = y - z
        dssn = np.abs(d[d < 0].sum())
        if dssn < 0.001 * np.abs(y).sum() or i == max_iter:
            break
            
        w[d >= 0] = 0
        w[d < 0] = np.exp(i * np.abs(d[d < 0]) / dssn)
        w[0] = np.exp(i * (d[d < 0].max() if len(d[d < 0]) > 0 else 0) / dssn)
        w[-1] = w[0]
        
    return z


def baseline_snip(y, max_half_window=40):
    """
    SNIP (Statistics-sensitive Non-linear Iterative Peak-clipping).
    Algoritmo iterativo de recorte no lineal de picos.
    """
    y_base = np.log(np.log(np.sqrt(np.abs(y) + 1.0) + 1.0) + 1.0)
    n = len(y_base)
    
    for p in range(1, max_half_window + 1):
        for i in range(p, n - p):
            val1 = y_base[i]
            val2 = (y_base[i - p] + y_base[i + p]) / 2.0
            if val2 < val1:
                y_base[i] = val2
                
    baseline = (np.exp(np.exp(y_base) - 1.0) - 1.0)**2 - 1.0
    return np.maximum(0, baseline)


def baseline_polynomial(x, y, poly_order=3, n_iter=10):
    """
    Ajuste Polinomial Modificado Iterativo (ModPoly).
    Ignora iterativamente los puntos por encima del polinomio ajustado.
    """
    x_norm = (x - np.mean(x)) / np.std(x)
    y_fit = y.copy()
    
    for _ in range(n_iter):
        coeffs = np.polyfit(x_norm, y_fit, poly_order)
        poly_vals = np.polyval(coeffs, x_norm)
        # Mantener solo los mínimos
        y_fit = np.minimum(y_fit, poly_vals)
        
    return poly_vals


def estimar_linea_base(x, y, metodo='als', **kwargs):
    """
    Función unificada para la estimación de línea base en Raman.
    Métodos disponibles: 'als', 'airpls', 'snip', 'polynomial'.
    """
    metodo = metodo.lower()
    if metodo == 'als':
        lam = kwargs.get('lam', 1e5)
        p = kwargs.get('p', 0.01)
        return baseline_als(y, lam=lam, p=p)
    elif metodo == 'airpls':
        lam = kwargs.get('lam', 1e5)
        return baseline_airpls(y, lam=lam)
    elif metodo == 'snip':
        max_hw = kwargs.get('max_half_window', 40)
        return baseline_snip(y, max_half_window=max_hw)
    elif metodo == 'polynomial' or metodo == 'poly':
        order = kwargs.get('poly_order', 3)
        return baseline_polynomial(x, y, poly_order=order)
    else:
        raise ValueError(f"Método de línea base no reconocido: {metodo}")


# ==============================================================================
# 3. DETECCIÓN Y AJUSTE DE PICOS (PEAK DETECTION & FWHM)
# ==============================================================================

def gaussian_profile(x, amp, center, sigma):
    return amp * np.exp(-((x - center) ** 2) / (2 * sigma ** 2))

def lorentzian_profile(x, amp, center, gamma):
    return amp * (gamma**2 / ((x - center)**2 + gamma**2))

def voigt_profile(x, amp, center, sigma, gamma):
    # Aproximación rápida de Pseudo-Voigt (combinación lineal de Gaussiana y Lorentziana)
    fwhm_g = 2.35482 * sigma
    fwhm_l = 2 * gamma
    fwhm_v = 0.5346 * fwhm_l + np.sqrt(0.2166 * fwhm_l**2 + fwhm_g**2)
    eta = 1.36603 * (fwhm_l / fwhm_v) - 0.47719 * (fwhm_l / fwhm_v)**2 + 0.11116 * (fwhm_l / fwhm_v)**3
    eta = np.clip(eta, 0, 1)
    
    g_val = gaussian_profile(x, amp, center, sigma)
    l_val = lorentzian_profile(x, amp, center, gamma)
    return eta * l_val + (1 - eta) * g_val


def calcular_fwhm_directo(x, y, peak_idx):
    """
    Calcula el FWHM (Ancho Completo a la Mitad del Máximo) de forma directa
    mediante interpolación lineal sobre los datos espectrales procesados.
    """
    x_peak = x[peak_idx]
    y_peak = y[peak_idx]
    half_max = y_peak / 2.0
    
    if y_peak <= 0:
        return 0.0, (x_peak, x_peak)
        
    # Buscar borde izquierdo
    left_idx = peak_idx
    while left_idx > 0 and y[left_idx] > half_max:
        left_idx -= 1
        
    if left_idx == 0:
        x_left = x[0]
    else:
        # Interpolación lineal izquierda
        x1, x2 = x[left_idx], x[left_idx + 1]
        y1, y2 = y[left_idx], y[left_idx + 1]
        x_left = x1 + (half_max - y1) * (x2 - x1) / (y2 - y1) if y2 != y1 else x1

    # Buscar borde derecho
    right_idx = peak_idx
    while right_idx < len(y) - 1 and y[right_idx] > half_max:
        right_idx += 1
        
    if right_idx == len(y) - 1:
        x_right = x[-1]
    else:
        # Interpolación lineal derecha
        x1, x2 = x[right_idx - 1], x[right_idx]
        y1, y2 = y[right_idx - 1], y[right_idx]
        x_right = x1 + (half_max - y1) * (x2 - x1) / (y2 - y1) if y2 != y1 else x2

    fwhm = abs(x_right - x_left)
    return fwhm, (x_left, x_right)


def ajustar_perfil_pico(x, y, peak_center_guess, window_width=25.0, shape='lorentzian'):
    """
    Ajusta una función teórica de línea de pico (Lorentziana, Gaussiana o Voigt)
    en una ventana centrada en el pico para obtener FWHM exacto, centro y área neta.
    """
    mask = (x >= peak_center_guess - window_width) & (x <= peak_center_guess + window_width)
    x_win = x[mask]
    y_win = y[mask]
    
    if len(x_win) < 5:
        return None
        
    amp_guess = np.max(y_win)
    idx_max = np.argmax(y_win)
    center_guess = x_win[idx_max]
    
    # Estimar FWHM empírico inicial
    half_max = amp_guess / 2.0
    half_mask = y_win >= half_max
    if np.sum(half_mask) >= 2:
        fwhm_guess = np.max(x_win[half_mask]) - np.min(x_win[half_mask])
    else:
        fwhm_guess = 5.0
        
    fwhm_guess = max(1.0, fwhm_guess)

    try:
        if shape == 'gaussian':
            sigma_guess = fwhm_guess / 2.35482
            popt, _ = curve_fit(gaussian_profile, x_win, y_win, 
                                p0=[amp_guess, center_guess, sigma_guess],
                                bounds=([0, center_guess - 10, 0.1], [amp_guess * 2, center_guess + 10, 50]))
            amp, center, sigma = popt
            fwhm_fit = 2.35482 * abs(sigma)
            area = amp * abs(sigma) * np.sqrt(2 * np.pi)
            
        elif shape == 'voigt':
            sigma_guess = fwhm_guess / 2.35482
            gamma_guess = fwhm_guess / 2.0
            popt, _ = curve_fit(voigt_profile, x_win, y_win, 
                                p0=[amp_guess, center_guess, sigma_guess, gamma_guess],
                                bounds=([0, center_guess - 10, 0.1, 0.1], [amp_guess * 2, center_guess + 10, 50, 50]))
            amp, center, sigma, gamma = popt
            fwhm_g = 2.35482 * abs(sigma)
            fwhm_l = 2 * abs(gamma)
            fwhm_fit = 0.5346 * fwhm_l + np.sqrt(0.2166 * fwhm_l**2 + fwhm_g**2)
            area = amp * (fwhm_fit * 1.065) # aproximación de área Voigt
            
        else:  # Lorentzian (por defecto en espectroscopia Raman)
            gamma_guess = fwhm_guess / 2.0
            popt, _ = curve_fit(lorentzian_profile, x_win, y_win, 
                                p0=[amp_guess, center_guess, gamma_guess],
                                bounds=([0, center_guess - 10, 0.1], [amp_guess * 2, center_guess + 10, 50]))
            amp, center, gamma = popt
            fwhm_fit = 2.0 * abs(gamma)
            area = amp * np.pi * abs(gamma)

        # Bondad de ajuste R^2
        y_fit_win = (gaussian_profile(x_win, amp, center, sigma) if shape == 'gaussian' else 
                    (voigt_profile(x_win, amp, center, sigma, gamma) if shape == 'voigt' else 
                     lorentzian_profile(x_win, amp, center, gamma)))
        ss_res = np.sum((y_win - y_fit_win) ** 2)
        ss_tot = np.sum((y_win - np.mean(y_win)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return {
            'center': center,
            'amplitude': amp,
            'fwhm_fit': fwhm_fit,
            'area_fit': area,
            'r_squared': max(0.0, r_squared),
            'shape': shape,
            'x_win': x_win,
            'y_fit_win': y_fit_win
        }
    except Exception:
        return None


def buscar_picos_raman(x, y_net, distance_cm=10.0, prominence_factor=0.03, height_factor=0.02, smooth_window=7):
    """
    Identifica picos en un espectro Raman con sustracción de línea base.
    Retorna una lista de diccionarios con metadatos de picos (Posición, Altura, FWHM, Área, etc.).
    """
    if len(y_net) == 0:
        return []
        
    # Paso opcional: suavizado Savitzky-Golay ligero para evitar detectar ruido
    if smooth_window > 3 and len(y_net) > smooth_window:
        if smooth_window % 2 == 0:
            smooth_window += 1
        y_smooth = savgol_filter(y_net, smooth_window, polyorder=2)
    else:
        y_smooth = y_net
        
    dx = np.mean(np.diff(x))
    distance_pts = max(1, int(round(distance_cm / dx)))
    
    max_y = np.max(y_smooth)
    min_prominence = max_y * prominence_factor
    min_height = max_y * height_factor
    
    peak_indices, props = find_peaks(
        y_smooth,
        height=min_height,
        prominence=min_prominence,
        distance=distance_pts
    )
    
    lista_picos = []
    for idx in peak_indices:
        x_pico = x[idx]
        y_raw_pico = y_net[idx]
        
        # FWHM Directo
        fwhm_dir, (x_left, x_right) = calcular_fwhm_directo(x, y_net, idx)
        
        # Integración de Área Neta Trapezoidal
        mask_area = (x >= x_left) & (x <= x_right)
        area_neta = np.trapezoid(y_net[mask_area], x[mask_area]) if np.sum(mask_area) > 1 else y_raw_pico * fwhm_dir
        
        # Ajuste de Perfil Lorentziano
        fit_res = ajustar_perfil_pico(x, y_net, x_pico, window_width=max(15.0, fwhm_dir * 1.5), shape='lorentzian')
        
        lista_picos.append({
            'idx': idx,
            'position_cm': x_pico,
            'intensity_net': y_raw_pico,
            'fwhm_direct': fwhm_dir,
            'fwhm_left': x_left,
            'fwhm_right': x_right,
            'area_net': area_neta,
            'fit_result': fit_res
        })
        
    # Ordenar picos por intensidad descendente
    lista_picos.sort(key=lambda p: p['intensity_net'], reverse=True)
    return lista_picos


# ==============================================================================
# 4. NORMALIZACIÓN Y PIPELINE COMPLETO
# ==============================================================================

def normalizar_espectro(y, metodo='max'):
    """
    Normaliza el espectro Raman.
    Métodos:
      - 'max': Escala la intensidad máxima a 1.0
      - 'minmax': Escala al rango [0, 1]
      - 'vector': Norma L2 unitaria
      - 'area': Área total bajo la curva igual a 1.0
    """
    y_norm = np.array(y, dtype=float).copy()
    if metodo == 'max':
        max_val = np.max(y_norm)
        return y_norm / max_val if max_val > 0 else y_norm
    elif metodo == 'minmax':
        min_val, max_val = np.min(y_norm), np.max(y_norm)
        return (y_norm - min_val) / (max_val - min_val) if max_val > min_val else y_norm
    elif metodo == 'vector':
        norm = np.sqrt(np.sum(y_norm ** 2))
        return y_norm / norm if norm > 0 else y_norm
    elif metodo == 'area':
        area = np.sum(np.abs(y_norm))
        return y_norm / area if area > 0 else y_norm
    return y_norm


def procesar_espectro_raman_completo(x, y, do_despike=True, baseline_method='als', 
                                    baseline_params=None, norm_method=None,
                                    peak_params=None):
    """
    Ejecuta el pipeline completo de procesamiento espectral Raman:
    1. Despiking (opcional)
    2. Estimación y sustracción de línea base
    3. Normalización (opcional)
    4. Búsqueda de picos y análisis de FWHM
    """
    if baseline_params is None:
        baseline_params = {}
    if peak_params is None:
        peak_params = {}
        
    # 1. Despiking
    y_clean = despike_spectrum(y) if do_despike else np.array(y, dtype=float)
    
    # 2. Línea Base
    y_baseline = estimar_linea_base(x, y_clean, metodo=baseline_method, **baseline_params)
    y_net = np.maximum(0, y_clean - y_baseline)
    
    # 3. Normalización
    if norm_method:
        y_net_final = normalizar_espectro(y_net, metodo=norm_method)
    else:
        y_net_final = y_net
        
    # 4. Picos y FWHM
    picos = buscar_picos_raman(x, y_net_final, **peak_params)
    
    return {
        'x': x,
        'y_raw': y,
        'y_clean': y_clean,
        'y_baseline': y_baseline,
        'y_net': y_net_final,
        'picos': picos
    }
