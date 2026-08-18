"""
Módulo de Base de Datos de Referencia Raman e Identificación de Fases Minerales,
Pigmentos Arqueométricos y Compuestos Cristalográficos.
CNCPC / Laboratorio CÓDICE.
"""

import numpy as np

# Diccionario de referencia con desplazamientos Raman principales (cm^-1),
# parámetros cristalo-químicos, sistemas cristalinos y polimorfos.
RAMAN_DATABASE = {
    # -------------------------------------------------------------------------
    # 1. PIGMENTOS AZULES
    # -------------------------------------------------------------------------
    'Azul Maya (Índigo + Paligorskita)': {
        'bands': [1575, 1585, 545, 599, 1225, 1250, 1310, 1365],
        'main_band': 1575,
        'category': 'Pigmentos Azules Mesoamericanos',
        'formula': 'C₁₆H₁₀N₂O₂ + (Mg,Al)₂Si₄O₁₀(OH)·4H₂O',
        'color': '#1E90FF',
        'tipo': ['pigmento', 'ambos'],
        'sistema_cristalino': 'Monoclínico / Complejo Híbrido Arcilla-Colorante (C2/m)',
        'polimorfos': 'Índigo libre / Sepiolita',
        'fwhm_ref': 12.0
    },
    'Azurita (Carbonato Básico de Cobre)': {
        'bands': [400, 1094, 249, 1432, 1578, 837, 765],
        'main_band': 400,
        'category': 'Pigmentos Azules',
        'formula': 'Cu₃(CO₃)₂(OH)₂',
        'color': '#0000FF',
        'tipo': ['pigmento', 'mineral', 'ambos'],
        'sistema_cristalino': 'Monoclínico (P2₁/c)',
        'polimorfos': 'Malaquita (polimorfo parcial hidratado)',
        'fwhm_ref': 6.5
    },
    'Lapislázuli / Azul Ultramar (Lazurita)': {
        'bands': [548, 258, 805, 1096, 1640, 585],
        'main_band': 548,
        'category': 'Pigmentos Azules',
        'formula': 'Na₈₋₁₀Al₆Si₆O₂₄S₂₋₄',
        'color': '#00008B',
        'tipo': ['pigmento', 'mineral', 'ambos'],
        'sistema_cristalino': 'Cúbico (P-43n - Grupo de la Sodalita)',
        'polimorfos': 'Haüyna / Noseana',
        'fwhm_ref': 8.0
    },
    'Azul de Prusia (Ferrocianuro Férrico)': {
        'bands': [2154, 2095, 535, 280],
        'main_band': 2154,
        'category': 'Pigmentos Azules Sintéticos',
        'formula': 'Fe₄[Fe(CN)₆]₃·xH₂O',
        'color': '#003366',
        'tipo': ['pigmento'],
        'sistema_cristalino': 'Cúbico de cara centrada (Fm-3m)',
        'polimorfos': 'Azul de Turnbull',
        'fwhm_ref': 14.0
    },
    'Esmalte / Smalt (Vidrio de Cobalto)': {
        'bands': [470, 950, 1060],
        'main_band': 470,
        'category': 'Pigmentos Azules',
        'formula': 'K-Co-Silicato (Vidrio amorfo)',
        'color': '#4169E1',
        'tipo': ['pigmento'],
        'sistema_cristalino': 'Amorfo (Estructura vítrea desordenada)',
        'polimorfos': 'Ninguno',
        'fwhm_ref': 45.0
    },

    # -------------------------------------------------------------------------
    # 2. PIGMENTOS ROJOS Y NARANJAS
    # -------------------------------------------------------------------------
    'Cinabrio / Bermellón (HgS trigonal)': {
        'bands': [253, 343, 282, 353],
        'main_band': 253,
        'category': 'Pigmentos Rojos / Sulfuros',
        'formula': 'α-HgS',
        'color': '#FF0000',
        'tipo': ['pigmento', 'mineral', 'ambos'],
        'sistema_cristalino': 'Trigonal / Romboédrico (P3₁21)',
        'polimorfos': 'Metacinabrio (β-HgS cúbico) / Hipercinabrio',
        'fwhm_ref': 5.2
    },
    'Metacinabrio (HgS cúbico negro/degradado)': {
        'bands': [228, 178, 275],
        'main_band': 228,
        'category': 'Fases de Degradación de Mercurio',
        'formula': 'β-HgS',
        'color': '#2B2B2B',
        'tipo': ['mineral', 'ambos'],
        'sistema_cristalino': 'Cúbico tipo Esfalerita (F-43m)',
        'polimorfos': 'Cinabrio (α-HgS trigonal)',
        'fwhm_ref': 15.0
    },
    'Hematita (Fe2O3 - Ocre Rojo)': {
        'bands': [225, 293, 412, 613, 1320, 498],
        'main_band': 293,
        'category': 'Óxidos de Hierro / Ocres',
        'formula': 'α-Fe₂O₃',
        'color': '#CD5C5C',
        'tipo': ['pigmento', 'mineral', 'ambos'],
        'sistema_cristalino': 'Trigonal / Corindón (R-3c)',
        'polimorfos': 'Maghemita (γ-Fe₂O₃ cúbica) / Goethita',
        'fwhm_ref': 7.5
    },
    'Minio / Azarcón (Tetraóxido de Plomo)': {
        'bands': [548, 121, 151, 224, 313, 390, 478],
        'main_band': 548,
        'category': 'Pigmentos Rojos / Naranjas',
        'formula': 'Pb₃O₄ (Pb₂²⁺Pb⁴⁺O₄)',
        'color': '#FF4500',
        'tipo': ['pigmento', 'mineral', 'ambos'],
        'sistema_cristalino': 'Tetragonal (P4₂/mbc)',
        'polimorfos': 'Massicot (β-PbO) / Litargirio (α-PbO)',
        'fwhm_ref': 7.0
    },
    'Laca de Grana Cochinilla (Ácido Carmínico)': {
        'bands': [1305, 1465, 1230, 1640, 1420],
        'main_band': 1305,
        'category': 'Colorantes y Lacas Orgánicas',
        'formula': 'C₂₂H₂₀O₁₃ (Complejo de Al-Ca)',
        'color': '#C71585',
        'tipo': ['pigmento', 'organico'],
        'sistema_cristalino': 'Complejo Amorfo / Orgánico Quelado',
        'polimorfos': 'Kermes / Laca de Palo',
        'fwhm_ref': 20.0
    },
    'Realgar (Sulfuro de Arsénico Naranja)': {
        'bands': [354, 220, 192, 183, 341],
        'main_band': 354,
        'category': 'Pigmentos Naranjas / Sulfuros',
        'formula': 'As₄S₄ (α-As₄S₄)',
        'color': '#FF4500',
        'tipo': ['pigmento', 'mineral', 'ambos'],
        'sistema_cristalino': 'Monoclínico (P2₁/n)',
        'polimorfos': 'Pararrealgar (degradación lumínica) / Alacranita',
        'fwhm_ref': 6.0
    },

    # -------------------------------------------------------------------------
    # 3. PIGMENTOS AMARILLOS
    # -------------------------------------------------------------------------
    'Oropimente (Sulfuro de Arsénico Amarillo)': {
        'bands': [354, 292, 311, 383, 154, 202, 136],
        'main_band': 354,
        'category': 'Pigmentos Amarillos / Sulfuros',
        'formula': 'As₂S₃',
        'color': '#FFD700',
        'tipo': ['pigmento', 'mineral', 'ambos'],
        'sistema_cristalino': 'Monoclínico en capas (P2₁/n)',
        'polimorfos': 'Anomorfo As₂S₃ / Realgar',
        'fwhm_ref': 6.2
    },
    'Goethita (FeOOH - Ocre Amarillo)': {
        'bands': [385, 243, 299, 479, 550, 685],
        'main_band': 385,
        'category': 'Óxidos de Hierro / Ocres',
        'formula': 'α-FeO(OH)',
        'color': '#E9967A',
        'tipo': ['pigmento', 'mineral', 'ambos'],
        'sistema_cristalino': 'Ortorrómbico / Grupo del Diásporo (Pnma)',
        'polimorfos': 'Lepidocrocita (γ-FeOOH) / Hematita',
        'fwhm_ref': 9.0
    },
    'Massicot (Óxido de Plomo Amarillo Ortorrómbico)': {
        'bands': [288, 143, 85],
        'main_band': 288,
        'category': 'Pigmentos Amarillos',
        'formula': 'β-PbO',
        'color': '#FFFF00',
        'tipo': ['pigmento', 'mineral', 'ambos'],
        'sistema_cristalino': 'Ortorrómbico (Pbcm)',
        'polimorfos': 'Litargirio (α-PbO tetragonal)',
        'fwhm_ref': 5.8
    },
    'Amarillo de Nápoles (Antimoniato de Plomo)': {
        'bands': [510, 138, 330, 640],
        'main_band': 510,
        'category': 'Pigmentos Amarillos Históricos',
        'formula': 'Pb₂(SbO₄)₂ (Estructura Pirocloro)',
        'color': '#F0E68C',
        'tipo': ['pigmento', 'mineral', 'ambos'],
        'sistema_cristalino': 'Cúbico tipo Pirocloro (Fd-3m)',
        'polimorfos': 'Bindheimita',
        'fwhm_ref': 12.0
    },

    # -------------------------------------------------------------------------
    # 4. PIGMENTOS VERDES
    # -------------------------------------------------------------------------
    'Malaquita (Carbonato Básico de Cobre)': {
        'bands': [432, 149, 178, 269, 536, 1058, 1367, 1495],
        'main_band': 432,
        'category': 'Pigmentos Verdes',
        'formula': 'Cu₂CO₃(OH)₂',
        'color': '#008000',
        'tipo': ['pigmento', 'mineral', 'ambos'],
        'sistema_cristalino': 'Monoclínico (P2₁/a)',
        'polimorfos': 'Azurita (carbonato anhidro/hidratado)',
        'fwhm_ref': 6.8
    },
    'Verdigris / Cardenillo (Acetato Básico de Cobre)': {
        'bands': [1535, 1445, 940, 680, 275],
        'main_band': 1445,
        'category': 'Pigmentos Verdes Sintéticos',
        'formula': 'Cu(CH₃COO)₂·[Cu(OH)₂]₃',
        'color': '#2E8B57',
        'tipo': ['pigmento'],
        'sistema_cristalino': 'Monoclínico (P2₁/c)',
        'polimorfos': 'Resinato de Cobre',
        'fwhm_ref': 16.0
    },
    'Tierra Verde (Celadonita / Glauconita)': {
        'bands': [700, 395, 270, 545, 170],
        'main_band': 700,
        'category': 'Tierras y Silicatos Verdes',
        'formula': 'K[(Al,Fe³⁺),(Mg,Fe²⁺)](Si₄O₁₀)(OH)₂',
        'color': '#556B2F',
        'tipo': ['pigmento', 'mineral', 'ambos'],
        'sistema_cristalino': 'Monoclínico Filosilicato en hojas (C2/m)',
        'polimorfos': 'Glauconita / Esmectitas',
        'fwhm_ref': 18.0
    },

    # -------------------------------------------------------------------------
    # 5. BLANCOS, CARBONATOS Y SULFATOS
    # -------------------------------------------------------------------------
    'Calcita (CaCO3)': {
        'bands': [1086, 712, 282, 156],
        'main_band': 1086,
        'category': 'Carbonatos / Cargas / Estucos',
        'formula': 'CaCO₃',
        'color': '#8B0000',
        'tipo': ['mineral', 'ambos'],
        'sistema_cristalino': 'Trigonal / Romboédrico (R-3c)',
        'polimorfos': 'Aragonita (ortorrómbico) / Vaterita (hexagonal)',
        'fwhm_ref': 4.5
    },
    'Aragonita (CaCO3)': {
        'bands': [1085, 206, 153, 704, 113],
        'main_band': 1085,
        'category': 'Carbonatos / Conchas Arqueológicas',
        'formula': 'CaCO₃',
        'color': '#A52A2A',
        'tipo': ['mineral', 'ambos'],
        'sistema_cristalino': 'Ortorrómbico (Pmcn)',
        'polimorfos': 'Calcita (trigonal) / Vaterita',
        'fwhm_ref': 5.0
    },
    'Blanco de Plomo (Hidrocerusita)': {
        'bands': [1050, 1054, 400, 680, 140],
        'main_band': 1050,
        'category': 'Pigmentos Blancos',
        'formula': '2PbCO₃·Pb(OH)₂',
        'color': '#708090',
        'tipo': ['pigmento', 'mineral', 'ambos'],
        'sistema_cristalino': 'Trigonal (R-3m)',
        'polimorfos': 'Cerusita (PbCO₃ ortorrómbico)',
        'fwhm_ref': 6.0
    },
    'Blanco de Plomo (Cerusita)': {
        'bands': [1053, 676, 838, 148],
        'main_band': 1053,
        'category': 'Pigmentos Blancos',
        'formula': 'PbCO₃',
        'color': '#778899',
        'tipo': ['pigmento', 'mineral', 'ambos'],
        'sistema_cristalino': 'Ortorrómbico (Pmcn)',
        'polimorfos': 'Hidrocerusita (trigonal)',
        'fwhm_ref': 5.5
    },
    'Yeso (Sulfato de Calcio Dihidratado)': {
        'bands': [1008, 414, 493, 619, 670, 1136],
        'main_band': 1008,
        'category': 'Sulfatos / Bases de Preparación',
        'formula': 'CaSO₄·2H₂O',
        'color': '#DAA520',
        'tipo': ['mineral', 'ambos'],
        'sistema_cristalino': 'Monoclínico (C2/c)',
        'polimorfos': 'Basanita (CaSO₄·0.5H₂O) / Anhidrita (CaSO₄)',
        'fwhm_ref': 4.8
    },
    'Anhidrita (Sulfato de Calcio Anhidro)': {
        'bands': [1017, 608, 626, 674, 1128],
        'main_band': 1017,
        'category': 'Sulfatos',
        'formula': 'CaSO₄',
        'color': '#B8860B',
        'tipo': ['mineral', 'ambos'],
        'sistema_cristalino': 'Ortorrómbico (Cmcm)',
        'polimorfos': 'Yeso / Basanita',
        'fwhm_ref': 5.0
    },
    'Barita (Sulfato de Bario)': {
        'bands': [988, 453, 617, 1083, 1140],
        'main_band': 988,
        'category': 'Sulfatos / Cargas',
        'formula': 'BaSO₄',
        'color': '#D2691E',
        'tipo': ['mineral', 'ambos'],
        'sistema_cristalino': 'Ortorrómbico (Pnma)',
        'polimorfos': 'Celestina (SrSO₄) / Anglesita (PbSO₄)',
        'fwhm_ref': 4.6
    },
    'Anatasa (Dióxido de Titanio)': {
        'bands': [144, 399, 516, 639, 197],
        'main_band': 144,
        'category': 'Pigmentos Blancos / Óxidos',
        'formula': 'TiO₂',
        'color': '#2F4F4F',
        'tipo': ['pigmento', 'mineral', 'ambos'],
        'sistema_cristalino': 'Tetragonal (I4₁/amd)',
        'polimorfos': 'Rutilo (tetragonal P4₂/mnm) / Brookita (ortorrómbico)',
        'fwhm_ref': 7.8
    },
    'Rutilo (Dióxido de Titanio)': {
        'bands': [447, 612, 235, 143],
        'main_band': 447,
        'category': 'Pigmentos Blancos / Óxidos',
        'formula': 'TiO₂',
        'color': '#556B2F',
        'tipo': ['pigmento', 'mineral', 'ambos'],
        'sistema_cristalino': 'Tetragonal (P4₂/mnm)',
        'polimorfos': 'Anatasa / Brookita',
        'fwhm_ref': 15.0
    },
    'Blanco de Zinc (Cincita)': {
        'bands': [438, 332, 380, 580],
        'main_band': 438,
        'category': 'Pigmentos Blancos',
        'formula': 'ZnO',
        'color': '#B0C4DE',
        'tipo': ['pigmento', 'mineral', 'ambos'],
        'sistema_cristalino': 'Hexagonal tipo Wurtzita (P6₃mc)',
        'polimorfos': 'Zincita sintética',
        'fwhm_ref': 8.5
    },

    # -------------------------------------------------------------------------
    # 6. NEGROS Y MATERIALES CARBÓNICOS
    # -------------------------------------------------------------------------
    'Negro de Hueso / Marfil (Hidroxiapatita + Carbón)': {
        'bands': [960, 1350, 1580, 1072, 430, 588],
        'main_band': 960,
        'category': 'Pigmentos Negros',
        'formula': 'Ca₅(PO₄)₃(OH) + C',
        'color': '#1C1C1C',
        'tipo': ['pigmento', 'ambos'],
        'sistema_cristalino': 'Hexagonal (P6₃/m - Hidroxiapatita biocristalina)',
        'polimorfos': 'Fluorapatita / Clorapatita',
        'fwhm_ref': 14.0
    },
    'Carbón Vegetal / Hollín (Bandas D y G)': {
        'bands': [1350, 1585, 1600],
        'main_band': 1585,
        'category': 'Materiales Carbónicos',
        'formula': 'C (amorfo/micrografítico)',
        'color': '#333333',
        'tipo': ['pigmento', 'ambos'],
        'sistema_cristalino': 'Carbono amorfo desordenado ($sp^2/sp^3$ hibridado)',
        'polimorfos': 'Grafito / Diamante / Fullereno',
        'fwhm_ref': 40.0
    },
    'Grafito': {
        'bands': [1580, 1350, 2700],
        'main_band': 1580,
        'category': 'Materiales Carbónicos',
        'formula': 'C (grafítico)',
        'color': '#4F4F4F',
        'tipo': ['mineral', 'ambos'],
        'sistema_cristalino': 'Hexagonal estratificado (P6₃/mmc)',
        'polimorfos': 'Diamante / Grafeno',
        'fwhm_ref': 12.0
    },
    'Magnetita (Óxido de Hierro Negro)': {
        'bands': [670, 310, 540],
        'main_band': 670,
        'category': 'Óxidos de Hierro',
        'formula': 'Fe₃O₄ (Fe²⁺Fe₂³⁺O₄)',
        'color': '#2E8B57',
        'tipo': ['mineral', 'ambos'],
        'sistema_cristalino': 'Cúbico tipo Espinela Inversa (Fd-3m)',
        'polimorfos': 'Maghemita / Wüstita',
        'fwhm_ref': 16.0
    },

    # -------------------------------------------------------------------------
    # 7. SILICATOS, AGLUTINANTES Y RESINAS
    # -------------------------------------------------------------------------
    'Cuarzo / Arena Silícea': {
        'bands': [464, 206, 128, 355, 1083],
        'main_band': 464,
        'category': 'Silicatos',
        'formula': 'α-SiO₂',
        'color': '#4682B4',
        'tipo': ['mineral', 'ambos'],
        'sistema_cristalino': 'Trigonal / Cuarzo Alfa (P3₁21)',
        'polimorfos': 'Cristobalita / Tridimita / Coesita / Ópalo',
        'fwhm_ref': 4.2
    },
    'Cera de Abeja / Aglutinante Lípido': {
        'bands': [1063, 1131, 1296, 1441, 1463, 2850, 2883],
        'main_band': 1441,
        'category': 'Aglutinantes / Ceras',
        'formula': 'Ésteres y Ácidos Grasos (Palmitato de miricilo)',
        'color': '#FF8C00',
        'tipo': ['organico'],
        'sistema_cristalino': 'Sólido semicristalino parafínico',
        'polimorfos': 'Aceite de linaza / Resina',
        'fwhm_ref': 22.0
    },
    'Resina Natural (Colofonia / Copal / Almáciga)': {
        'bands': [1650, 1450, 1200, 800],
        'main_band': 1650,
        'category': 'Barnices y Resinas',
        'formula': 'Terpenoides Poliméricos',
        'color': '#D2B48C',
        'tipo': ['organico'],
        'sistema_cristalino': 'Polímero natural amorfo',
        'polimorfos': 'Barniz Dammar / Ámbar',
        'fwhm_ref': 35.0
    }
}


