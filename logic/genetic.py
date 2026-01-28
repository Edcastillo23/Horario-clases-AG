import random
import copy
import config as cfg
import data_manager as dm

class HorarioGenetico:
    def __init__(self):
        self.agenda_prim = {g: [[None for _ in cfg.BLOQUES_PRIM] for _ in cfg.DIAS] for g in cfg.GRUPOS_PRIMARIA}
        self.agenda_sec = {g: [[None for _ in cfg.BLOQUES_SEC] for _ in cfg.DIAS] for g in cfg.GRUPOS_BACHILLERATO}
        self.fitness = 0

    def inicializar(self, asignaciones):
        pendientes_prim = {g: [] for g in cfg.GRUPOS_PRIMARIA}
        pendientes_sec = {g: [] for g in cfg.GRUPOS_BACHILLERATO}

        for asig in asignaciones:
            info_clase = (asig.materia, asig.docente.nombre)
            for grupo in asig.grupos:
                if grupo in cfg.GRUPOS_PRIMARIA:
                    pendientes_prim[grupo].extend([info_clase] * asig.horas)
                elif grupo in cfg.GRUPOS_BACHILLERATO:
                    pendientes_sec[grupo].extend([info_clase] * asig.horas)

        self._rellenar_nivel(self.agenda_prim, pendientes_prim, len(cfg.BLOQUES_PRIM))
        self._rellenar_nivel(self.agenda_sec, pendientes_sec, len(cfg.BLOQUES_SEC))

    def _rellenar_nivel(self, agenda, pendientes, num_bloques):
        dias = len(cfg.DIAS)
        total_slots = dias * num_bloques
        for grupo, lista_clases in pendientes.items():
            huecos = total_slots - len(lista_clases)
            semana_mix = lista_clases + [None] * huecos
            random.shuffle(semana_mix)
            idx = 0
            for d in range(dias):
                for b in range(num_bloques):
                    agenda[grupo][d][b] = semana_mix[idx]
                    idx += 1

    def calcular_fitness(self):
        score = 0
        
        # 1. RESTRICCIÓN DURA: Choques de Docente (Mismo Nivel y Cruzado)
        score += self._check_choques_internos(self.agenda_prim, len(cfg.BLOQUES_PRIM))
        score += self._check_choques_internos(self.agenda_sec, len(cfg.BLOQUES_SEC))
        score += self._check_choques_cruzados()

        # 2. NUEVA RESTRICCIÓN: Pedagogía de Bloques y Máximo Diario
        score += self._check_pedagogia_grupos(self.agenda_prim, "Primaria")
        score += self._check_pedagogia_grupos(self.agenda_sec, "Bachillerato")

        self.fitness = score
        return score

    def _check_pedagogia_grupos(self, agenda, nivel):
        """Verifica bloques de 2 horas, máximo 2h/día y prohibición de 3h+ seguidas"""
        penalizacion = 0
        
        for grupo in agenda:
            for d_idx in range(len(cfg.DIAS)):
                dia_clases = agenda[grupo][d_idx] # Lista de materias del día
                
                # Diccionario para contar horas totales de cada materia en el día
                conteo_dia = {}
                
                # Analizar bloques consecutivos
                i = 0
                while i < len(dia_clases):
                    clase_actual = dia_clases[i]
                    
                    if clase_actual is None:
                        i += 1
                        continue
                    
                    materia = clase_actual[0]
                    conteo_dia[materia] = conteo_dia.get(materia, 0) + 1
                    
                    # Medir duración del bloque consecutivo
                    duracion_bloque = 1
                    j = i + 1
                    while j < len(dia_clases) and dia_clases[j] is not None and dia_clases[j][0] == materia:
                        duracion_bloque += 1
                        j += 1
                    
                    # REGLA: Bloques de exactamente 2 horas
                    if duracion_bloque == 1:
                        # Si la materia tiene más de 1 hora semanal, no debería estar sola
                        penalizacion -= 100 
                    elif duracion_bloque == 2:
                        penalizacion += 50 # Premio por cumplir el bloque doble
                    elif duracion_bloque >= 3:
                        # REGLA: Nunca 3 horas o más seguidas
                        penalizacion -= 1000 
                    
                    i = j # Saltar al final del bloque analizado

                # REGLA: No más de 2 horas de la misma materia al día para el grupo
                for materia, total_horas in conteo_dia.items():
                    if total_horas > 2:
                        penalizacion -= 800

        return penalizacion

    def _check_choques_internos(self, agenda, num_bloques):
        penalizacion = 0
        for d in range(len(cfg.DIAS)):
            for b in range(num_bloques):
                profes = [agenda[g][d][b][1] for g in agenda if agenda[g][d][b] is not None]
                dupes = len(profes) - len(set(profes))
                if dupes > 0:
                    penalizacion -= (500 * dupes)
        return penalizacion

    def _check_choques_cruzados(self):
        penalizacion = 0
        for d_idx in range(len(cfg.DIAS)):
            for b_prim_idx in range(len(cfg.BLOQUES_PRIM)):
                profes_prim = [self.agenda_prim[g][d_idx][b_prim_idx][1] 
                            for g in cfg.GRUPOS_PRIMARIA if self.agenda_prim[g][d_idx][b_prim_idx]]
                
                if not profes_prim: continue
                
                bloques_sec_conflictivos = cfg.MAPA_COLISIONES.get(b_prim_idx, [])
                for b_sec_idx in bloques_sec_conflictivos:
                    for g_sec in cfg.GRUPOS_BACHILLERATO:
                        clase_sec = self.agenda_sec[g_sec][d_idx][b_sec_idx]
                        if clase_sec and clase_sec[1] in profes_prim:
                            penalizacion -= 1000
        return penalizacion

# --- OPERADORES (Cruce y Mutación se mantienen igual) ---
def cruzar(padre1, padre2):
    hijo = HorarioGenetico()
    for g in cfg.GRUPOS_PRIMARIA:
        hijo.agenda_prim[g] = copy.deepcopy(padre1.agenda_prim[g] if random.random() > 0.5 else padre2.agenda_prim[g])
    for g in cfg.GRUPOS_BACHILLERATO:
        hijo.agenda_sec[g] = copy.deepcopy(padre1.agenda_sec[g] if random.random() > 0.5 else padre2.agenda_sec[g])
    return hijo

def mutar(ind):
    es_prim = random.random() < 0.5
    agenda = ind.agenda_prim if es_prim else ind.agenda_sec
    grupos = cfg.GRUPOS_PRIMARIA if es_prim else cfg.GRUPOS_BACHILLERATO
    n_bloques = len(cfg.BLOQUES_PRIM) if es_prim else len(cfg.BLOQUES_SEC)
    
    g = random.choice(grupos)
    d1, b1 = random.randint(0, 4), random.randint(0, n_bloques-1)
    d2, b2 = random.randint(0, 4), random.randint(0, n_bloques-1)
    agenda[g][d1][b1], agenda[g][d2][b2] = agenda[g][d2][b2], agenda[g][d1][b1]