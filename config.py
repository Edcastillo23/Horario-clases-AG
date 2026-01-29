# --- CONVERSIÓN DE TIEMPO ---
def hora_a_minutos(hora_str):
    h, m = map(int, hora_str.split(':'))
    return h * 60 + m

# --- BACHILLERATO (Secundaria) ---
# Formato: (Inicio, Fin, Es_Clase)
TIEMPOS_BACH = [
    ("07:00", "07:50", True),  # B0
    ("07:50", "08:40", True),  # B1
    ("08:40", "09:30", True), # B2
    ("09:30", "10:00", False),  # Descanso
    ("10:00", "10:50", True),  # B3
    ("10:50", "11:40", True), # B4
    ("11:40", "12:30", True),  # B4
    ("12:30", "13:30", False),  # Almuerzo
    ("13:30", "14:20", True),  # B6
    ("14:20", "15:10", True)   # B7
]

# Para simplificar, creamos una lista limpia con sus tiempos reales en minutos
BLOQUES_SEC = []
for i, (ini, fin, es_clase) in enumerate(TIEMPOS_BACH):
    if es_clase:
        BLOQUES_SEC.append({
            'id': len(BLOQUES_SEC), # 0, 1, 2...
            'inicio': hora_a_minutos(ini),
            'fin': hora_a_minutos(fin),
            'label': f"{ini}-{fin}"
        })

# --- PRIMARIA ---
# Bloques de 50 min
TIEMPOS_PRIM = [
    ("07:00", "07:50", True),
    ("07:50", "08:40", True),
    ("08:40", "09:10", False), # Receso
    ("09:10", "10:00", True),
    ("10:00", "10:50", True),
    ("10:50", "11:00", False), # Receso
    ("11:00", "11:50", True),
    ("11:50", "12:40", True)
]
BLOQUES_PRIM = []
for i, (ini, fin, es_clase) in enumerate(TIEMPOS_PRIM):
    if es_clase:
        BLOQUES_PRIM.append({
            'id': len(BLOQUES_PRIM),
            'inicio': hora_a_minutos(ini),
            'fin': hora_a_minutos(fin),
            'label': f"{ini}-{fin}"
        })

GRUPOS_PRIMARIA = ['1°', '2°', '3°', '4°', '5°']
GRUPOS_BACHILLERATO = ['6°', '7°', '8°', '9°']
DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
TODOS_LOS_GRADOS = GRUPOS_PRIMARIA + GRUPOS_BACHILLERATO

# --- PRE-CALCULO DE COLISIONES ---
# Esto genera un diccionario: { indice_bloque_primaria: [indices_bloque_secundaria_que_chocan] }
MAPA_COLISIONES = {}

for b_prim in BLOQUES_PRIM:
    chocan = []
    for b_sec in BLOQUES_SEC:
        # Lógica de solapamiento: max(inicios) < min(finales)
        if max(b_prim['inicio'], b_sec['inicio']) < min(b_prim['fin'], b_sec['fin']):
            chocan.append(b_sec['id'])
    MAPA_COLISIONES[b_prim['id']] = chocan