def identificar_banda(position_cm, tolerance=10.0, modo='completo'):
    """
    Busca coincidencias individuales para un número de onda determinado (cm^-1).
    modo: 'completo', 'pigmentos', 'cristalografia'.
    Retorna una lista de candidatos posibles ordenados por relevancia.
    """
    coincidencias = []
    modo_norm = modo.lower()
    
    for nombre, info in RAMAN_DATABASE.items():
        tipos = info.get('tipo', ['ambos'])
        
        if 'pigment' in modo_norm:
            if 'pigmento' not in tipos and 'ambos' not in tipos and 'organico' not in tipos:
                continue
        elif 'cristal' in modo_norm or 'mineral' in modo_norm:
            if 'mineral' not in tipos and 'ambos' not in tipos:
                continue
                
        for band in info['bands']:
            diff = abs(position_cm - band)
            if diff <= tolerance:
                coincidencias.append({
                    'compuesto': nombre,
                    'banda_teorica': band,
                    'diferencia': diff,
                    'es_principal': (band == info['main_band']),
                    'formula': info['formula'],
                    'categoria': info['category'],
                    'sistema_cristalino': info.get('sistema_cristalino', 'N/A'),
                    'polimorfos': info.get('polimorfos', 'Ninguno'),
                    'fwhm_ref': info.get('fwhm_ref', 8.0)
                })
                
    # Ordenar primero por si es banda principal y luego por menor diferencia de cm^-1
    coincidencias.sort(key=lambda c: (not c['es_principal'], c['diferencia']))
    return coincidencias


