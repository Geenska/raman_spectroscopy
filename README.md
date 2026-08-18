# 🔬 Raman SpectroLab Pro - CNCPC / CÓDICE

> **Plataforma de Procesamiento Espectral, Sustracción de Fluorescencia, Caracterización Cristalográfica y Análisis Arqueométrico de Espectros Raman**

![Python Version](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)
![GUI Engine](https://img.shields.io/badge/GUI-Tkinter%20%2F%20TkinterDnD2-00599C?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-GNU%20GPL%20v3.0-blue?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=for-the-badge)
![Institution](https://img.shields.io/badge/INAH-CNCPC%20%2F%20CÓDICE-red?style=for-the-badge)

**Raman SpectroLab Pro** es una plataforma científica de escritorio de alto rendimiento desarrollada para la visualización interactiva, filtrado de rayos cósmicos (*despiking*), sustracción de fluorescencia mediante penalización por curvatura (ALS/AIRPLS/SNIP), ajuste no lineal de perfiles de banda (Lorentziano, Gaussiano y Voigt), cálculo del ancho a media altura (**FWHM**), identificación de fases pigmentarias mesoamericanas y coloniales, discriminación cristalográfica de polimorfos y análisis estadístico multivariado (PCA).

Diseñado específicamente para el estudio no destructivo del patrimonio cultural, obras de arte y materiales arqueológicos en el **Laboratorio CÓDICE** de la **CNCPC - INAH**, el software permite procesar tanto mediciones puntuales como lotes masivos de excavaciones y proyectos de conservación.

---

## 📑 Tabla de Contenidos

- [🔬 Raman SpectroLab Pro - CNCPC / CÓDICE](#-raman-spectrolab-pro---cncpc--códice)
  - [📑 Tabla de Contenidos](#-tabla-de-contenidos)
  - [📌 Visión General](#-visión-general)
  - [✨ Características Principales](#-características-principales)
    - [🧹 Filtrado de Rayos Cósmicos (*Despiking*)](#-filtrado-de-rayos-cósmicos-despiking)
    - [📉 Sustracción de Fluorescencia y Línea Base](#-sustracción-de-fluorescencia-y-línea-base)
    - [📐 Análisis de Bandas, Geometría y FWHM](#-análisis-de-bandas-geometría-y-fwhm)
    - [🎨 Motor Arqueométrico y Diagnóstico Cristalográfico](#-motor-arqueométrico-y-diagnóstico-cristalográfico)
    - [📊 Modo Comparación con Línea Base en $y = 0$](#-modo-comparación-con-línea-base-en-y--0)
    - [📈 Análisis Estadístico Multivariado (PCA)](#-análisis-estadístico-multivariado-pca)
    - [📦 Procesamiento y Exportación Masiva por Lote](#-procesamiento-y-exportación-masiva-por-lote)
  - [🏗️ Arquitectura del Proyecto](#️-arquitectura-del-proyecto)
  - [📁 Formatos Soportados y Matriz de Exportación](#-formatos-soportados-y-matriz-de-exportación)
    - [Formatos de Entrada](#formatos-de-entrada)
    - [Formatos y Matriz de Salida](#formatos-y-matriz-de-salida)
  - [💻 Instalación y Requisitos del Sistema](#-instalación-y-requisitos-del-sistema)
    - [Requisitos Previos](#requisitos-previos)
    - [Opción 1: Windows (Iniciador Automático en 1 Clic)](#opción-1-windows-iniciador-automático-en-1-clic)
    - [Opción 2: Linux / macOS (Terminal)](#opción-2-linux--macos-terminal)
  - [⚡ Guía Rápida de Flujo de Trabajo](#-guía-rápida-de-flujo-de-trabajo)
  - [🧪 Pruebas Unitarias Automatizadas](#-pruebas-unitarias-automatizadas)
  - [🏛️ Créditos e Institución](#️-créditos-e-institución)
  - [📄 Licencia](#-licencia)

---

## 📌 Visión General

La espectroscopía Raman es una técnica fundamental en la caracterización no destructiva de bienes culturales muebles e inmuebles (códices, pintura mural, escultura policromada, textiles y cerámica). No obstante, los espectros experimentales suelen presentar retos analíticos complejos:
1. **Intensa fluorescencia de fondo** originada por aglutinantes orgánicos (gomas, colas, aceites, resinas) y minerales arcillosos que distorsionan las alturas relativas de las bandas.
2. **Picos espurios por rayos cósmicos** en sensores CCD durante adquisiciones de campo.
3. **Falta de herramientas integradas** para discriminar polimorfos cristalinos (ej. Calcita vs. Aragonita, Anatasa vs. Rutilo) y diagnosticar el estado de degradación o tensión de red mediante el ensanchamiento de banda (**FWHM**).

**Raman SpectroLab Pro** unifica la lectura universal multi-espectrómetro, la sustracción matemática rigurosa de fluorescencia, la deconstrucción de perfiles físicos y una base de datos patrimonial con cálculo de similitud multibanda en una interfaz gráfica optimizada de tema claro.

---

## ✨ Características Principales

### 🧹 Filtrado de Rayos Cósmicos (*Despiking*)
- **Derivada espacial con Z-Score modificado:** Detección de artefactos ultradelgados (1-2 pixeles) producidos por partículas de radiación ambiental en el CCD.
- **Interpolación no lineal:** Reemplazo suave y adaptativo del artefacto sin deformar las bandas vibracionales adyacentes de la muestra.

### 📉 Sustracción de Fluorescencia y Línea Base
- **ALS (*Asymmetric Least Squares* - Whittaker & Eilers):** Minimización de la función de costo con penalización por curvatura de segundo orden ($\lambda$) y pesos asimétricos ($p=0.01$).
- **AIRPLS (*Adaptive Iteratively Reweighted Penalized Least Squares*):** Ponderación adaptativa exponencial iterativa; excelente para fondos complejos con pendientes variables.
- **SNIP (*Statistics-sensitive Non-linear Iterative Peak-clipping*):** Algoritmo estándar de la IAEA para recorte iterativo no lineal.
- **ModPoly:** Ajuste polinomial iterativo modificado con umbral de recorte.

### 📐 Análisis de Bandas, Geometría y FWHM
- **Detección por Prominencia:** Medición de altura relativa local respecto al contorno circundante, eliminando el ruido electrónico ($0.8-2\%$) y preservando bandas secundarias clave.
- **FWHM Directo:** Estimado a la mitad de la altura máxima neta ($I_{\text{net}} / 2$).
- **Ajuste No Lineal de Perfiles (`curve_fit`):**
  - **Lorentziano:** Modelo físico fundamental de vida media del fonón en redes cristalinas.
  - **Gaussiano:** Ensanchamiento instrumental de monocromador y ranura óptica.
  - **Voigt:** Convolución física exacta (Lorentziano + Gaussiano).
- **Métricas Cuantitativas:** Centro de banda ($x_0\text{ cm}^{-1}$), Altura neta, FWHM ajustado, Área integrada y Coeficiente de Determinación ($R^2$).

### 🎨 Motor Arqueométrico y Diagnóstico Cristalográfico
- **Score Multibanda (% Match):** Ponderación probabilística entre la banda principal ($40\%$) y la concurrencia de bandas secundarias ($60\%$).
- **3 Modos de Enfoque Conmutables:**
  - `🔬 Vista Completa (Arqueometría)`: Perspectiva integral de pigmentos, minerales y soportes orgánicos.
  - `🎨 Solo Pigmentos Históricos`: Nombres vernáculos y patrimoniales (Azul Maya, Cinabrio, Grana Cochinilla, Minio, Oropimente, Blanco de Plomo, Cardenillo).
  - `💎 Solo Cristalografía / Minerales`: Grupos espaciales ($R\bar{3}c$, $Pmcn$, $I4_1/amd$, $P3_121$, etc.), diferenciación de polimorfos y diagnóstico de orden de red:
    - $\text{FWHM} \le 1.3 \times \text{ref}$: **Alta Cristalinidad / Cristales Sanos**.
    - $\text{FWHM} \le 2.2 \times \text{ref}$: **Tensiones de Red / Nanocristalino**.
    - $\text{FWHM} > 2.2 \times \text{ref}$: **Fase Amorfa / Degradada**.

### 📊 Modo Comparación con Línea Base en $y = 0$
- **Alineación de Piso Común:** Sustracción simultánea de línea base para todas las muestras superpuestas, situando todos los fondos en la recta horizontal $y=0$.
- **3 Modos de Visualización:**
  - `📏 Piso Cero y=0 (Intensidad Real)`: Permite evaluar directamente qué muestras presentan picos más intensos y mayor concentración de fase.
  - `🪜 Apilado en Cascada (Offset)`: Desplazamiento vertical progresivo ($+\Delta y$) para inspeccionar espectros sin encimamiento.
  - `📊 Normalizado (0 - 1)`: Escalamiento unitario para comparar únicamente morfología y desplazamientos espectrales.

### 📈 Análisis Estadístico Multivariado (PCA)
- **Descomposición por Valores Singulares (SVD):** Reducción de dimensionalidad sobre una cuadrícula interpolada homogénea.
- **Score Plot ($\text{PC}_1\text{ vs }\text{PC}_2$):** Representación bidimensional con varianza explicada acumulada para clasificación no supervisada de estratigrafías, talleres o fuentes de materia prima.

### 📦 Procesamiento y Exportación Masiva por Lote
- **Flujo Directo en Ventana Principal:** Sin pantallas modales intermedias; utiliza exactamente los parámetros calibrados en pantalla.
- **Generación en 1 Clic de:**
  - `Matriz_General_Lote_CODICE.xlsx`: Libro Excel consolidado con resumen de fases por muestra, diagnóstico de red y tabla de picos.
  - `Graficas_Procesadas_HD/`: Gráficas individuales rotuladas a 200 DPI.
  - `Datos_Limpios_CSV/`: Espectros sin fluorescencia ni ruido listos para software externo (Origin, QGIS).

---

## 🏗️ Arquitectura del Proyecto

```text
raman_spectroscopy/
├── raman_analysis.py       # Aplicación principal de escritorio GUI (Tkinter, Matplotlib, Eventos, Hilos)
├── raman_database.py       # Base de datos arqueométrica, cristalografía, polimorfos y motor de match
├── raman_processing.py     # Algoritmos numéricos: Despiking, ALS, AIRPLS, SNIP, FWHM, Lorentz/Voigt
├── lectura_raman.py        # Lector universal multi-formato, decodificación y cálculo Promedio/Suma
├── test_raman.py           # Suite completa de pruebas unitarias automatizadas (unittest)
├── run_raman.bat           # Iniciador automático para entornos Microsoft Windows
├── run_raman.sh            # Iniciador automático para sistemas Linux y macOS
├── requirements.txt        # Dependencias oficiales del entorno Python
├── LICENSE                 # Licencia libre copyleft GNU General Public License v3.0
└── README.md               # Documentación técnica y científica del sistema
```

---

## 📁 Formatos Soportados y Matriz de Exportación

### Formatos de Entrada
| Formato | Extensión | Descripción |
| :--- | :--- | :--- |
| **B&W Tek BWSpec** | `.txt` | Espectros brutos con metadatos de integración, láser y calibración. |
| **ASCII / CSV / TSV** | `.csv`, `.txt`, `.dat`, `.asc` | 2 columnas (Desplazamiento Raman $\text{cm}^{-1}$ vs Intensidad). Detección automática de comas y codificación (`UTF-8, Latin-1, CP1252`). |
| **Carga de Carpetas** | Carpetas | Ingesta masiva y cálculo instantáneo del **Espectro Promedio** y **Espectro Suma**. |

### Formatos y Matriz de Salida
| Destino | Formato | Detalle Técnico |
| :--- | :--- | :--- |
| **Portapapeles del Sistema** | `Ctrl+C` | Formato nativo Win32 `CF_DIB` de 64 bits a 200 DPI para pegado directo en Word/PowerPoint. |
| **Gráficas Individuales HD** | `PNG`, `PDF`, `SVG`, `EPS` | Exportación vectorial y mapa de bits a 300 DPI con rotulado institucional. |
| **Reporte Muestra Actual** | `Excel (.xlsx)` | Pestañas con tabla de picos, ajuste Lorentziano/Voigt y espectro numérico limpio. |
| **Matriz General de Lote** | `Excel (.xlsx)` | Matriz consolidada de todas las muestras del proyecto con diagnósticos de certeza y FWHM. |
| **Datos Procesados** | `CSV (.csv)` | Archivos tabulados con el espectro corregido sin fluorescencia. |

---

## 💻 Instalación y Requisitos del Sistema

### Requisitos Previos
- **Python 3.9 o superior** ([python.org](https://www.python.org/downloads/)). *En Windows, asegúrate de marcar la casilla "Add Python to PATH" durante la instalación.*

### Opción 1: Windows (Iniciador Automático en 1 Clic)
1. Descarga o clona este repositorio en tu computadora o memoria USB.
2. Haz **doble clic en [`run_raman.bat`](run_raman.bat)**.
   * *El script creará automáticamente el entorno virtual `.venv`, instalará las dependencias y abrirá la aplicación.*

### Opción 2: Linux / macOS (Terminal)
```bash
# 1. Clonar el repositorio
git clone https://github.com/Geenska/raman_spectroscopy.git
cd raman_spectroscopy

# 2. Dar permisos de ejecución e iniciar
chmod +x run_raman.sh
./run_raman.sh
```

---

## ⚡ Guía Rápida de Flujo de Trabajo

1. **Cargar Espectros:** Arrastra una carpeta de datos a la ventana o usa `[ 📂 Cargar Archivo(s) ]` / `[ 📁 Cargar Carpeta ]`.
2. **Calibrar Parámetros en Vivo:**
   - Selecciona el algoritmo de línea base preferido ($\text{ALS}$ predeterminado con $\lambda = 10^5$).
   - Ajusta el umbral de prominencia de picos ($3.0\%$ predeterminado).
   - Elige el modelo de perfil de pico ($\text{Lorentziano, Gaussiano o Voigt}$).
3. **Seleccionar Enfoque:** Conmuta entre `🔬 Vista Completa`, `🎨 Solo Pigmentos` o `💎 Solo Cristalografía`.
4. **Comparar Muestras:** Activa `[☑ Activar Superposición de Selección]` o presiona `[ ☑ Superponer Todas las Muestras ]` para comparar las curvas ancladas sobre la horizontal $y = 0$.
5. **Exportar Resultados:**
   - Presiona `Ctrl + C` para copiar la gráfica actual en alta resolución.
   - Presiona `[ 📦 Exportar Todo el Lote (Excel + HD) ]` para generar el reporte maestro consolidado de todas las muestras en un solo paso.

---

## 🧪 Pruebas Unitarias Automatizadas

El proyecto cuenta con una suite rigurosa de pruebas automatizadas que validan la lectura de formatos, la sustracción de línea base, el cálculo de FWHM y el motor de identificación:

```bash
python test_raman.py
```

---

## 🏛️ Créditos e Institución

Proyecto concebido y desarrollado para el **Laboratorio CÓDICE** y la **CNCPC** (*Coordinación Nacional de Conservación del Patrimonio Cultural - Instituto Nacional de Antropología e Historia, INAH*), con el objetivo de estandarizar, acelerar y fortalecer los estudios analíticos de caracterización de materiales patrimoniales en México.

---

## 📄 Licencia

Este proyecto se distribuye bajo los términos de la licencia libre y de código abierto **GNU General Public License v3.0 (GPL-3.0)**. Consulta el archivo [`LICENSE`](LICENSE) para obtener más información.

