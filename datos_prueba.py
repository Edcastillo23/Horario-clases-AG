import data_manager as dm
import config as cfg

def cargar_datos_complejos():
    print("--- CARGANDO ESCENARIO REALISTA (DICCIONARIO) ---")
    
    # 1. Limpiar memoria
    dm.BASE_DATOS["docentes"] = []
    dm.BASE_DATOS["asignaciones"] = []

    # =========================================================================
    # DICCIONARIO MAESTRO DE CARGA ACADÉMICA
    # Estructura: 
    # "Nombre Docente": [
    #      ( "Materia",  Horas_Semanales,  [Lista_de_Grados] ),
    #      ( "Otra Materia", Horas, [Otros_Grados] )
    # ]
    # =========================================================================
    
    CARGA_ACADEMICA = {
        # --- DOCENTES DE PRIMARIA ---
        " Profe Angélica": [
            ("Matemáticas", 6, ["1°"]),
            ("Lengua",      6, ["1°"]),
            ("Ética",       1, ["1°"]),
            ("Sociales",    2, ["1°"]),
            ("Religión",    1, ["1°"]),
            ("Naturales",   2, ["1°"]),
            ("Inglés",      4, ["1°","2°"])
        ],
        "Profe Diana": [
            ("Matemáticas", 6, ["2°"]),
            ("Lengua",      6, ["2°"]),
            ("Ética",       1, ["2°"]),
            ("Sociales",    2, ["2°"]),
            ("Religión",    1, ["2°"]),
            ("Naturales",   2, ["2°"])
        ],
        "Profe Clara": [
            ("Matemáticas", 6, ["3°"]),
            ("Lengua",      6, ["3°"]),
            ("Ética",       1, ["3°"]),
            ("Sociales",    2, ["3°"]),
            ("Religión",    1, ["3°"]),
            ("Naturales",   2, ["3°"])
        ],
        "Profe Jhoana": [
            ("Matemáticas", 6, ["4°"]),
            ("Lengua",      6, ["4°"]),
            ("Ética",       1, ["4°"]),
            ("Sociales",    2, ["4°"]),
            ("Religión",    1, ["4°"]),
            ("Naturales",   2, ["4°"]),
            ("Sociales",    4, ["5°","6°","7°","8°","9°"])     
        ],
        "Profe Liliana": [
            ("Ética",       1, ["5°","6°","7°","8°","9°"]),
            ("Religión",    1, ["5°","6°","7°","8°","9°"]),
            ("Ambiental",   1, ["6°","7°","8°","9°"]),
            ("Naturales",   4, ["5°","6°","7°","8°","9°"])    
        ],
        "Profe Edinson": [
            ("Matemáticas", 6, ["5°","6°","7°","8°","9°"]),
            ("Tecnología",  2, ["6°","7°","8°","9°"])    
        ],
        "Profe Juan David": [
            ("Informática", 1, ["6°","7°","8°","9°"]),
            ("Informática", 2, ["1°","2°","3°","4°","5°"]),
            ("Artística",   2, ["6°","7°","8°","9°"]),
            ("Edu. Física", 2, ["6°","7°","8°","9°"])    
        ],   
        "Profe Cristina": [
            ("Inglés", 6, ["6°","7°","8°","9°"]),
            ("Inglés", 4, ["3°","4°","5°"])    
        ],
        "Profe Sebastian": [
            ("Música", 2, ["6°","7°","8°","9°"])
        ], 
        "Profe Sandra": [
            ("Lengua", 6, ["6°","7°","8°","9°"]),
            ("Lengua", 6, ["5°"])
        ],    
        "Profe Felix": [
            ("Artística",   2, ["1°","2°","3°","4°","5°"]),
            ("Edu. Física", 2, ["1°","2°","3°","4°","5°"])
        ],
        "Profe Juancho": [
            ("Danza", 1, ["1°","2°","3°","4°","5°"] ),
            ("Danza2", 1, ["1°","2°","3°","4°","5°"]),
            ("Danza", 2, ["6°","7°","8°","9°"])
        ]
        
    }

    # =========================================================================
    # LÓGICA DE PROCESAMIENTO (NO TOCAR)
    # =========================================================================
    
    count_asignaciones = 0

    for nombre_docente, lista_materias in CARGA_ACADEMICA.items():
        
        # 1. Determinar automáticamente los grados habilitados para este docente
        # Recorremos todas sus materias y recolectamos los grados únicos
        grados_habilitados = set()
        for _, _, grupos in lista_materias:
            for g in grupos:
                grados_habilitados.add(g)
        
        # Convertimos a lista y ordenamos (opcional, por estética)
        lista_grados_final = sorted(list(grados_habilitados))
        
        # 2. Crear y guardar al Docente
        nuevo_docente = dm.Docente(nombre_docente, lista_grados_final)
        dm.BASE_DATOS["docentes"].append(nuevo_docente)
        
        # 3. Crear las asignaciones
        for materia, horas, grupos in lista_materias:
            # Validar que los grupos existan en la config (para evitar errores de dedo)
            grupos_validos = [g for g in grupos if g in cfg.TODOS_LOS_GRADOS]
            
            if not grupos_validos:
                print(f"[WARN] La materia {materia} de {nombre_docente} no tiene grupos válidos.")
                continue

            nueva_asig = dm.Asignacion(
                materia=materia,
                docente=nuevo_docente,
                horas=horas,
                grupos_asignados=grupos_validos
            )
            dm.BASE_DATOS["asignaciones"].append(nueva_asig)
            count_asignaciones += 1

    print(f"✅ Carga Completa: {len(dm.BASE_DATOS['docentes'])} docentes y {count_asignaciones} bloques de asignación generados.")