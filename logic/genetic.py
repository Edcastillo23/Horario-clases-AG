import random
import copy
import config as cfg

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
        
        # 1. RESTRICCIONES CRÍTICAS (Choques Docentes)
        score += self._check_choques_internos(self.agenda_prim, len(cfg.BLOQUES_PRIM))
        score += self._check_choques_internos(self.agenda_sec, len(cfg.BLOQUES_SEC))
        score += self._check_choques_cruzados()

        # 2. ANTI-FRAGMENTACIÓN Y PEDAGOGÍA
        score += self._check_pedagogia_y_fragmentacion(self.agenda_prim)
        score += self._check_pedagogia_y_fragmentacion(self.agenda_sec)

        # 3. REGLA DEL UNIFORME Y DEPORTES (Separación de días)
        score += self._check_distribucion_deportiva(self.agenda_prim, "Primaria")
        score += self._check_distribucion_deportiva(self.agenda_sec, "Bachillerato")

        # 4. NUEVA REGLA: SINCRONIZACIÓN DE PARES (6-7 y 8-9)
        score += self._check_sincronizacion_pares(self.agenda_sec)

        # 5. COMPACIDAD (Evitar huecos a primera hora)
        score += self._check_huecos_incomodos(self.agenda_prim)
        score += self._check_huecos_incomodos(self.agenda_sec)

        self.fitness = score
        return score

    def _check_sincronizacion_pares(self, agenda):
        """
        Obliga a que pares de grados específicos tengan Edu. Física 
        exactamente al mismo tiempo.
        """
        score = 0
        # Pares a sincronizar (asegúrate que los nombres coincidan con config.py)
        # Nota: Si usas "6°" o "6", ajústalo aquí.
        pares_objetivo = [("6°", "7°"), ("8°", "9°")] 
        claves_fisica = ["física", "fisica", "deporte"]

        for g1, g2 in pares_objetivo:
            # Validar que los grupos existan en la agenda actual
            if g1 not in agenda or g2 not in agenda:
                continue

            # Recorrer toda la semana bloque a bloque
            for d in range(len(cfg.DIAS)):
                for b in range(len(cfg.BLOQUES_SEC)):
                    bloque1 = agenda[g1][d][b]
                    bloque2 = agenda[g2][d][b]

                    # Determinar si hay física en G1
                    tiene_fisica_1 = False
                    if bloque1:
                        if any(k in bloque1[0].lower() for k in claves_fisica):
                            tiene_fisica_1 = True

                    # Determinar si hay física en G2
                    tiene_fisica_2 = False
                    if bloque2:
                        if any(k in bloque2[0].lower() for k in claves_fisica):
                            tiene_fisica_2 = True

                    # EVALUACIÓN DE SINCRONÍA
                    if tiene_fisica_1 and tiene_fisica_2:
                        score += 500 # ¡Bien! Sincronizados
                    elif tiene_fisica_1 != tiene_fisica_2:
                        # Uno tiene y el otro no -> ERROR GRAVE
                        score -= 5000 
        
        return score

    def _check_pedagogia_y_fragmentacion(self, agenda):
        score = 0
        for grupo in agenda:
            bloques_unitarios_semanales = {} 

            for d_idx in range(len(cfg.DIAS)):
                bloques_dia = agenda[grupo][d_idx]
                conteo_dia = {}
                i = 0
                while i < len(bloques_dia):
                    if bloques_dia[i] is None:
                        i += 1
                        continue
                    
                    materia = bloques_dia[i][0]
                    longitud = 1
                    j = i + 1
                    while j < len(bloques_dia) and bloques_dia[j] and bloques_dia[j][0] == materia:
                        longitud += 1
                        j += 1
                    
                    conteo_dia[materia] = conteo_dia.get(materia, 0) + longitud

                    if longitud == 1:
                        bloques_unitarios_semanales[materia] = bloques_unitarios_semanales.get(materia, 0) + 1
                    elif longitud == 2:
                        score += 200 
                    elif longitud >= 3:
                        score -= 5000 

                    i = j 

                for mat, total in conteo_dia.items():
                    if total > 2:
                        score -= 2000

            for materia, cantidad_unitarios in bloques_unitarios_semanales.items():
                if cantidad_unitarios > 1:
                    penalizacion = (cantidad_unitarios - 1) * 800
                    score -= penalizacion
        return score

    def _check_distribucion_deportiva(self, agenda, nivel):
        score = 0
        claves_fisica = ["física", "fisica", "deporte"]
        claves_danza = ["danza", "baile", "danzas"]

        for grupo in agenda:
            dias_fisica = {} 
            dias_danza = {}  

            for d_idx in range(len(cfg.DIAS)):
                h_f = 0
                h_d = 0
                for bloque in agenda[grupo][d_idx]:
                    if bloque:
                        nm = bloque[0].lower()
                        if any(k in nm for k in claves_fisica): h_f += 1
                        if any(k in nm for k in claves_danza): h_d += 1
                
                if h_f > 0: dias_fisica[d_idx] = h_f
                if h_d > 0: dias_danza[d_idx] = h_d

            if nivel == "Primaria":
                dia_uniforme_found = False
                dias_solo_danza = []
                all_days = set(dias_fisica.keys()) | set(dias_danza.keys())
                
                for d in all_days:
                    hf = dias_fisica.get(d, 0)
                    hd = dias_danza.get(d, 0)

                    if hf >= 1 and hd >= 1:
                        if hf == 2 and hd == 1:
                            score += 5000 
                            dia_uniforme_found = True
                        else:
                            score += 500 
                    elif hf > 0 and hd == 0:
                        score -= 2000 
                    elif hd > 0 and hf == 0:
                        dias_solo_danza.append(d)

                if dia_uniforme_found and dias_solo_danza:
                    dias_mix = [d for d, h in dias_fisica.items() if dias_danza.get(d, 0) > 0]
                    for d_mix in dias_mix:
                        for d_danza in dias_solo_danza:
                            dist = abs(d_mix - d_danza)
                            if dist == 1: score -= 3000 
                            else: score += 1000 

            elif nivel == "Bachillerato":
                l_fis = list(dias_fisica.keys())
                l_dan = list(dias_danza.keys())
                if l_fis and l_dan:
                    for df in l_fis:
                        for dd in l_dan:
                            dist = abs(df - dd)
                            if dist == 0: score -= 3000
                            elif dist == 1: score -= 2000
                            else: score += 500
        return score

    def _check_huecos_incomodos(self, agenda):
        score = 0
        for grupo in agenda:
            for d_idx in range(len(cfg.DIAS)):
                bloques = agenda[grupo][d_idx]
                if blocks_are_empty(bloques[0]):
                    if any(b is not None for b in bloques):
                        score -= 200
        return score

    def _check_choques_internos(self, agenda, num_bloques):
        penalizacion = 0
        for d in range(len(cfg.DIAS)):
            for b in range(num_bloques):
                profes = [agenda[g][d][b][1] for g in agenda if agenda[g][d][b] is not None]
                if len(profes) != len(set(profes)):
                    penalizacion -= 5000 
        return penalizacion

    def _check_choques_cruzados(self):
        penalizacion = 0
        for d_idx in range(len(cfg.DIAS)):
            for b_prim in range(len(cfg.BLOQUES_PRIM)):
                profes_prim = set()
                for g in cfg.GRUPOS_PRIMARIA:
                    clase = self.agenda_prim[g][d_idx][b_prim]
                    if clase: profes_prim.add(clase[1])
                if not profes_prim: continue

                bloques_sec = cfg.MAPA_COLISIONES.get(b_prim, [])
                for b_sec in bloques_sec:
                    for g_sec in cfg.GRUPOS_BACHILLERATO:
                        clase_sec = self.agenda_sec[g_sec][d_idx][b_sec]
                        if clase_sec and clase_sec[1] in profes_prim:
                            penalizacion -= 5000
        return penalizacion

def blocks_are_empty(bloque):
    return bloque is None

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