def identificar_espectro(peaks_positions, tolerance=12.0, min_score=25.0, modo='completo'):
    """
    Evalúa la lista completa de picos detectados en el espectro contra la base de datos.
    modo: 'completo', 'pigmentos', 'cristalografia'.
    Calcula un Score de Similitud normalizado (0 a 100%) ponderando la banda principal.
    """
    if not peaks_positions:
        return []
        
    peaks_arr = np.array(peaks_positions, dtype=float)
    candidatos = {}
    modo_norm = modo.lower()
    
    for nombre, info in RAMAN_DATABASE.items():
        tipos = info.get('tipo', ['ambos'])
        
        if 'pigment' in modo_norm:
            if 'pigmento' not in tipos and 'ambos' not in tipos and 'organico' not in tipos:
                continue
        elif 'cristal' in modo_norm or 'mineral' in modo_norm:
            if 'mineral' not in tipos and 'ambos' not in tipos:
                continue
                
        bands_teoricas = info['bands']
        main_band = info['main_band']
        
        coincidencias_bandas = []
        for b_t in bands_teoricas:
            diffs = np.abs(peaks_arr - b_t)
            min_diff = np.min(diffs)
            if min_diff <= tolerance:
                coincidencias_bandas.append(b_t)
                
        num_coincidencias = len(set(coincidencias_bandas))
        if num_coincidencias > 0:
            contiene_principal = main_band in coincidencias_bandas
            
            # Ponderación: 40% banda principal + 60% cobertura de bandas secundarias
            frac_secundarias = num_coincidencias / len(bands_teoricas)
            score_base = frac_secundarias * 60.0
            score_main = 40.0 if contiene_principal else 0.0
            
            score_final = min(100.0, score_base + score_main)
            
            if score_final >= min_score:
                candidatos[nombre] = {
                    'score': round(score_final, 1),
                    'bandas_coincidentes': num_coincidencias,
                    'total_bandas': len(bands_teoricas),
                    'formula': info['formula'],
                    'categoria': info['category'],
                    'sistema_cristalino': info.get('sistema_cristalino', 'N/A'),
                    'polimorfos': info.get('polimorfos', 'Ninguno'),
                    'fwhm_ref': info.get('fwhm_ref', 8.0),
                    'contiene_principal': contiene_principal
                }
                
    # Ordenar por mayor score
    compuestos_ordenados = sorted(candidatos.items(), key=lambda x: x[1]['score'], reverse=True)
    return compuestos_ordenados
