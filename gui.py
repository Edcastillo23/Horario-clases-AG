import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import copy
import random
from gui_resultados import VentanaResultados 

# --- IMPORTACIÓN DE MÓDULOS PROPIOS ---
try:
    import config as cfg
    import data_manager as dm
    try:
        from logic import genetic as ag
    except ImportError:
        ag = None
except ImportError as e:
    print(f"Error crítico: Faltan archivos de configuración ({e}).")
    exit()

class AplicacionHorario(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Horarios: Primaria y Bachillerato")
        self.geometry("950x700") # Un poco más grande para acomodar los grados
        
        # Estilos
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", rowheight=25)

        # --- PESTAÑAS ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.tab_docentes = ttk.Frame(self.notebook)
        self.tab_asignacion = ttk.Frame(self.notebook)
        self.tab_generar = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_docentes, text=" 1. Registro de Docentes ")
        self.notebook.add(self.tab_asignacion, text=" 2. Carga Académica ")
        self.notebook.add(self.tab_generar, text=" 3. Generar Horario ")

        self._setup_tab_docentes()
        self._setup_tab_asignacion()
        self._setup_tab_generar()

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    # ==========================================
    # PESTAÑA 1: DOCENTES (MODIFICADA)
    # ==========================================
    def _setup_tab_docentes(self):
        # Panel Izquierdo: Formulario
        frame_form = ttk.LabelFrame(self.tab_docentes, text="Registrar Nuevo Docente")
        frame_form.pack(side="left", fill="y", padx=10, pady=10)

        ttk.Label(frame_form, text="Nombre del Docente:").pack(anchor="w", padx=5, pady=5)
        self.entry_nombre = ttk.Entry(frame_form, width=30)
        self.entry_nombre.pack(padx=5, pady=5)

        # --- SECCIÓN DE GRADOS HABILITADOS (MODIFICACIÓN CLAVE) ---
        lbl_grados = ttk.Label(frame_form, text="Seleccione grados habilitados:", font=("Arial", 9, "bold"))
        lbl_grados.pack(anchor="w", padx=5, pady=(15, 5))

        self.vars_grados_docente = {}
        frame_checks = ttk.Frame(frame_form)
        frame_checks.pack(fill="x", padx=10)

        # Combinamos las listas de grados de config
        grados_totales = cfg.GRUPOS_PRIMARIA + cfg.GRUPOS_BACHILLERATO

        # Generar cuadrícula de checkboxes
        for i, grado in enumerate(grados_totales):
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(frame_checks, text=grado, variable=var)
            # Organizar en 3 columnas
            chk.grid(row=i//3, column=i%3, sticky="w", padx=5, pady=2)
            self.vars_grados_docente[grado] = var

        btn_add = ttk.Button(frame_form, text="Guardar Docente", command=self.agregar_docente)
        btn_add.pack(pady=20, fill="x", padx=5)

        # Panel Derecho: Tabla
        self.tree_docentes = ttk.Treeview(self.tab_docentes, columns=("Nombre", "Grados"), show="headings")
        self.tree_docentes.heading("Nombre", text="Nombre")
        self.tree_docentes.heading("Grados", text="Grados Habilitados")
        self.tree_docentes.column("Grados", width=400)
        self.tree_docentes.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    def agregar_docente(self):
        nombre = self.entry_nombre.get().strip()
        
        # Recopilar qué grados se marcaron
        seleccionados = [g for g, v in self.vars_grados_docente.items() if v.get()]

        if not nombre:
            messagebox.showerror("Error", "Debe ingresar un nombre.")
            return
        if not seleccionados:
            messagebox.showwarning("Cuidado", "Debe seleccionar al menos un grado.")
            return

        # Verificar duplicados
        if any(d.nombre == nombre for d in dm.BASE_DATOS["docentes"]):
            messagebox.showerror("Error", "Ya existe un docente con ese nombre.")
            return

        # Guardar en Data Manager (Pasamos la lista de grados, no booleanos)
        nuevo = dm.Docente(nombre, seleccionados)
        dm.BASE_DATOS["docentes"].append(nuevo)

        # Actualizar Tabla Visual
        self.tree_docentes.insert("", "end", values=(nombre, ", ".join(seleccionados)))

        # Limpiar formulario
        self.entry_nombre.delete(0, tk.END)
        for v in self.vars_grados_docente.values(): v.set(False)

    # ==========================================
    # PESTAÑA 2: ASIGNACIÓN
    # ==========================================
    def _setup_tab_asignacion(self):
        frame_left = ttk.Frame(self.tab_asignacion)
        frame_left.pack(side="left", fill="y", padx=10, pady=10)
        
        ttk.Label(frame_left, text="Docente:").pack(anchor="w")
        self.combo_docentes = ttk.Combobox(frame_left, state="readonly")
        self.combo_docentes.pack(fill="x", pady=5)
        self.combo_docentes.bind("<<ComboboxSelected>>", self.al_seleccionar_docente_combo)

        ttk.Label(frame_left, text="Materia:").pack(anchor="w")
        self.entry_materia = ttk.Entry(frame_left)
        self.entry_materia.pack(fill="x", pady=5)

        ttk.Label(frame_left, text="Horas/Semana:").pack(anchor="w")
        self.spin_horas = ttk.Spinbox(frame_left, from_=1, to=10, width=5)
        self.spin_horas.set(4)
        self.spin_horas.pack(pady=5)

        ttk.Label(frame_left, text="Grupos Destino:", font=("Arial", 9, "bold")).pack(anchor="w", pady=(10,5))
        
        self.vars_grupos = {}
        self.widgets_grupos = {}
        
        # Checkboxes de grupos (Primaria y Bachillerato juntos)
        grados_totales = cfg.GRUPOS_PRIMARIA + cfg.GRUPOS_BACHILLERATO
        for g in grados_totales:
            v = tk.BooleanVar()
            chk = ttk.Checkbutton(frame_left, text=g, variable=v)
            chk.pack(anchor="w")
            self.vars_grupos[g] = v
            self.widgets_grupos[g] = chk

        ttk.Button(frame_left, text="Asignar Carga", command=self.agregar_asignacion).pack(fill="x", pady=20)

        # Tabla derecha
        self.tree_asignaciones = ttk.Treeview(self.tab_asignacion, columns=("M", "D", "H", "G"), show="headings")
        self.tree_asignaciones.heading("M", text="Materia"); self.tree_asignaciones.column("M", width=100)
        self.tree_asignaciones.heading("D", text="Docente"); self.tree_asignaciones.column("D", width=150)
        self.tree_asignaciones.heading("H", text="Hrs"); self.tree_asignaciones.column("H", width=50)
        self.tree_asignaciones.heading("G", text="Grupos"); self.tree_asignaciones.column("G", width=250)
        self.tree_asignaciones.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    def on_tab_change(self, event):
        # Refrescar lista de docentes al entrar a Tab 2
        if self.notebook.index(self.notebook.select()) == 1:
            self.combo_docentes['values'] = [d.nombre for d in dm.BASE_DATOS["docentes"]]

    def al_seleccionar_docente_combo(self, event):
        nombre_sel = self.combo_docentes.get()
        docente = next((d for d in dm.BASE_DATOS["docentes"] if d.nombre == nombre_sel), None)
        
        if not docente: return

        # Habilitar solo los grados que el docente tiene en su lista "grados_habilitados"
        for grado, widget in self.widgets_grupos.items():
            if hasattr(docente, 'grados_habilitados') and grado in docente.grados_habilitados:
                widget.configure(state="normal")
            else:
                widget.configure(state="disabled")
                self.vars_grupos[grado].set(False)

    def agregar_asignacion(self):
        doc = self.combo_docentes.get()
        mat = self.entry_materia.get().strip()
        grupos = [g for g, v in self.vars_grupos.items() if v.get()]
        
        if not doc or not mat:
            messagebox.showerror("Error", "Faltan datos.")
            return
        if not grupos:
            messagebox.showerror("Error", "Seleccione al menos un grupo.")
            return

        try:
            horas = int(self.spin_horas.get())
        except ValueError:
            horas = 4

        d_obj = next(d for d in dm.BASE_DATOS["docentes"] if d.nombre == doc)
        dm.BASE_DATOS["asignaciones"].append(dm.Asignacion(mat, d_obj, horas, grupos))
        
        self.tree_asignaciones.insert("", "end", values=(mat, doc, horas, ", ".join(grupos)))
        
        # Resetear
        for v in self.vars_grupos.values(): v.set(False)

    # ==========================================
    # PESTAÑA 3: GENERAR
    # ==========================================
    def _setup_tab_generar(self):
        self.btn_run = ttk.Button(self.tab_generar, text=">>> GENERAR HORARIO ÓPTIMO <<<", command=self.ejecutar_algoritmo)
        self.btn_run.pack(pady=20, ipadx=10, ipady=5)
        
        self.txt_log = tk.Text(self.tab_generar, height=20, width=90, bg="#f0f0f0")
        self.txt_log.pack(padx=20, pady=10)

    def log(self, msg):
        self.txt_log.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.txt_log.see(tk.END)

    def ejecutar_algoritmo(self):
        if not dm.BASE_DATOS["asignaciones"]:
            messagebox.showwarning("Atención", "No hay carga académica para procesar.")
            return
        
        self.btn_run.config(state="disabled")
        # Hilo daemon para que se cierre si cerramos la app
        threading.Thread(target=self.proceso_ag_background, daemon=True).start()

    def proceso_ag_background(self):
        try:
            # --- PARÁMETROS OPTIMIZADOS ---
            pob_size = 500  
            gens = 2000
            
            # Tasa de mutación dinámica
            tasa_mutacion_base = 0.2
            tasa_mutacion_actual = tasa_mutacion_base
            
            self.log(f"Iniciando Motor Genético Inteligente...")
            self.log(f"Población: {pob_size} | Generaciones Máx: {gens}")
            
            # 1. Inicialización
            poblacion = [ag.HorarioGenetico() for _ in range(pob_size)]
            for h in poblacion:
                h.inicializar(dm.BASE_DATOS["asignaciones"])
                h.calcular_fitness()

            best = copy.deepcopy(poblacion[0])
            generaciones_sin_mejora = 0

            # 2. Ciclo Evolutivo
            for gen in range(gens):
                # Ordenar: Los mejores (fitness cercano a 0) arriba
                poblacion.sort(key=lambda x: x.fitness, reverse=True)
                
                mejor_actual = poblacion[0]
                
                # --- DETECCIÓN DE MEJORA ---
                if mejor_actual.fitness > best.fitness:
                    diff = mejor_actual.fitness - best.fitness
                    best = copy.deepcopy(mejor_actual)
                    generaciones_sin_mejora = 0
                    tasa_mutacion_actual = tasa_mutacion_base # Resetear mutación si mejoramos
                    self.log(f"Gen {gen}: Mejora encontrada! Fitness = {best.fitness}")
                else:
                    generaciones_sin_mejora += 1

                # --- ESTRATEGIA DE SALIDA ---
                if best.fitness == 0:
                    self.log("¡Solución PERFECTA encontrada (Fitness 0)!")
                    break
                
                # --- ESTRATEGIA ANTI-ESTANCAMIENTO ---
                # Si llevamos 50 generaciones atascados, nos volvemos agresivos
                if generaciones_sin_mejora > 50:
                    tasa_mutacion_actual = 0.6 # Mutación agresiva (60%)
                    if generaciones_sin_mejora % 50 == 0:
                        self.log(f"⚠ Estancado {generaciones_sin_mejora} gens. Aumentando mutación a {int(tasa_mutacion_actual*100)}%...")
                elif generaciones_sin_mejora > 20:
                    tasa_mutacion_actual = 0.4
                else:
                    tasa_mutacion_actual = tasa_mutacion_base

                # --- EVOLUCIÓN (CRUCE Y MUTACIÓN) ---
                nueva_pob = []
                
                # ELITISMO: Guardamos los 2 mejores intactos
                nueva_pob.append(best)
                nueva_pob.append(copy.deepcopy(poblacion[1]))
                
                # RELLENO
                while len(nueva_pob) < pob_size:
                    # Torneo: Elegimos 2 pares al azar y pelean
                    p1 = max(random.sample(poblacion[:50], 2), key=lambda x: x.fitness) # Elige de los 50 mejores
                    p2 = max(random.sample(poblacion[:50], 2), key=lambda x: x.fitness)
                    
                    hijo = ag.cruzar(p1, p2)
                    
                    # Mutación dinámica
                    if random.random() < tasa_mutacion_actual:
                        ag.mutar(hijo)
                    
                    hijo.calcular_fitness()
                    nueva_pob.append(hijo)
                
                poblacion = nueva_pob
                
                # Refresco visual moderado
                if gen % 20 == 0: time.sleep(0.001)

            self.log("--- PROCESO TERMINADO ---")
            self.log(f"Calificación Final: {best.fitness}")
            
            if best.fitness < 0:
                self.log("NOTA: Si el fitness es negativo, aún hay reglas rotas.")
                self.log("Intenta correrlo de nuevo o revisa la disponibilidad docente.")

            self.btn_run.config(state="normal")
            self.after(100, lambda: self.abrir_ventana_resultados(best))
            
        except Exception as e:
            self.log(f"Error Crítico en AG: {e}")
            print(e)
            self.btn_run.config(state="normal")

    def abrir_ventana_resultados(self, horario_generado):
        vent = VentanaResultados(self, horario_generado)
        vent.grab_set()
        vent.focus_set()

if __name__ == "__main__":
    app = AplicacionHorario()
    app.mainloop()