"""
Suite de Pruebas Automatizadas para la Librería Raman Spectroscopy
Verifica los módulos: lectura_raman, raman_processing y raman_database
"""

import os
import shutil
import tempfile
import unittest
import numpy as np
import pandas as pd

import lectura_raman
import raman_processing
import raman_database


class TestRamanSpectroscopy(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix='raman_test_')
        
        # Crear archivo sintético en formato BWSpec
        cls.sample_bwspec = os.path.join(cls.temp_dir, 'sample_A.txt')
        with open(cls.sample_bwspec, 'w', encoding='utf-8') as f:
            f.write(";BWSpec 4.0\n")
            f.write(";Laser Wavelength: 785.0 nm\n")
            f.write(";Integration Time: 5000 ms\n")
            f.write("Pixel; Wavelength; Raman Shift; Dark; Raw; Relative Intensity\n")
            for i in range(200):
                shift = 100.0 + i * 8.0
                intensity = 500.0 + 3000.0 * np.exp(-((shift - 1086.0) ** 2) / (2 * 12.0 ** 2)) + float(np.random.normal(0, 5))
                f.write(f"{i}; {800.0 + i*0.5:.2f}; {shift:.2f}; 100.0; {intensity:.1f}; {intensity:.1f}\n")
                
        # Crear segundo archivo sintético ASCII (2 columnas)
        cls.sample_ascii = os.path.join(cls.temp_dir, 'sample_B.csv')
        with open(cls.sample_ascii, 'w', encoding='utf-8') as f:
            f.write("RamanShift,Intensity\n")
            for i in range(200):
                shift = 100.0 + i * 8.0
                intensity = 300.0 + 1500.0 * np.exp(-((shift - 253.0) ** 2) / (2 * 10.0 ** 2))
                f.write(f"{shift:.2f},{intensity:.2f}\n")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_lectura_bwspec(self):
        """Verifica la correcta lectura de archivos BWSpec (.txt)"""
        data = lectura_raman.cargar_espectro_raman(self.sample_bwspec)
        self.assertIn('x', data)
        self.assertIn('y', data)
        self.assertIn('nombre', data)
        self.assertGreater(len(data['x']), 100, "El espectro debe contener más de 100 puntos")
        self.assertEqual(data['formato'], 'BWSpec')

    def test_lectura_directorio(self):
        """Verifica la carga en lote de directorio y generación de espectros SUMA y PROMEDIO"""
        espectros = lectura_raman.cargar_directorio_raman(self.temp_dir)
        self.assertGreater(len(espectros), 2, "Debe cargar múltiples espectros del directorio")
        nombres = [e['nombre'] for e in espectros]
        self.assertIn('--- ESPECTRO PROMEDIO ---', nombres)
        self.assertIn('--- ESPECTRO SUMA ---', nombres)

    def test_despiking(self):
        """Verifica que el algoritmo de despiking elimine picos agudos artificiales"""
        y_sim = np.ones(100) * 10.0
        y_sim[50] = 500.0  # Rayo cósmico artificial
        
        y_clean = raman_processing.despike_spectrum(y_sim, threshold=4.0)
        self.assertLess(y_clean[50], 50.0, "El pico espurio debe ser suavizado por despiking")

    def test_linea_base(self):
        """Verifica la convergencia de los algoritmos ALS, AIRPLS, SNIP y Polinomial"""
        x = np.linspace(100, 2000, 500)
        baseline_true = 50 + 0.05 * x + 10 * np.sin(x / 200)
        peak = 100 * np.exp(-((x - 1000) ** 2) / (2 * 15 ** 2))
        y = baseline_true + peak
        
        b_als = raman_processing.baseline_als(y, lam=1e5, p=0.01)
        b_airpls = raman_processing.baseline_airpls(y, lam=1e5)
        b_snip = raman_processing.baseline_snip(y, max_half_window=30)
        
        self.assertEqual(len(b_als), len(y))
        self.assertEqual(len(b_airpls), len(y))
        self.assertEqual(len(b_snip), len(y))
        
        # La línea base estimada no debe incluir la parte superior del pico
        self.assertLess(b_als[np.argmin(np.abs(x - 1000))], y[np.argmin(np.abs(x - 1000))])

    def test_fwhm_y_picos(self):
        """Verifica el cálculo de FWHM directo y ajuste de perfil sobre un pico sintético conocido"""
        x = np.linspace(100, 1000, 1000)
        amp_known = 100.0
        center_known = 500.0
        gamma_known = 10.0
        fwhm_known = 2.0 * gamma_known  # FWHM Lorentziano = 20.0
        
        y_lorentz = raman_processing.lorentzian_profile(x, amp_known, center_known, gamma_known)
        
        # Test FWHM directo
        idx_peak = np.argmin(np.abs(x - center_known))
        fwhm_dir, _ = raman_processing.calcular_fwhm_directo(x, y_lorentz, idx_peak)
        self.assertAlmostEqual(fwhm_dir, fwhm_known, delta=0.5)
        
        # Test Ajuste de Perfil
        fit_res = raman_processing.ajustar_perfil_pico(x, y_lorentz, center_known, window_width=40.0, shape='lorentzian')
        self.assertIsNotNone(fit_res)
        self.assertAlmostEqual(fit_res['fwhm_fit'], fwhm_known, delta=0.2)
        self.assertAlmostEqual(fit_res['center'], center_known, delta=0.1)

    def test_identificacion_base_datos(self):
        """Verifica la búsqueda e identificación de compuestos por banda Raman"""
        matches = raman_database.identificar_banda(1086.0, tolerance=5.0)
        self.assertGreater(len(matches), 0)
        compuestos = [m['compuesto'] for m in matches]
        self.assertIn('Calcita (CaCO3)', compuestos)

    def test_reinterpolacion_y_superposicion(self):
        """Verifica la reinterpolación sobre grilla común para superposición y PCA"""
        espectros = lectura_raman.cargar_directorio_raman(self.temp_dir)
        specs_indiv = [s for s in espectros if 'ESPECTRO' not in s['nombre']]
        x_comun, y_list = lectura_raman.reinterpolar_espectros_a_grilla_comun(specs_indiv, num_puntos=500)
        self.assertEqual(len(x_comun), 500)
        self.assertEqual(len(y_list), len(specs_indiv))
        for y_interp in y_list:
            self.assertEqual(len(y_interp), 500)

    def test_identificacion_espectro_y_modos(self):
        """Verifica la identificación multibanda con score y el filtrado por modos de análisis"""
        # Picos característicos de Cinabrio
        picos_cinabrio = [253.0, 282.0, 343.0]
        candidatos = raman_database.identificar_espectro(picos_cinabrio, modo='pigmentos')
        self.assertGreater(len(candidatos), 0)
        self.assertIn('Cinabrio / Bermellón (HgS trigonal)', candidatos[0][0])
        self.assertGreaterEqual(candidatos[0][1]['score'], 80.0)

        # Modo Cristalografía
        picos_calcita = [1086.0, 712.0, 282.0]
        candidatos_cristal = raman_database.identificar_espectro(picos_calcita, modo='cristalografia')
        self.assertGreater(len(candidatos_cristal), 0)
        self.assertIn('Calcita', candidatos_cristal[0][0])
        self.assertIn('Trigonal', candidatos_cristal[0][1]['sistema_cristalino'])


if __name__ == '__main__':
    unittest.main()

