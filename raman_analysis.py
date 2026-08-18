"""
Raman SpectroLab Pro - Aplicación de Escritorio para Procesamiento Espectral Raman.
Incluye:
- Interfaz en Tema Claro (Light Mode) de laboratorio
- Visualización espectral interactiva con Matplotlib y Tkinter
- Sustracción de Línea Base (ALS, AIRPLS, SNIP, Polinomial)
- Despiking y cálculo de FWHM (Directo y Ajuste de Perfil Lorentziano/Gaussiano/Voigt)
- Identificación específica de fases minerales, fórmula química y estado cristalino (FWHM)
- Análisis Multivariado PCA
- Exportación a Excel y CSV
"""

import os
import sys
import io
import time
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False
    TkinterDnD = object

import lectura_raman
import raman_processing
import raman_database

try:
    from sklearn.decomposition import PCA
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class RamanAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Laboratorio CODICE - Espectroscopia Raman | CNCPC")
        self.root.geometry("1450x880")
        self.root.minsize(1100, 720)
        
        # Variables de estado de datos
        self.espectros_cargados = []
        self.espectro_actual = None
        self.resultado_procesado = None
        
        # Variables de control de visualización y enfoque de análisis
        self.var_modo_analisis = tk.StringVar(value="🔬 Vista Completa (Arqueometría)")
        self.var_modo_comparacion = tk.StringVar(value="📏 Piso Cero y=0 (Intensidad Real)")
        self.var_show_labels = tk.BooleanVar(value=True)
        self.var_label_style = tk.StringVar(value="Posición + FWHM")
        self.var_max_labels = tk.StringVar(value="10")
        self.var_show_fwhm_lines = tk.BooleanVar(value=True)
        
        # Configurar Estilos Tkinter (Tema Claro)
        self._configurar_estilos()
        
        # Crear Interfaz
        self._crear_interfaz()
        
        # Registrar eventos Drag and Drop
        self._registrar_drag_and_drop()
        
        # Atajos de teclado
        self.root.bind('<Control-c>', lambda e: self.copiar_grafica_portapapeles())
        self.root.bind('<Control-C>', lambda e: self.copiar_grafica_portapapeles())

    def copiar_grafica_portapapeles(self):
        """
        Copia la figura actual de Matplotlib al portapapeles del sistema (Windows o Linux)
        en alta resolución (200 DPI) para pegado directo en Word, PowerPoint, Paint, etc.
        Implementación Win32 API de 64 bits garantizada idéntica a xrf_analysis.
        """
        copiado = False
        try:
            # 1. En sistemas Windows (32-bit y 64-bit nativo con Win32 API)
            if sys.platform.startswith('win'):
                import ctypes
                from ctypes import wintypes
                
                output = io.BytesIO()
                self.fig.savefig(output, format='bmp', dpi=200, bbox_inches='tight', facecolor=self.fig.get_facecolor())
                data = output.getvalue()[14:]  # Omitir los 14 bytes del encabezado BMP para obtener formato CF_DIB
                output.close()
                
                user32 = ctypes.windll.user32
                kernel32 = ctypes.windll.kernel32
                
                # Configurar firma explícita de tipos (argtypes/restype) para evitar truncamiento de punteros a 32 bits en Python 64-bit
                kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
                kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
                kernel32.GlobalLock.restype = wintypes.LPVOID
                kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
                kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
                
                user32.OpenClipboard.argtypes = [wintypes.HWND]
                user32.OpenClipboard.restype = wintypes.BOOL
                user32.EmptyClipboard.restype = wintypes.BOOL
                user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
                user32.SetClipboardData.restype = wintypes.HANDLE
                user32.CloseClipboard.restype = wintypes.BOOL
                
                CF_DIB = 8
                GMEM_MOVEABLE = 0x0002
                
                # Reintentar abrir el portapapeles por si otra aplicación de Windows lo tiene ocupado
                opened = False
                for _ in range(5):
                    if user32.OpenClipboard(None):
                        opened = True
                        break
                    time.sleep(0.05)
                    
                if not opened:
                    raise RuntimeError("El portapapeles está bloqueado momentáneamente por otra aplicación de Windows.")
                    
                try:
                    user32.EmptyClipboard()
                    h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
                    if not h_mem:
                        raise MemoryError("No se pudo asignar memoria global para la imagen.")
                        
                    p_mem = kernel32.GlobalLock(h_mem)
                    if not p_mem:
                        raise MemoryError("No se pudo bloquear la memoria para escribir la imagen.")
                        
                    ctypes.memmove(p_mem, data, len(data))
                    kernel32.GlobalUnlock(h_mem)
                    
                    if not user32.SetClipboardData(CF_DIB, h_mem):
                        raise RuntimeError("Falló al transferir los datos al portapapeles de Windows.")
                    copiado = True
                finally:
                    user32.CloseClipboard()
                    
            # 2. En sistemas Linux / macOS
            else:
                output = io.BytesIO()
                self.fig.savefig(output, format='png', dpi=200, bbox_inches='tight', facecolor=self.fig.get_facecolor())
                png_data = output.getvalue()
                output.close()
                
                # Probar wl-copy (Wayland)
                try:
                    p = subprocess.Popen(['wl-copy', '-t', 'image/png'], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
                    p.communicate(input=png_data)
                    if p.returncode == 0:
                        copiado = True
                except Exception:
                    pass
                    
                # Probar xclip (X11)
                if not copiado:
                    try:
                        p = subprocess.Popen(['xclip', '-selection', 'clipboard', '-target', 'image/png'], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
                        p.communicate(input=png_data)
                        if p.returncode == 0:
                            copiado = True
                    except Exception:
                        pass
                        
            if copiado:
                if hasattr(self, 'btn_copy_graph'):
                    self.btn_copy_graph.config(text="✓ ¡Gráfica Copiada!")
                    self.root.after(2000, lambda: self.btn_copy_graph.config(text="📋 Copiar (Ctrl+C)"))
            else:
                if not sys.platform.startswith('win'):
                    messagebox.showinfo("Copiar Gráfica", "Para copiar al portapapeles en Linux instala 'xclip' o 'wl-clipboard':\n\nsudo pacman -S xclip wl-clipboard")
                else:
                    messagebox.showwarning("Atención", "No se pudo copiar la imagen al portapapeles.")
        except Exception as e:
            messagebox.showerror("Error al copiar gráfica", str(e))

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Paleta de colores TEMA CLARO (Light Theme)
        bg_main = '#f4f6f8'       # Fondo principal gris claro suave
        bg_card = '#ffffff'       # Blanco para tarjetas y contenedores
        fg_dark = '#212529'       # Texto oscuro principal
        accent_blue = '#0d6efd'   # Azul primario profesional
        border_color = '#dee2e6'  # Bordes gris tenue
        
        self.root.configure(bg=bg_main)
        
        style.configure('.', background=bg_main, foreground=fg_dark, font=('Segoe UI', 10))
        style.configure('TFrame', background=bg_main)
        style.configure('TLabelframe', background=bg_card, foreground=accent_blue, font=('Segoe UI', 10, 'bold'), borderwidth=1, relief='solid')
        style.configure('TLabelframe.Label', background=bg_card, foreground=accent_blue)
        
        style.configure('TButton', background='#e9ecef', foreground=fg_dark, borderwidth=1, focuscolor=accent_blue, font=('Segoe UI', 9))
        style.map('TButton', background=[('active', '#dee2e6'), ('pressed', '#cef0f5')])
        
        style.configure('Treeview', background=bg_card, foreground=fg_dark, fieldbackground=bg_card, rowheight=26, borderwidth=1, relief='solid')
        style.configure('Treeview.Heading', background='#e9ecef', foreground=fg_dark, font=('Segoe UI', 9, 'bold'))
        style.map('Treeview', background=[('selected', '#e7f1ff')], foreground=[('selected', '#0d6efd')])

    def _crear_interfaz(self):
        # -------------------------------------------------------------
        # CABECERA SUPERIOR (HEADER PANEL)
        # -------------------------------------------------------------
        header_frame = ttk.Frame(self.root, padding=(18, 10))
        header_frame.pack(fill=tk.X)
        
        header_label = ttk.Label(
            header_frame, 
            text="🔬 Laboratorio CODICE - Espectroscopia Raman", 
            font=('Segoe UI', 15, 'bold'), 
            foreground='#0d6efd'
        )
        header_label.pack(anchor='w')

        subtitle_label = ttk.Label(
            header_frame, 
            text="CNCPC - Procesamiento e Interpretación de Espectros Raman", 
            font=('Segoe UI', 9, 'italic'), 
            foreground='#6c757d'
        )
        subtitle_label.pack(anchor='w', pady=(2, 0))

        # Línea divisoria tenue
        sep = ttk.Separator(self.root, orient='horizontal')
        sep.pack(fill=tk.X, padx=8, pady=(0, 4))

        # -------------------------------------------------------------
        # CONTENEDOR PRINCIPAL
        # -------------------------------------------------------------
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        
        # Panel izquierdo con ancho garantizado (430px) y barra de desplazamiento vertical
        left_container = ttk.Frame(main_container, width=430)
        left_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))
        left_container.pack_propagate(False)
        
        self.left_canvas = tk.Canvas(left_container, bg='#f4f6f8', bd=0, highlightthickness=0)
        self.left_scrollbar = ttk.Scrollbar(left_container, orient="vertical", command=self.left_canvas.yview)
        
        self.left_content = ttk.Frame(self.left_canvas)
        self.left_window = self.left_canvas.create_window((0, 0), window=self.left_content, anchor="nw")
        
        def _on_left_canvas_configure(event):
            self.left_canvas.itemconfig(self.left_window, width=event.width)
            
        def _on_left_content_configure(event):
            self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))
            
        self.left_canvas.bind("<Configure>", _on_left_canvas_configure)
        self.left_content.bind("<Configure>", _on_left_content_configure)
        self.left_canvas.configure(yscrollcommand=self.left_scrollbar.set)
        
        self.left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Vincular rueda del ratón (MouseWheel en Windows y Button-4/Button-5 en Linux)
        def _on_mousewheel(event):
            if event.delta:
                self.left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:
                self.left_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.left_canvas.yview_scroll(1, "units")

        def _bind_mousewheel(event):
            self.root.bind_all("<MouseWheel>", _on_mousewheel)
            self.root.bind_all("<Button-4>", _on_mousewheel)
            self.root.bind_all("<Button-5>", _on_mousewheel)

        def _unbind_mousewheel(event):
            self.root.unbind_all("<MouseWheel>")
            self.root.unbind_all("<Button-4>")
            self.root.unbind_all("<Button-5>")

        left_container.bind("<Enter>", _bind_mousewheel)
        left_container.bind("<Leave>", _unbind_mousewheel)
        
        # Panel derecho que ocupa todo el espacio restante para la gráfica y la tabla
        right_frame = ttk.Frame(main_container)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self._crear_panel_izquierdo(self.left_content)
        self._crear_panel_derecho(right_frame)

    def _crear_panel_izquierdo(self, parent):
        # 1. Grupo Archivos
        frame_files = ttk.LabelFrame(parent, text=" 📁 Archivos de Espectros ")
        frame_files.pack(fill=tk.BOTH, expand=False, padx=6, pady=5)
        
        # Zona visual para Drag & Drop
        self.lbl_drop = tk.Label(
            frame_files,
            text="📥 Arrastra y suelta espectros (.txt, .csv) o carpetas aquí",
            bg='#e9ecef', fg='#495057', font=('Segoe UI', 8, 'italic'),
            relief='groove', bd=1, pady=6
        )
        self.lbl_drop.pack(fill=tk.X, padx=6, pady=(6, 4))
        
        # Botones de Carga y Gestión
        btn_grid = ttk.Frame(frame_files)
        btn_grid.pack(fill=tk.X, padx=6, pady=2)
        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)
        
        btn_cargar_file = ttk.Button(btn_grid, text="📄 Abrir Archivo(s)", command=self.abrir_archivo)
        btn_cargar_file.grid(row=0, column=0, sticky='ew', padx=2, pady=2)
        
        btn_cargar_dir = ttk.Button(btn_grid, text="📂 Abrir Carpeta", command=self.abrir_directorio)
        btn_cargar_dir.grid(row=0, column=1, sticky='ew', padx=2, pady=2)
        
        btn_quitar = ttk.Button(btn_grid, text="❌ Quitar Selección", command=self.quitar_seleccionados)
        btn_quitar.grid(row=1, column=0, sticky='ew', padx=2, pady=2)
        
        btn_limpiar = ttk.Button(btn_grid, text="🗑️ Limpiar Todo", command=self.limpiar_lista)
        btn_limpiar.grid(row=1, column=1, sticky='ew', padx=2, pady=2)
        
        # Treeview de Archivos con Scrollbar
        tree_container = ttk.Frame(frame_files)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        
        self.tree_files = ttk.Treeview(tree_container, columns=('format',), selectmode='extended', height=6)
        self.tree_files.heading('#0', text='Muestra / Espectro')
        self.tree_files.heading('format', text='Formato')
        self.tree_files.column('#0', width=260, minwidth=180, anchor='w')
        self.tree_files.column('format', width=90, minwidth=70, anchor='center')
        
        scroll_tree = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree_files.yview)
        self.tree_files.configure(yscroll=scroll_tree.set)
        
        self.tree_files.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_tree.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree_files.bind('<<TreeviewSelect>>', self._al_seleccionar_espectro)
        self.tree_files.bind('<Delete>', self.quitar_seleccionados)
        self.tree_files.bind('<BackSpace>', self.quitar_seleccionados)
        
        # Opciones de Comparación / Superposición
        frame_overlay = ttk.LabelFrame(frame_files, text=" 📊 Modo Comparación / Superposición ", padding=(6, 4))
        frame_overlay.pack(fill=tk.X, padx=6, pady=(3, 6))
        
        self.var_overlay = tk.BooleanVar(value=False)
        chk_overlay = ttk.Checkbutton(frame_overlay, text="Activar Superposición de Selección", variable=self.var_overlay, command=self._al_cambiar_check_overlay)
        chk_overlay.pack(anchor='w', pady=(1, 2))
        
        ttk.Button(frame_overlay, text="☑ Superponer Todas las Muestras", command=self.seleccionar_todos_espectros).pack(fill=tk.X, pady=(0, 3))
        
        ttk.Label(frame_overlay, text="Alineación de Línea Base:").pack(anchor='w')
        self.combo_comp_mode = ttk.Combobox(
            frame_overlay,
            values=[
                "📏 Piso Cero y=0 (Intensidad Real)",
                "🪜 Apilado en Cascada (Offset)",
                "📊 Normalizado (0 - 1)"
            ],
            textvariable=self.var_modo_comparacion,
            state="readonly",
            width=28
        )
        self.combo_comp_mode.pack(fill=tk.X, pady=(2, 2))
        self.combo_comp_mode.bind("<<ComboboxSelected>>", lambda e: self.actualizar_analisis())
        
        # 2. Grupo Parámetros de Procesamiento
        frame_params = ttk.LabelFrame(parent, text=" ⚙️ Parámetros de Procesamiento ")
        frame_params.pack(fill=tk.BOTH, expand=True, padx=6, pady=5)
        
        self.var_despike = tk.BooleanVar(value=True)
        chk_despike = ttk.Checkbutton(frame_params, text="Filtro de Rayos Cósmicos (Despiking)", variable=self.var_despike, command=self.actualizar_analisis)
        chk_despike.pack(anchor='w', padx=6, pady=2)
        
        self.var_show_raw = tk.BooleanVar(value=False)
        chk_show_raw = ttk.Checkbutton(frame_params, text="Mostrar Espectro Bruto y Línea Base", variable=self.var_show_raw, command=self.actualizar_analisis)
        chk_show_raw.pack(anchor='w', padx=6, pady=2)
        
        ttk.Separator(frame_params, orient='horizontal').pack(fill=tk.X, padx=6, pady=4)
        
        ttk.Label(frame_params, text="Algoritmo de Línea Base:").pack(anchor='w', padx=6, pady=(3, 1))
        self.combo_baseline = ttk.Combobox(frame_params, values=['ALS (Asymmetric Least Squares)', 'AIRPLS (Adaptive Iterative)', 'SNIP (Peak Clipping)', 'Polynomial ModPoly'], state='readonly')
        self.combo_baseline.current(0)
        self.combo_baseline.pack(fill=tk.X, padx=6, pady=2)
        self.combo_baseline.bind('<<ComboboxSelected>>', lambda e: self.actualizar_analisis())
        
        # Slider Lambda con etiqueta de valor
        frame_lam = ttk.Frame(frame_params)
        frame_lam.pack(fill=tk.X, padx=6, pady=3)
        frame_lam_top = ttk.Frame(frame_lam)
        frame_lam_top.pack(fill=tk.X)
        ttk.Label(frame_lam_top, text="Suavidad Línea Base (Lambda log₁₀):").pack(side=tk.LEFT)
        self.lbl_lambda_val = ttk.Label(frame_lam_top, text="10⁵·⁰", font=('Segoe UI', 9, 'bold'), foreground='#0d6efd')
        self.lbl_lambda_val.pack(side=tk.RIGHT)
        self.slider_lambda = ttk.Scale(frame_lam, from_=2.0, to=8.0, value=5.0, command=self._al_cambiar_lambda)
        self.slider_lambda.pack(fill=tk.X, pady=(2, 0))
        
        # Slider Prominencia con etiqueta de valor
        frame_sens = ttk.Frame(frame_params)
        frame_sens.pack(fill=tk.X, padx=6, pady=3)
        frame_sens_top = ttk.Frame(frame_sens)
        frame_sens_top.pack(fill=tk.X)
        ttk.Label(frame_sens_top, text="Prominencia Mínima de Picos:").pack(side=tk.LEFT)
        self.lbl_prom_val = ttk.Label(frame_sens_top, text="3.0%", font=('Segoe UI', 9, 'bold'), foreground='#0d6efd')
        self.lbl_prom_val.pack(side=tk.RIGHT)
        self.slider_prom = ttk.Scale(frame_sens, from_=0.5, to=20.0, value=3.0, command=self._al_cambiar_prom)
        self.slider_prom.pack(fill=tk.X, pady=(2, 0))
        
        ttk.Label(frame_params, text="Perfil de Ajuste FWHM:").pack(anchor='w', padx=6, pady=(4, 1))
        self.combo_shape = ttk.Combobox(frame_params, values=['lorentzian', 'gaussian', 'voigt'], state='readonly')
        self.combo_shape.current(0)
        self.combo_shape.pack(fill=tk.X, padx=6, pady=2)
        self.combo_shape.bind('<<ComboboxSelected>>', lambda e: self.actualizar_analisis())
        
        ttk.Separator(frame_params, orient='horizontal').pack(fill=tk.X, padx=6, pady=4)
        
        btn_reproc = ttk.Button(frame_params, text="🔄 Reprocesar Espectro", command=self.actualizar_analisis)
        btn_reproc.pack(fill=tk.X, padx=6, pady=2)
        
        if HAS_SKLEARN:
            btn_pca = ttk.Button(frame_params, text="📈 Análisis Multivariado (PCA)", command=self.ejecutar_pca)
            btn_pca.pack(fill=tk.X, padx=6, pady=2)
            
        btn_export = ttk.Button(frame_params, text="💾 Exportar Muestra Actual (Excel)", command=self.exportar_excel)
        btn_export.pack(fill=tk.X, padx=6, pady=(3, 2))
        
        btn_batch = ttk.Button(frame_params, text="📦 Exportar Todo el Lote (Excel + HD)", command=self.exportar_lote_completo)
        btn_batch.pack(fill=tk.X, padx=6, pady=(2, 2))

    def _programar_actualizacion(self, delay_ms=45):
        if hasattr(self, '_timer_reproc') and self._timer_reproc:
            try:
                self.root.after_cancel(self._timer_reproc)
            except Exception:
                pass
        self._timer_reproc = self.root.after(delay_ms, self.actualizar_analisis)

    def _al_cambiar_lambda(self, val):
        v = float(val)
        if hasattr(self, 'lbl_lambda_val'):
            self.lbl_lambda_val.config(text=f"10^{v:.1f}")
        self._programar_actualizacion()

    def _al_cambiar_prom(self, val):
        v = float(val)
        if hasattr(self, 'lbl_prom_val'):
            self.lbl_prom_val.config(text=f"{v:.1f}%")
        self._programar_actualizacion()

    def _crear_panel_derecho(self, parent):
        # 1. Barra Superior de Herramientas de la Gráfica (Copiar + Guardar HD + Selector de Enfoque + Etiquetas + FWHM)
        graph_ctrl_box = ttk.Frame(parent)
        graph_ctrl_box.pack(fill=tk.X, padx=5, pady=(2, 3))
        
        self.btn_copy_graph = ttk.Button(
            graph_ctrl_box,
            text="📋 Copiar (Ctrl+C)",
            command=self.copiar_grafica_portapapeles
        )
        self.btn_copy_graph.pack(side=tk.LEFT, padx=(0, 3))
        
        btn_save_hd = ttk.Button(
            graph_ctrl_box,
            text="💾 Guardar HD",
            command=self.exportar_figura_hd
        )
        btn_save_hd.pack(side=tk.LEFT, padx=(0, 6))
        
        ttk.Separator(graph_ctrl_box, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=2)
        
        ttk.Label(graph_ctrl_box, text="Enfoque:").pack(side=tk.LEFT, padx=(4, 2))
        self.combo_modo = ttk.Combobox(
            graph_ctrl_box,
            values=["🔬 Vista Completa (Arqueometría)", "🎨 Solo Pigmentos Históricos", "💎 Solo Cristalografía / Minerales"],
            textvariable=self.var_modo_analisis,
            state="readonly",
            width=28
        )
        self.combo_modo.pack(side=tk.LEFT, padx=2)
        self.combo_modo.bind("<<ComboboxSelected>>", lambda e: self.actualizar_analisis())
        
        ttk.Separator(graph_ctrl_box, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=2)
        
        chk_labels = ttk.Checkbutton(
            graph_ctrl_box,
            text="🏷️ Etiquetas",
            variable=self.var_show_labels,
            command=self.actualizar_analisis
        )
        chk_labels.pack(side=tk.LEFT, padx=(4, 2))
        
        ttk.Label(graph_ctrl_box, text="Estilo:").pack(side=tk.LEFT, padx=(4, 2))
        self.combo_label_style = ttk.Combobox(
            graph_ctrl_box,
            values=["Posición + FWHM", "Solo Posición", "Posición + Fase"],
            textvariable=self.var_label_style,
            state="readonly",
            width=14
        )
        self.combo_label_style.pack(side=tk.LEFT, padx=2)
        self.combo_label_style.bind("<<ComboboxSelected>>", lambda e: self.actualizar_analisis())
        
        ttk.Label(graph_ctrl_box, text="Máx:").pack(side=tk.LEFT, padx=(4, 2))
        self.combo_max_labels = ttk.Combobox(
            graph_ctrl_box,
            values=["5", "10", "15", "Todos"],
            textvariable=self.var_max_labels,
            state="readonly",
            width=5
        )
        self.combo_max_labels.pack(side=tk.LEFT, padx=2)
        self.combo_max_labels.bind("<<ComboboxSelected>>", lambda e: self.actualizar_analisis())
        
        chk_fwhm = ttk.Checkbutton(
            graph_ctrl_box,
            text="📐 FWHM",
            variable=self.var_show_fwhm_lines,
            command=self.actualizar_analisis
        )
        chk_fwhm.pack(side=tk.LEFT, padx=4)
        
        # 2. Gráfica Matplotlib con fondo claro puro
        self.fig = Figure(figsize=(8, 4.8), dpi=100, facecolor='#ffffff')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#ffffff')
        self.ax.tick_params(colors='#212529', which='both')
        for spine in self.ax.spines.values():
            spine.set_color('#ced4da')
            
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.draw()
        
        # Barra de navegación + Coordenadas en tiempo real
        nav_bar_frame = ttk.Frame(parent)
        nav_bar_frame.pack(fill=tk.X, padx=5)
        
        self.toolbar = NavigationToolbar2Tk(self.canvas, nav_bar_frame)
        self.toolbar.update()
        
        self.lbl_coords = ttk.Label(nav_bar_frame, text="X: --- cm⁻¹  |  Y: --- U.A.", font=('Segoe UI', 9, 'bold'), foreground='#0d6efd')
        self.lbl_coords.pack(side=tk.RIGHT, padx=8, pady=3)
        
        self.canvas.mpl_connect('motion_notify_event', self._al_mover_raton)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=(2, 2))
        
        # 3. Tabla de Picos e Identificación (Compacta para maximizar la gráfica)
        frame_table = ttk.LabelFrame(parent, text=" 📊 Tabla de Picos, FWHM, Fases y Cristalografía ")
        frame_table.pack(fill=tk.X, expand=False, padx=5, pady=(2, 4))
        
        cols = ('pos', 'raw_int', 'net_int', 'fwhm_dir', 'fwhm_fit', 'area', 'r2', 'compound')
        self.tree_peaks = ttk.Treeview(frame_table, columns=cols, show='headings', height=4)
        
        self.tree_peaks.heading('pos', text='Posición (cm⁻¹)')
        self.tree_peaks.heading('raw_int', text='Int. Bruta')
        self.tree_peaks.heading('net_int', text='Int. Neta')
        self.tree_peaks.heading('fwhm_dir', text='FWHM Directo')
        self.tree_peaks.heading('fwhm_fit', text='FWHM Ajuste')
        self.tree_peaks.heading('area', text='Área Neta')
        self.tree_peaks.heading('r2', text='R² Ajuste')
        self.tree_peaks.heading('compound', text='Identificación Candidata (Fórmula / FWHM / Sistema Cristalino)')
        
        self.tree_peaks.column('pos', width=105, anchor='center')
        self.tree_peaks.column('raw_int', width=85, anchor='center')
        self.tree_peaks.column('net_int', width=85, anchor='center')
        self.tree_peaks.column('fwhm_dir', width=105, anchor='center')
        self.tree_peaks.column('fwhm_fit', width=105, anchor='center')
        self.tree_peaks.column('area', width=95, anchor='center')
        self.tree_peaks.column('r2', width=75, anchor='center')
        self.tree_peaks.column('compound', width=380, anchor='w')
        
        scrollbar = ttk.Scrollbar(frame_table, orient=tk.VERTICAL, command=self.tree_peaks.yview)
        self.tree_peaks.configure(yscroll=scrollbar.set)
        
        self.tree_peaks.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _al_mover_raton(self, event):
        if hasattr(self, 'lbl_coords') and event.inaxes == self.ax and event.xdata is not None and event.ydata is not None:
            self.lbl_coords.config(text=f"X: {event.xdata:.1f} cm⁻¹  |  Y: {event.ydata:.1f} U.A.")
        elif hasattr(self, 'lbl_coords'):
            self.lbl_coords.config(text="X: --- cm⁻¹  |  Y: --- U.A.")

    def exportar_figura_hd(self):
        """
        Exporta la gráfica en formato vectorial (PDF, SVG) o mapa de bits de alta resolución (PNG 300 DPI).
        """
        filepath = filedialog.asksaveasfilename(
            title="Guardar Figura en Alta Resolución",
            defaultextension=".png",
            filetypes=[
                ("Imagen PNG Alta Resolución (300 DPI)", "*.png"),
                ("Documento Vectorial PDF", "*.pdf"),
                ("Gráfico Vectorial Escalable SVG", "*.svg"),
                ("PostScript Encapsulado EPS", "*.eps")
            ]
        )
        if filepath:
            try:
                ext = os.path.splitext(filepath)[1].lower()
                dpi = 300 if ext in ['.png', '.jpg'] else None
                self.fig.savefig(filepath, dpi=dpi, bbox_inches='tight', facecolor=self.fig.get_facecolor())
                messagebox.showinfo("Exportación Exitosa", f"Figura guardada correctamente en:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error al exportar figura", str(e))

    def _registrar_drag_and_drop(self):
        if HAS_DND:
            widgets_drop = [self.tree_files, self.lbl_drop, self.left_canvas, self.canvas.get_tk_widget(), self.root]
            for w in widgets_drop:
                try:
                    w.drop_target_register(DND_FILES)
                    w.dnd_bind('<<Drop>>', self._procesar_drop)
                except Exception as e:
                    print(f"[DnD] Registro omitido para widget: {e}")

    def _procesar_drop(self, event):
        try:
            rutas = self.root.tk.splitlist(event.data)
            self.cargar_rutas(list(rutas))
        except Exception as e:
            messagebox.showerror("Error al procesar archivos arrastrados", str(e))

    def abrir_archivo(self):
        filenames = filedialog.askopenfilenames(
            title="Seleccionar espectro(s) Raman",
            filetypes=[("Archivos Espectrales", "*.txt *.csv *.asc *.tsv *.dat"), ("Todos los archivos", "*.*")]
        )
        if filenames:
            self.cargar_rutas(list(filenames))

    def abrir_directorio(self):
        dir_path = filedialog.askdirectory(title="Seleccionar carpeta con espectros Raman")
        if dir_path:
            self.cargar_rutas([dir_path])

    def cargar_rutas(self, rutas):
        extensiones = ('.txt', '.csv', '.asc', '.tsv', '.dat')
        nuevos = []
        
        for r in rutas:
            r = os.path.abspath(r.strip('{}'))
            if os.path.isdir(r):
                specs_dir = lectura_raman.cargar_directorio_raman(r)
                for sp in specs_dir:
                    if not any(e.get('ruta') == sp.get('ruta') and e.get('nombre') == sp.get('nombre') for e in self.espectros_cargados):
                        nuevos.append(sp)
            elif os.path.isfile(r) and r.lower().endswith(extensiones):
                if not any(e.get('ruta') == r for e in self.espectros_cargados):
                    try:
                        spec = lectura_raman.cargar_espectro_raman(r)
                        nuevos.append(spec)
                    except Exception as err:
                        print(f"[Error de lectura] {r}: {err}")
                        
        if nuevos:
            prev_len = len(self.espectros_cargados)
            self.espectros_cargados.extend(nuevos)
            self._actualizar_lista_archivos(select_idx=prev_len)
        elif not self.espectros_cargados:
            messagebox.showwarning("Advertencia", "No se encontraron espectros Raman compatibles para cargar.")

    def quitar_seleccionados(self, event=None):
        sel = self.tree_files.selection()
        if not sel:
            return
        indices_a_quitar = set(int(i) for i in sel if i.isdigit())
        self.espectros_cargados = [sp for idx, sp in enumerate(self.espectros_cargados) if idx not in indices_a_quitar]
        self._actualizar_lista_archivos()

    def limpiar_lista(self):
        if not self.espectros_cargados:
            return
        if messagebox.askyesno("Confirmar", "¿Deseas vaciar toda la lista de espectros cargados?"):
            self.espectros_cargados = []
            self.espectro_actual = None
            self.resultado_procesado = None
            self._actualizar_lista_archivos()

    def _actualizar_lista_archivos(self, select_idx=None):
        for item in self.tree_files.get_children():
            self.tree_files.delete(item)
            
        for i, sp in enumerate(self.espectros_cargados):
            self.tree_files.insert('', 'end', iid=str(i), text=sp['nombre'], values=(sp['formato'],))
            
        if self.espectros_cargados:
            target_idx = 0 if select_idx is None or select_idx >= len(self.espectros_cargados) else select_idx
            self.tree_files.selection_set(str(target_idx))
            self.espectro_actual = self.espectros_cargados[target_idx]
            self.actualizar_analisis()
        else:
            self.espectro_actual = None
            self.resultado_procesado = None
            self.ax.clear()
            self.canvas.draw()
            for item in self.tree_peaks.get_children():
                self.tree_peaks.delete(item)

    def seleccionar_todos_espectros(self):
        items = self.tree_files.get_children()
        items_a_sel = [it for it in items if int(it) < len(self.espectros_cargados) and '--- ESPECTRO' not in self.espectros_cargados[int(it)]['nombre']]
        if not items_a_sel:
            items_a_sel = list(items)
        if items_a_sel:
            self.tree_files.selection_set(items_a_sel)
            self.var_overlay.set(True)
            self.actualizar_analisis()


    def _al_cambiar_check_overlay(self):
        if self.var_overlay.get():
            sel = self.tree_files.selection()
            if len(sel) <= 1:
                # Si solo hay uno o ninguno seleccionado, seleccionamos todas las muestras individuales
                items = self.tree_files.get_children()
                items_a_sel = [it for it in items if int(it) < len(self.espectros_cargados) and '--- ESPECTRO' not in self.espectros_cargados[int(it)]['nombre']]
                if not items_a_sel:
                    items_a_sel = list(items)
                if items_a_sel:
                    self.tree_files.selection_set(items_a_sel)
        else:
            # Si se desactivó la casilla, dejamos solo 1 seleccionado
            sel = self.tree_files.selection()
            if len(sel) > 1:
                primer_item = sel[0]
                self.tree_files.selection_set(primer_item)
                if primer_item.isdigit() and int(primer_item) < len(self.espectros_cargados):
                    self.espectro_actual = self.espectros_cargados[int(primer_item)]
        self.actualizar_analisis()

    def _al_seleccionar_espectro(self, event):
        sel = self.tree_files.selection()
        if not sel:
            return
            
        indices = [int(i) for i in sel if i.isdigit() and int(i) < len(self.espectros_cargados)]
        if len(indices) == 1:
            self.espectro_actual = self.espectros_cargados[indices[0]]
            self.var_overlay.set(False)
        elif len(indices) > 1:
            self.var_overlay.set(True)
            
        self.actualizar_analisis()

    def actualizar_analisis(self):
        sel = self.tree_files.selection()
        indices = [int(i) for i in sel if i.isdigit() and int(i) < len(self.espectros_cargados)]
        
        # Si la casilla de superposición está activa pero solo hay 1 seleccionado,
        # tomar todas las muestras individuales para superponerlas
        if self.var_overlay.get() and len(indices) <= 1:
            indices = [i for i, s in enumerate(self.espectros_cargados) if '--- ESPECTRO' not in s['nombre']]
            if not indices:
                indices = list(range(len(self.espectros_cargados)))
                
        # Modo comparación / superposición cuando hay 2 o más espectros
        if len(indices) > 1:
            self._dibujar_grafica_overlay(indices)
            self._actualizar_tabla_overlay(indices)
            return

        if not self.espectro_actual and indices:
            self.espectro_actual = self.espectros_cargados[indices[0]]

        if not self.espectro_actual:
            return
            
        x = self.espectro_actual['x']
        y = self.espectro_actual['y']
        
        do_despike = self.var_despike.get()
        combo_val = self.combo_baseline.get()
        
        if 'ALS' in combo_val:
            method = 'als'
        elif 'AIRPLS' in combo_val:
            method = 'airpls'
        elif 'SNIP' in combo_val:
            method = 'snip'
        else:
            method = 'polynomial'
            
        lam_val = 10 ** float(self.slider_lambda.get())
        prom_val = float(self.slider_prom.get()) / 100.0
        shape_fit = self.combo_shape.get()
        
        res = raman_processing.procesar_espectro_raman_completo(
            x, y,
            do_despike=do_despike,
            baseline_method=method,
            baseline_params={'lam': lam_val},
            peak_params={'prominence_factor': prom_val}
        )
        
        for p in res['picos']:
            fit_res = raman_processing.ajustar_perfil_pico(
                x, res['y_net'], p['position_cm'], window_width=max(15.0, p['fwhm_direct'] * 1.5), shape=shape_fit
            )
            p['fit_result'] = fit_res
            
        self.resultado_procesado = res
        
        self._dibujar_grafica()
        self._actualizar_tabla_picos()

    def _dibujar_grafica_overlay(self, indices):
        self.ax.clear()
        
        colores = ['#0d6efd', '#dc3545', '#198754', '#d63384', '#fd7e14', '#6f42c1', '#20c997', '#0dcaf0', '#b02a37', '#6c757d', '#d97706', '#059669']
        modo_comp = self.var_modo_comparacion.get()
        do_despike = self.var_despike.get()
        
        combo_val = self.combo_baseline.get()
        if 'ALS' in combo_val:
            method = 'als'
        elif 'AIRPLS' in combo_val:
            method = 'airpls'
        elif 'SNIP' in combo_val:
            method = 'snip'
        else:
            method = 'polynomial'
        lam_val = 10 ** float(self.slider_lambda.get())
        
        # Procesar todos los espectros seleccionados restando la línea base (y_net en y=0)
        espectros_procesados = []
        max_global_net = 1.0
        
        for idx in indices:
            sp = self.espectros_cargados[idx]
            x = sp['x']
            y = sp['y']
            
            if do_despike:
                try:
                    y = raman_processing.despike_spectrum(y)
                except Exception:
                    pass
                    
            if method == 'als':
                y_base = raman_processing.baseline_als(y, lam=lam_val)
            elif method == 'airpls':
                y_base = raman_processing.baseline_airpls(y, lam=lam_val)
            elif method == 'snip':
                y_base = raman_processing.baseline_snip(y)
            else:
                y_base = raman_processing.baseline_polynomial(x, y)
                
            y_net = np.maximum(0, y - y_base)
            max_val = np.max(y_net) if len(y_net) > 0 else 1.0
            if max_val > max_global_net:
                max_global_net = max_val
                
            espectros_procesados.append({
                'nombre': sp['nombre'],
                'x': x,
                'y_net': y_net,
                'max_val': max_val
            })
            
        # Línea guía horizontal del piso de línea base en y=0
        self.ax.axhline(0, color='#6c757d', linestyle='--', lw=1.1, alpha=0.75, label='_nolegend_')
        
        offset_step = max_global_net * 0.45  # Paso de separación vertical en modo cascada
        
        for i, item in enumerate(espectros_procesados):
            x = item['x']
            y_net = item['y_net']
            c = colores[i % len(colores)]
            
            if "Normalizado" in modo_comp:
                y_max = item['max_val']
                y_plot = (y_net / y_max) if y_max > 0 else y_net
                label_txt = f"{item['nombre']} (máx {y_max:.0f} U.A.)"
            elif "Cascada" in modo_comp:
                offset = i * offset_step
                y_plot = y_net + offset
                label_txt = f"{item['nombre']} (+{offset:.0f})"
                self.ax.axhline(offset, color=c, linestyle=':', lw=0.8, alpha=0.5, label='_nolegend_')
            else:  # "Piso Cero y=0 (Intensidad Real)"
                y_plot = y_net
                label_txt = f"{item['nombre']} (pico {item['max_val']:.0f} U.A.)"
                
            self.ax.plot(x, y_plot, label=label_txt, color=c, lw=1.6, alpha=0.9)
            
        self.ax.set_xlabel('Desplazamiento Raman (cm⁻¹)', color='#212529', fontsize=10, fontweight='bold')
        
        if "Normalizado" in modo_comp:
            y_label_str = 'Intensidad Normalizada (0 a 1)'
            sub_title = "Normalizado (0 a 1)"
        elif "Cascada" in modo_comp:
            y_label_str = 'Intensidad Neta con Desplazamiento Vertical (U.A.)'
            sub_title = "Apilado en Cascada (Offset)"
        else:
            y_label_str = 'Intensidad Raman Neta [Línea Base en y = 0] (U.A.)'
            sub_title = "Línea Base en y = 0 (Intensidad Real)"
            
        self.ax.set_ylabel(y_label_str, color='#212529', fontsize=10, fontweight='bold')
        self.ax.set_title(f"Comparación Espectral Raman | {sub_title} ({len(indices)} espectros)", color='#0d6efd', fontsize=11, fontweight='bold')
        self.ax.legend(facecolor='#ffffff', edgecolor='#ced4da', labelcolor='#212529', fontsize=8, loc='upper right')
        self.ax.grid(True, linestyle=':', alpha=0.5, color='#ced4da')
        
        self.fig.tight_layout()
        self.canvas.draw()

    def _actualizar_tabla_overlay(self, indices):
        for item in self.tree_peaks.get_children():
            self.tree_peaks.delete(item)
            
        combo_val = self.combo_baseline.get()
        method = 'als' if 'ALS' in combo_val else ('airpls' if 'AIRPLS' in combo_val else ('snip' if 'SNIP' in combo_val else 'polynomial'))
        lam_val = 10 ** float(self.slider_lambda.get())
        do_despike = self.var_despike.get()
        modo_text = self.var_modo_analisis.get()
        modo_key = 'pigmentos' if 'Pigment' in modo_text else ('cristalografia' if 'Cristal' in modo_text else 'completo')
        
        for idx in indices:
            sp = self.espectros_cargados[idx]
            x = sp['x']
            y = sp['y']
            
            if do_despike:
                try:
                    y = raman_processing.despike_spectrum(y)
                except Exception:
                    pass
                    
            if method == 'als':
                y_base = raman_processing.baseline_als(y, lam=lam_val)
            elif method == 'airpls':
                y_base = raman_processing.baseline_airpls(y, lam=lam_val)
            elif method == 'snip':
                y_base = raman_processing.baseline_snip(y)
            else:
                y_base = raman_processing.baseline_polynomial(x, y)
                
            y_net = np.maximum(0, y - y_base)
            max_idx = np.argmax(y_net)
            pos_max = x[max_idx] if max_idx < len(x) else 0.0
            int_net_max = np.max(y_net)
            int_raw_max = y[max_idx] if max_idx < len(y) else int_net_max
            
            matches = raman_database.identificar_banda(pos_max, tolerance=10.0, modo=modo_key)
            id_str = f"{matches[0]['compuesto']} [{matches[0]['formula']}]" if matches else "Sin asignar"
            
            self.tree_peaks.insert('', 'end', values=(
                f"{pos_max:.1f}",
                f"{int_raw_max:.1f}",
                f"{int_net_max:.1f}",
                "-",
                "-",
                "-",
                "-",
                f"[Muestra: {sp['nombre']}] -> Banda máx ~ {pos_max:.1f} cm⁻¹ (Int. Neta: {int_net_max:.0f} U.A. | {id_str})"
            ))

    def _dibujar_grafica(self):
        self.ax.clear()
        
        res = self.resultado_procesado
        if not res:
            self.canvas.draw()
            return
            
        x = res['x']
        y_clean = res['y_clean']
        y_base = res['y_baseline']
        y_net = res['y_net']
        picos = res['picos']
        
        # Graficar en colores nítidos de tema claro
        if self.var_show_raw.get():
            self.ax.plot(x, y_clean, color='#6c757d', label='Espectro Bruto / Despiked', alpha=0.5, lw=1.0)
            self.ax.plot(x, y_base, color='#dc3545', linestyle='--', label='Línea Base Estimada', lw=1.3)
            
        self.ax.plot(x, y_net, color='#0d6efd', label='Espectro Raman Procesado (Línea Base Sustraída)', lw=1.6)
        
        show_labels = self.var_show_labels.get()
        show_fwhm = self.var_show_fwhm_lines.get()
        style_mode = self.var_label_style.get()
        max_str = self.var_max_labels.get()
        max_n = int(max_str) if max_str.isdigit() else len(picos)
        
        picos_a_graficar = picos[:max_n]
        
        for p in picos_a_graficar:
            x_p = p['position_cm']
            y_p = p['intensity_net']
            fwhm_d = p['fwhm_direct']
            
            self.ax.plot(x_p, y_p, 'o', color='#fd7e14', markersize=5)
            
            if show_fwhm:
                y_half = y_p / 2.0
                self.ax.hlines(y_half, p['fwhm_left'], p['fwhm_right'], color='#d63384', linestyle=':', lw=1.5)
                
            if show_labels:
                if style_mode == "Solo Posición":
                    texto_label = f"{x_p:.1f}"
                elif style_mode == "Posición + Fase":
                    modo_text = self.var_modo_analisis.get()
                    modo_key = 'pigmentos' if 'Pigment' in modo_text else ('cristalografia' if 'Cristal' in modo_text else 'completo')
                    matches = raman_database.identificar_banda(x_p, tolerance=10.0, modo=modo_key)
                    if matches:
                        comp_name = matches[0]['compuesto'].split('(')[0].strip()
                        texto_label = f"{x_p:.1f}\n({comp_name})"
                    else:
                        texto_label = f"{x_p:.1f}"
                else:  # "Posición + FWHM"
                    texto_label = f"{x_p:.1f}\n(FWHM {fwhm_d:.1f})"
                    
                self.ax.annotate(
                    texto_label,
                    xy=(x_p, y_p),
                    xytext=(x_p, y_p + np.max(y_net) * 0.04),
                    ha='center', va='bottom',
                    fontsize=8, color='#212529', fontweight='bold',
                    arrowprops=dict(arrowstyle='->', color='#fd7e14', lw=0.8)
                )
            
        self.ax.set_xlabel('Desplazamiento Raman (cm⁻¹)', color='#212529', fontsize=10, fontweight='bold')
        self.ax.set_ylabel('Intensidad (U.A.)', color='#212529', fontsize=10, fontweight='bold')
        self.ax.set_title(f"Espectro Raman: {self.espectro_actual['nombre']}", color='#0d6efd', fontsize=11, fontweight='bold')
        self.ax.legend(facecolor='#ffffff', edgecolor='#ced4da', labelcolor='#212529', fontsize=9)
        self.ax.grid(True, linestyle=':', alpha=0.5, color='#ced4da')
        
        self.fig.tight_layout()
        self.canvas.draw()

    def _actualizar_tabla_picos(self):
        for item in self.tree_peaks.get_children():
            self.tree_peaks.delete(item)
            
        res = self.resultado_procesado
        if not res or not res['picos']:
            return
            
        modo_text = self.var_modo_analisis.get()
        modo_key = 'pigmentos' if 'Pigment' in modo_text else ('cristalografia' if 'Cristal' in modo_text else 'completo')
        
        # Identificación global del espectro
        posiciones = [p['position_cm'] for p in res['picos']]
        candidatos_globales = raman_database.identificar_espectro(posiciones, modo=modo_key)
        
        for p in res['picos']:
            x_p = p['position_cm']
            y_raw = self.espectro_actual['y'][p['idx']] if p['idx'] < len(self.espectro_actual['y']) else p['intensity_net']
            y_net = p['intensity_net']
            fwhm_dir = p['fwhm_direct']
            area_net = p['area_net']
            
            fit_res = p['fit_result']
            if fit_res:
                fwhm_fit = fit_res['fwhm_fit']
                r2_fit = fit_res['r_squared']
            else:
                fwhm_fit = np.nan
                r2_fit = np.nan
                
            # Evaluador específico de candidato según modo
            matches = raman_database.identificar_banda(x_p, tolerance=10.0, modo=modo_key)
            if matches:
                m = matches[0]
                fwhm_ref = m.get('fwhm_ref', 8.0)
                
                # Diagnóstico cristalográfico basado en FWHM
                if fwhm_dir <= fwhm_ref * 1.3:
                    estado_cristal = "Alta Cristalinidad / Orden de Red"
                elif fwhm_dir <= fwhm_ref * 2.2:
                    estado_cristal = "Tensiones de Red / Nanocristalino"
                else:
                    estado_cristal = "Fase Amorfa / Degradada"
                
                if 'Pigment' in modo_text:
                    compound_str = f"{m['compuesto']} [{m['formula']}] (Banda: {m['banda_teorica']} cm⁻¹ | Cat: {m['categoria']})"
                elif 'Cristal' in modo_text:
                    compound_str = f"{m['compuesto']} -> Sistema: {m['sistema_cristalino']} [{estado_cristal} | FWHM ref {fwhm_ref} cm⁻¹]"
                else:  # Vista Completa (Arqueometría)
                    compound_str = f"{m['compuesto']} [{m['formula']}] -> {m['sistema_cristalino']} ({estado_cristal})"
            else:
                compound_str = "Banda no asignada"
            
            self.tree_peaks.insert('', 'end', values=(
                f"{x_p:.1f}",
                f"{y_raw:.1f}",
                f"{y_net:.1f}",
                f"{fwhm_dir:.2f}",
                f"{fwhm_fit:.2f}" if not np.isnan(fwhm_fit) else "N/A",
                f"{area_net:.1f}",
                f"{r2_fit:.3f}" if not np.isnan(r2_fit) else "N/A",
                compound_str
            ))

    def ejecutar_pca(self):
        if not HAS_SKLEARN or len(self.espectros_cargados) < 3:
            messagebox.showwarning("PCA No Disponible", "Se requieren al menos 3 espectros cargados y la librería scikit-learn.")
            return
            
        try:
            sel = self.tree_files.selection()
            indices_sel = [int(i) for i in sel if i.isdigit() and int(i) < len(self.espectros_cargados)]
            
            if len(indices_sel) >= 3:
                specs = [self.espectros_cargados[i] for i in indices_sel]
            else:
                specs = [s for s in self.espectros_cargados if 'ESPECTRO' not in s['nombre']]
                
            if len(specs) < 3:
                messagebox.showwarning("Atención", "No hay suficientes espectros de muestra individuales para PCA.")
                return
                
            x_comun, y_list = lectura_raman.reinterpolar_espectros_a_grilla_comun(specs)
            X = np.array([raman_processing.normalizar_espectro(y, metodo='vector') for y in y_list])
            
            pca = PCA(n_components=2)
            scores = pca.fit_transform(X)
            var_exp = pca.explained_variance_ratio_ * 100
            
            top_pca = tk.Toplevel(self.root)
            top_pca.title("📈 PCA - Análisis de Componentes Principales")
            top_pca.geometry("800x600")
            top_pca.configure(bg='#f4f6f8')
            
            fig_pca = Figure(figsize=(7, 5), dpi=100, facecolor='#ffffff')
            ax_pca = fig_pca.add_subplot(111)
            ax_pca.set_facecolor('#ffffff')
            ax_pca.tick_params(colors='#212529')
            for spine in ax_pca.spines.values():
                spine.set_color('#ced4da')
                
            for i, sp in enumerate(specs):
                ax_pca.scatter(scores[i, 0], scores[i, 1], label=sp['nombre'], s=70)
                ax_pca.annotate(sp['nombre'], (scores[i, 0], scores[i, 1]), color='#212529', fontsize=9, xytext=(5, 5), textcoords='offset points', fontweight='bold')
                
            ax_pca.set_xlabel(f"PC1 ({var_exp[0]:.1f}% V.E.)", color='#212529', fontweight='bold')
            ax_pca.set_ylabel(f"PC2 ({var_exp[1]:.1f}% V.E.)", color='#212529', fontweight='bold')
            ax_pca.set_title("Gráfica de Puntuaciones PCA (Score Plot)", color='#0d6efd', fontweight='bold')
            ax_pca.grid(True, linestyle=':', alpha=0.5, color='#ced4da')
            fig_pca.tight_layout()
            
            canvas_pca = FigureCanvasTkAgg(fig_pca, master=top_pca)
            canvas_pca.draw()
            canvas_pca.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            messagebox.showerror("Error PCA", str(e))

    def exportar_excel(self):
        if not self.resultado_procesado:
            messagebox.showwarning("Atención", "No hay datos procesados para exportar.")
            return
            
        save_path = filedialog.asksaveasfilename(
            title="Guardar Reporte Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")]
        )
        if not save_path:
            return
            
        try:
            writer = pd.ExcelWriter(save_path, engine='openpyxl')
            
            rows = []
            for item in self.tree_peaks.get_children():
                vals = self.tree_peaks.item(item)['values']
                rows.append(vals)
                
            df_peaks = pd.DataFrame(rows, columns=[
                'Posición (cm⁻¹)', 'Int. Bruta', 'Int. Neta', 'FWHM Directo (cm⁻¹)',
                'FWHM Ajuste (cm⁻¹)', 'Área Neta', 'R² Ajuste', 'Identificación y Diagnóstico (Fórmula / FWHM / Cristalografía)'
            ])
            df_peaks.to_excel(writer, sheet_name='Tabla_Picos', index=False)
            
            res = self.resultado_procesado
            df_spec = pd.DataFrame({
                'Raman_Shift_cm-1': res['x'],
                'Intensidad_Bruta': res['y_raw'],
                'Intensidad_Limpia': res['y_clean'],
                'Linea_Base': res['y_baseline'],
                'Intensidad_Neta': res['y_net']
            })
            df_spec.to_excel(writer, sheet_name='Datos_Espectrales', index=False)
            
            writer.close()
            messagebox.showinfo("Exportación Exitosa", f"Reporte guardado correctamente en:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Error al Exportar Excel", str(e))

    def exportar_lote_completo(self):
        """
        Exporta automáticamente todas las muestras cargadas en la lista utilizando directamente
        los parámetros calibrados y activos en la pantalla principal (Línea base, Lambda,
        Prominencia, Despiking, Enfoque y FWHM).
        Genera la Matriz General de Lote en Excel, Gráficas HD y CSVs limpios.
        """
        espectros_reales = [s for s in self.espectros_cargados if '--- ESPECTRO' not in s['nombre']]
        if not espectros_reales:
            messagebox.showwarning("Atención", "No hay espectros de muestras cargados en la lista para exportar.")
            return
            
        dir_base = os.path.dirname(espectros_reales[0]['ruta']) if 'ruta' in espectros_reales[0] and os.path.exists(espectros_reales[0]['ruta']) else os.getcwd()
        dir_sugerido = os.path.join(dir_base, "Resultados_Lote_CODICE")
        
        dir_salida = filedialog.askdirectory(
            title="Seleccionar Carpeta para Guardar el Reporte de Lote Completo",
            initialdir=dir_base
        )
        if not dir_salida:
            return
            
        if os.path.abspath(dir_salida) == os.path.abspath(dir_base):
            dir_salida = dir_sugerido
            
        modo_text = self.var_modo_analisis.get()
        modo_key = 'pigmentos' if 'Pigment' in modo_text else ('cristalografia' if 'Cristal' in modo_text else 'completo')
        algo_name = self.combo_baseline.get()
        algo_key = 'als' if 'ALS' in algo_name else ('airpls' if 'AIRPLS' in algo_name else ('snip' if 'SNIP' in algo_name else 'polynomial'))
        lam_val = 10.0 ** float(self.slider_lambda.get())
        prom_pct = float(self.slider_prom.get())
        do_despike = self.var_despike.get()
        shape_fit = self.combo_shape.get()
        
        win_prog = tk.Toplevel(self.root)
        win_prog.title("Exportando Lote Completo | CÓDICE - CNCPC")
        win_prog.geometry("450x150")
        win_prog.resizable(False, False)
        win_prog.transient(self.root)
        win_prog.grab_set()
        win_prog.configure(bg='#ffffff')
        
        ttk.Label(win_prog, text="📦 Generando Matriz de Lote, Gráficas y Reportes...", font=('Segoe UI', 10, 'bold'), foreground='#0d6efd').pack(padx=16, pady=(16, 6), anchor='w')
        
        lbl_status = ttk.Label(win_prog, text="Iniciando...", font=('Segoe UI', 9, 'italic'), foreground='#495057')
        lbl_status.pack(padx=16, pady=(0, 6), anchor='w')
        
        pbar = ttk.Progressbar(win_prog, orient='horizontal', mode='determinate')
        pbar.pack(fill=tk.X, padx=16, pady=(0, 12))
        
        params = {
            'algo_name': algo_name,
            'algo_key': algo_key,
            'lam_val': lam_val,
            'prom_pct': prom_pct,
            'do_despike': do_despike,
            'shape_fit': shape_fit,
            'modo_text': modo_text,
            'modo_key': modo_key,
            'lambda_log': self.slider_lambda.get()
        }
        
        t = threading.Thread(
            target=self._ejecutar_exportacion_lote_worker,
            args=(espectros_reales, dir_salida, params, win_prog, pbar, lbl_status),
            daemon=True
        )
        t.start()

    def _ejecutar_exportacion_lote_worker(self, espectros_reales, dir_salida, params, win_prog, pbar, lbl_status):
        try:
            os.makedirs(dir_salida, exist_ok=True)
            dir_graficas = os.path.join(dir_salida, 'Graficas_Procesadas_HD')
            dir_csvs = os.path.join(dir_salida, 'Datos_Limpios_CSV')
            os.makedirs(dir_graficas, exist_ok=True)
            os.makedirs(dir_csvs, exist_ok=True)
            
            total = len(espectros_reales)
            resumen_lote = []
            todos_picos_lote = []
            
            for idx, spec in enumerate(espectros_reales):
                pct = int(((idx + 1) / total) * 100)
                self.root.after(0, lambda i=idx+1, t=total, p=pct, n=spec['nombre']: (
                    pbar.configure(value=p),
                    lbl_status.config(text=f"Procesando ({i}/{t}): {n}")
                ))
                
                x = spec['x']
                y = spec['y']
                
                y_clean = raman_processing.despike_spectrum(y) if params['do_despike'] else y.copy()
                
                algo_k = params['algo_key']
                if algo_k == 'als':
                    y_base = raman_processing.baseline_als(y_clean, lam=params['lam_val'])
                elif algo_k == 'airpls':
                    y_base = raman_processing.baseline_airpls(y_clean, lam=params['lam_val'])
                elif algo_k == 'snip':
                    y_base = raman_processing.baseline_snip(y_clean)
                else:
                    y_base = raman_processing.baseline_polynomial(x, y_clean)
                    
                y_net = np.maximum(0, y_clean - y_base)
                
                picos = raman_processing.detectar_picos(x, y_net, prominence_percent=params['prom_pct'])
                for p in picos:
                    fit_res = raman_processing.ajustar_perfil_pico(
                        x, y_net, p['position_cm'], window_width=max(15.0, p['fwhm_direct'] * 1.5), shape=params['shape_fit']
                    )
                    p['fit_result'] = fit_res
                    
                posiciones_cm = [p['position_cm'] for p in picos]
                candidatos = raman_database.identificar_espectro(posiciones_cm, modo=params['modo_key'])
                
                fase_1 = candidatos[0][0] if len(candidatos) > 0 else "Sin asignar"
                score_1 = f"{candidatos[0][1]['score']}%" if len(candidatos) > 0 else "-"
                formula_1 = candidatos[0][1]['formula'] if len(candidatos) > 0 else "-"
                sistema_1 = candidatos[0][1].get('sistema_cristalino', 'N/A') if len(candidatos) > 0 else "-"
                
                fase_2 = candidatos[1][0] if len(candidatos) > 1 else "-"
                score_2 = f"{candidatos[1][1]['score']}%" if len(candidatos) > 1 else "-"
                
                if len(picos) > 0:
                    p_max = max(picos, key=lambda p: p['intensity_net'])
                    fwhm_main = p_max['fwhm_direct']
                    p_str = ", ".join([f"{p['position_cm']:.1f}" for p in picos[:8]])
                    
                    if len(candidatos) > 0:
                        ref_f = candidatos[0][1].get('fwhm_ref', 8.0)
                        if fwhm_main <= ref_f * 1.3:
                            diag_fwhm = f"Alta Cristalinidad (FWHM {fwhm_main:.1f} cm⁻¹)"
                        elif fwhm_main <= ref_f * 2.2:
                            diag_fwhm = f"Tensiones de Red / Nanocristalino (FWHM {fwhm_main:.1f} cm⁻¹)"
                        else:
                            diag_fwhm = f"Fase Amorfa / Degradada (FWHM {fwhm_main:.1f} cm⁻¹)"
                    else:
                        diag_fwhm = f"FWHM {fwhm_main:.1f} cm⁻¹"
                else:
                    p_str = "Sin picos prominentes"
                    diag_fwhm = "-"
                    
                resumen_lote.append({
                    'Muestra': spec['nombre'],
                    'Num_Picos': len(picos),
                    'Picos_Detectados_cm-1': p_str,
                    'Fase_Principal_Identificada': fase_1,
                    'Certeza_Fase_1': score_1,
                    'Formula_Fase_1': formula_1,
                    'Sistema_Cristalino_Fase_1': sistema_1,
                    'Diagnostico_Cristalinidad_FWHM': diag_fwhm,
                    'Fase_Secundaria': fase_2,
                    'Certeza_Fase_2': score_2
                })
                
                for p in picos:
                    m_indiv = raman_database.identificar_banda(p['position_cm'], tolerance=10.0, modo=params['modo_key'])
                    cand_str = f"{m_indiv[0]['compuesto']} [{m_indiv[0]['formula']}]" if m_indiv else "No asignado"
                    f_fit = p['fit_result']['fwhm_fit'] if p['fit_result'] else np.nan
                    r2_fit = p['fit_result']['r_squared'] if p['fit_result'] else np.nan
                    
                    todos_picos_lote.append({
                        'Muestra': spec['nombre'],
                        'Posicion_cm-1': round(p['position_cm'], 2),
                        'Intensidad_Neta': round(p['intensity_net'], 2),
                        'FWHM_Directo_cm-1': round(p['fwhm_direct'], 2),
                        'FWHM_Ajuste_cm-1': round(f_fit, 2) if not np.isnan(f_fit) else "N/A",
                        'Area_Neta': round(p['area_net'], 2),
                        'R2_Ajuste': round(r2_fit, 3) if not np.isnan(r2_fit) else "N/A",
                        'Compuesto_Candidato': cand_str
                    })
                    
                try:
                    fig_hd = Figure(figsize=(9, 5), dpi=200, facecolor='#ffffff')
                    ax_hd = fig_hd.add_subplot(111)
                    ax_hd.set_facecolor('#ffffff')
                    ax_hd.plot(x, y_net, color='#0d6efd', lw=1.5, label='Espectro Raman Procesado')
                    
                    for p in picos[:10]:
                        ax_hd.plot(p['position_cm'], p['intensity_net'], 'o', color='#fd7e14', markersize=4)
                        ax_hd.annotate(
                            f"{p['position_cm']:.1f}",
                            xy=(p['position_cm'], p['intensity_net']),
                            xytext=(p['position_cm'], p['intensity_net'] + np.max(y_net) * 0.04),
                            ha='center', va='bottom', fontsize=7, fontweight='bold', color='#212529'
                        )
                        
                    ax_hd.set_xlabel('Desplazamiento Raman (cm⁻¹)', fontweight='bold', color='#212529')
                    ax_hd.set_ylabel('Intensidad (U.A.)', fontweight='bold', color='#212529')
                    ax_hd.set_title(f"INAH / CNCPC - CÓDICE: {spec['nombre']} | Fase: {fase_1} ({score_1})", color='#0d6efd', fontsize=10, fontweight='bold')
                    ax_hd.grid(True, linestyle=':', alpha=0.5, color='#ced4da')
                    fig_hd.tight_layout()
                    
                    out_png = os.path.join(dir_graficas, f"{spec['nombre']}.png")
                    fig_hd.savefig(out_png, dpi=200, bbox_inches='tight')
                except Exception as e_fig:
                    print(f"[Error Gráfica HD] {spec['nombre']}: {e_fig}")
                    
                try:
                    df_clean = pd.DataFrame({'Raman_Shift_cm-1': x, 'Intensidad_Neta': y_net})
                    out_csv = os.path.join(dir_csvs, f"{spec['nombre']}_limpio.csv")
                    df_clean.to_csv(out_csv, index=False)
                except Exception as e_csv:
                    print(f"[Error CSV] {spec['nombre']}: {e_csv}")
                    
            excel_path = os.path.join(dir_salida, 'Matriz_General_Lote_CODICE.xlsx')
            writer = pd.ExcelWriter(excel_path, engine='openpyxl')
            
            df_resumen = pd.DataFrame(resumen_lote)
            df_resumen.to_excel(writer, sheet_name='Resumen_Fases_Lote', index=False)
            
            if todos_picos_lote:
                df_det = pd.DataFrame(todos_picos_lote)
                df_det.to_excel(writer, sheet_name='Detalle_Todos_Picos', index=False)
                
            df_meta = pd.DataFrame([
                {'Parametro': 'Institución', 'Valor': 'INAH - CNCPC / Laboratorio CÓDICE'},
                {'Parametro': 'Fecha de Procesamiento', 'Valor': time.strftime('%Y-%m-%d %H:%M:%S')},
                {'Parametro': 'Total Muestras Procesadas', 'Valor': len(resumen_lote)},
                {'Parametro': 'Algoritmo Línea Base', 'Valor': params['algo_name']},
                {'Parametro': 'Lambda Suavidad (log10)', 'Valor': params['lambda_log']},
                {'Parametro': 'Prominencia Mínima Picos', 'Valor': f"{params['prom_pct']}%"},
                {'Parametro': 'Filtro Rayos Cósmicos (Despiking)', 'Valor': 'Activado' if params['do_despike'] else 'Desactivado'},
                {'Parametro': 'Enfoque de Base de Datos', 'Valor': params['modo_text']}
            ])
            df_meta.to_excel(writer, sheet_name='Metadatos_Lote', index=False)
            writer.close()
            
            self.root.after(0, lambda: (
                win_prog.destroy(),
                self._notificar_fin_lote_directo(dir_salida, len(resumen_lote))
            ))
            
        except Exception as e:
            err_str = str(e)
            self.root.after(0, lambda: (
                win_prog.destroy(),
                messagebox.showerror("Error al Exportar Lote", err_str)
            ))

    def _notificar_fin_lote_directo(self, dir_salida, total):
        resp = messagebox.askyesno(
            "Exportación de Lote Completada",
            f"Se procesaron y exportaron exitosamente {total} muestras del lote.\n\n"
            f"Resultados guardados en:\n{dir_salida}\n\n"
            "¿Deseas abrir la carpeta de resultados en el explorador?",
            parent=self.root
        )
        if resp:
            try:
                if sys.platform.startswith('win'):
                    os.startfile(dir_salida)
                elif sys.platform.startswith('darwin'):
                    subprocess.Popen(['open', dir_salida])
                else:
                    subprocess.Popen(['xdg-open', dir_salida])
            except Exception:
                pass


def main():
    root = TkinterDnD.Tk() if HAS_DND else tk.Tk()
    app = RamanAnalyzerApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
