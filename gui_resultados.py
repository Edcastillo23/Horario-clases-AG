import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import config as cfg 
from matplotlib.backends.backend_pdf import PdfPages
import data_manager as dm
import time

class VentanaResultados(tk.Toplevel):
    def __init__(self, parent, horario_generado):
        super().__init__(parent)
        self.title("Horario Final Generado")
        self.geometry("1100x700")
        self.horario = horario_generado
        
        # Estilo visual
        self.configure(bg="#f0f0f0")

        # --- 1. CABECERA Y CONTROLES ---
        frame_controls = ttk.Frame(self)
        frame_controls.pack(side="top", fill="x", padx=10, pady=10)

        ttk.Label(frame_controls, text="Seleccionar Nivel y Grupo:", font=("Arial", 11, "bold")).pack(side="left", padx=5)

        # Selector de Nivel (Pestañas lógicas)
        self.nivel_var = tk.StringVar(value="Bachillerato")
        self.combo_nivel = ttk.Combobox(frame_controls, textvariable=self.nivel_var, state="readonly", width=15)
        self.combo_nivel['values'] = ["Primaria", "Bachillerato"]
        self.combo_nivel.pack(side="left", padx=5)
        self.combo_nivel.bind("<<ComboboxSelected>>", self.actualizar_lista_grupos)

        # Selector de Grupo
        self.grupo_var = tk.StringVar()
        self.combo_grupo = ttk.Combobox(frame_controls, textvariable=self.grupo_var, state="readonly", width=10)
        self.combo_grupo.pack(side="left", padx=5)
        self.combo_grupo.bind("<<ComboboxSelected>>", self.dibujar_horario)

        # Botones de Acción
        btn_png = ttk.Button(frame_controls, text="💾 Descargar PNG", command=lambda: self.exportar("png"))
        btn_png.pack(side="right", padx=5)
        
        btn_pdf = ttk.Button(frame_controls, text="📄 Descargar PDF", command=lambda: self.exportar("pdf"))
        btn_pdf.pack(side="right", padx=5)

        btn_pdf = ttk.Button(frame_controls, text="📄 Reporte Completo PDF", command=self.exportar_reporte_completo_pdf)
        btn_pdf.pack(side="right", padx=5)

        btn_excel = ttk.Button(frame_controls, text="📊 Exportar Excel", command=self.exportar_excel)
        btn_excel.pack(side="right", padx=5)

        # --- 2. ÁREA DE DIBUJO (CANVAS) ---
        self.frame_plot = tk.Frame(self, bg="white", bd=2, relief="sunken")
        self.frame_plot.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Variables para Matplotlib
        self.fig = None
        self.canvas = None

        # Inicializar
        self.actualizar_lista_grupos(None)

    def exportar_excel(self):
        import pandas as pd
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            initialfile="Horario_Completo.xlsx"
        )
        if not filename: return

        try:
            # Crear DataFrames para Primaria
            data_prim = []
            horas_prim = [b['label'] for b in cfg.BLOQUES_PRIM]
            dias = cfg.DIAS
            
            for g in cfg.GRUPOS_PRIMARIA:
                for b_idx, hora in enumerate(horas_prim):
                    fila = {'Grupo': g, 'Hora': hora}
                    for d_idx, dia in enumerate(dias):
                        clase = self.horario.agenda_prim[g][d_idx][b_idx]
                        if clase:
                            fila[dia] = f"{clase[0]}\n({clase[1]})"
                        else:
                            fila[dia] = ""
                    data_prim.append(fila)
            
            df_prim = pd.DataFrame(data_prim)

            # Crear DataFrames para Bachillerato
            data_sec = []
            horas_sec = [b['label'] for b in cfg.BLOQUES_SEC]
            
            for g in cfg.GRUPOS_BACHILLERATO:
                for b_idx, hora in enumerate(horas_sec):
                    fila = {'Grupo': g, 'Hora': hora}
                    for d_idx, dia in enumerate(dias):
                        clase = self.horario.agenda_sec[g][d_idx][b_idx]
                        if clase:
                            fila[dia] = f"{clase[0]}\n({clase[1]})"
                        else:
                            fila[dia] = ""
                    data_sec.append(fila)
            
            df_sec = pd.DataFrame(data_sec)

            # Guardar en un solo Excel con dos hojas
            with pd.ExcelWriter(filename) as writer:
                df_prim.to_excel(writer, sheet_name='Primaria', index=False)
                df_sec.to_excel(writer, sheet_name='Bachillerato', index=False)
                
            messagebox.showinfo("Éxito", "Excel generado correctamente.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al exportar Excel: {e}")

    def actualizar_lista_grupos(self, event):
        nivel = self.nivel_var.get()
        if nivel == "Primaria":
            self.combo_grupo['values'] = cfg.GRUPOS_PRIMARIA
        else:
            self.combo_grupo['values'] = cfg.GRUPOS_BACHILLERATO
        
        if self.combo_grupo['values']:
            self.combo_grupo.current(0)
            self.dibujar_horario(None)

    def dibujar_horario(self, event):
        # Limpiar gráfico anterior
        for widget in self.frame_plot.winfo_children():
            widget.destroy()

        nivel = self.nivel_var.get()
        grupo = self.grupo_var.get()

        # 1. Preparar Datos
        if nivel == "Primaria":
            agenda = self.horario.agenda_prim
            bloques_info = cfg.BLOQUES_PRIM # Debes tener los textos de hora aquí
            # Si BLOQUES_PRIM en config es diccionario, asegura tener una lista de etiquetas
            
            etiquetas_horas = [b['label'] for b in cfg.BLOQUES_PRIM] # Asumiendo estructura dict
        else:
            agenda = self.horario.agenda_sec
            etiquetas_horas = [b['label'] for b in cfg.BLOQUES_SEC]

        dias = cfg.DIAS
        
        # Crear matriz de texto para la tabla
        cell_text = []
        cell_colors = []
        
        for b_idx in range(len(etiquetas_horas)):
            fila = []
            fila_colores = []
            for d_idx in range(len(dias)):
                # Obtener clase: agenda[grupo][dia][bloque]
                try:
                    clase = agenda[grupo][d_idx][b_idx]
                    if clase:
                        # clase es (Materia, Profe)
                        texto = f"{clase[0]}\n({clase[1]})"
                        col = "#e1f5fe" # Azul muy claro para clases
                    else:
                        texto = ""
                        col = "#ffffff" # Blanco para huecos
                except IndexError:
                    texto = "Err"
                    col = "red"
                
                fila.append(texto)
                fila_colores.append(col)
            cell_text.append(fila)
            cell_colors.append(fila_colores)

        # 2. Configurar Matplotlib
        # Ajustamos el tamaño de la figura (width, height) en pulgadas
        self.fig, ax = plt.subplots(figsize=(10, 6))
        
        # Ocultar ejes (no queremos plano cartesiano X,Y)
        ax.axis('tight')
        ax.axis('off')
        
        # Crear la tabla
        table = ax.table(
            cellText=cell_text,
            cellColours=cell_colors,
            rowLabels=etiquetas_horas,
            colLabels=dias,
            loc='center',
            cellLoc='center'
        )

        # Estilizar la tabla
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.8) # Escalar altura de celdas (Ancho, Alto)

        # Poner negrita a los encabezados
        for (row, col), cell in table.get_celld().items():
            if row == -1 or col == -1:
                cell.set_text_props(weight='bold')
                cell.set_facecolor('#cfd8dc') # Gris suave para cabeceras

        # Título del Gráfico
        ax.set_title(f"Horario: {grupo} ({nivel})", fontsize=14, weight='bold', pad=20)

        # 3. Incrustar en Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_plot)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def exportar(self, formato):
        if not self.fig: return
        
        grupo = self.grupo_var.get()
        nivel = self.nivel_var.get()
        
        filename = filedialog.asksaveasfilename(
            defaultextension=f".{formato}",
            filetypes=[(f"Archivo {formato.upper()}", f"*.{formato}")],
            initialfile=f"Horario_{nivel}_{grupo}.{formato}"
        )
    def obtener_horario_docente(self, nombre_profe):
        """
        Busca en todos los niveles y grupos para construir 
        la agenda semanal de un profesor específico.
        """
        # Estructura: [Día][Bloque] -> "Materia (Grado)"
        # Usamos el máximo de bloques disponibles (Bachillerato)
        agenda_profe = [[None for _ in range(len(cfg.BLOQUES_SEC))] for _ in range(len(cfg.DIAS))]
        
        # Buscar en Primaria
        for g in cfg.GRUPOS_PRIMARIA:
            for d_idx in range(len(cfg.DIAS)):
                for b_idx in range(len(cfg.BLOQUES_PRIM)):
                    clase = self.horario.agenda_prim[g][d_idx][b_idx]
                    if clase and clase[1] == nombre_profe:
                        agenda_profe[d_idx][b_idx] = f"{clase[0]}\nGrado: {g}"

        # Buscar en Bachillerato
        for g in cfg.GRUPOS_BACHILLERATO:
            for d_idx in range(len(cfg.DIAS)):
                for b_idx in range(len(cfg.BLOQUES_SEC)):
                    clase = self.horario.agenda_sec[g][d_idx][b_idx]
                    if clase and clase[1] == nombre_profe:
                        agenda_profe[d_idx][b_idx] = f"{clase[0]}\nGrado: {g}"
        
        return agenda_profe

    def generar_resumen_carga(self, pdf):
            """Genera la primera página del PDF con el total de horas por docente"""
            # 1. Calcular carga por docente
            conteo_carga = {d.nombre: 0 for d in dm.BASE_DATOS["docentes"]}
            
            for asig in dm.BASE_DATOS["asignaciones"]:
                # Carga total = horas_materia * cantidad_de_grupos
                carga_total_materia = asig.horas * len(asig.grupos)
                conteo_carga[asig.docente.nombre] += carga_total_materia

            # 2. Preparar datos para la tabla
            datos_tabla = []
            for nombre, horas in conteo_carga.items():
                datos_tabla.append([nombre, f"{horas} horas"])
            
            # Ordenar por nombre
            datos_tabla.sort(key=lambda x: x[0])

            # 3. Dibujar en Matplotlib
            fig, ax = plt.subplots(figsize=(11, 8.5))
            ax.axis('tight')
            ax.axis('off')

            tabla = ax.table(
                cellText=datos_tabla,
                colLabels=["Nombre del Docente", "Carga Horaria Semanal Total"],
                loc='center',
                cellLoc='center'
            )

            # Estilo de la tabla de resumen
            tabla.auto_set_font_size(False)
            tabla.set_fontsize(12)
            tabla.scale(0.8, 2.5)
            
            # Colorear cabecera de resumen
            for (row, col), cell in tabla.get_celld().items():
                if row == 0:
                    cell.set_facecolor('#1a237e') # Azul oscuro institucional
                    cell.set_text_props(color='white', weight='bold')
                else:
                    cell.set_facecolor('#f5f5f5')

            ax.set_title("RESUMEN DE CARGA ACADÉMICA TOTAL", fontsize=18, weight='bold', pad=40)
            
            # Agregar una nota al pie
            fig.text(0.5, 0.1, f"Fecha de generación: {time.strftime('%d/%m/%Y')}", 
                    ha='center', fontsize=10, style='italic')

            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)        
        
        

    # En gui_resultados.py

    def generar_tabla_pdf(self, pdf, titulo, encabezados_filas, datos_celdas, color_base):
        """Helper para crear una página de tabla en el PDF"""
        fig, ax = plt.subplots(figsize=(11, 8.5)) 
        ax.axis('tight')
        ax.axis('off')
        
        tabla = ax.table(
            cellText=datos_celdas,
            rowLabels=encabezados_filas,
            colLabels=cfg.DIAS,
            loc='center',
            cellLoc='center'
        )
        
        tabla.auto_set_font_size(False)
        tabla.set_fontsize(8)
        tabla.scale(1, 2.0) # Ajusta altura de filas
        
        # Estilizar celdas
        for (row, col), cell in tabla.get_celld().items():
            if row == 0 or col == -1:
                # Cabeceras
                cell.set_facecolor('#455a64')
                cell.set_text_props(color='white', weight='bold')
            else:
                # Verificar si es una fila de DESCANSO
                # En datos_celdas, las filas de descanso tienen el texto "DESCANSO" en todas las columnas
                texto_celda = datos_celdas[row-1][col]
                
                if texto_celda == "DESCANSO":
                    cell.set_facecolor('#ffccbc') # Color Naranja Suave para descansos
                    cell.set_text_props(weight='bold', color='#bf360c')
                elif texto_celda != "":
                    cell.set_facecolor(color_base) # Color normal de clase

        ax.set_title(titulo, fontsize=16, weight='bold', pad=30)
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    def exportar_reporte_completo_pdf(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="Reporte_General_Horarios.pdf"
        )
        if not filename: return

        try:
            with PdfPages(filename) as pdf:
                # --- PÁGINA 1: RESUMEN DE CARGA ---
                self.generar_resumen_carga(pdf)

                # --- SECCIÓN: HORARIOS POR GRADO (CON DESCANSOS) ---
                for g in cfg.GRUPOS_PRIMARIA + cfg.GRUPOS_BACHILLERATO:
                    es_prim = g in cfg.GRUPOS_PRIMARIA
                    
                    # Usamos la lista COMPLETA de tiempos (True y False)
                    tiempos_completos = cfg.TIEMPOS_PRIM if es_prim else cfg.TIEMPOS_BACH
                    agenda_matriz = self.horario.agenda_prim[g] if es_prim else self.horario.agenda_sec[g]
                    
                    etiquetas_filas = []
                    celdas = []
                    
                    # Contador para saber en qué índice de bloque ACADÉMICO vamos
                    idx_bloque_academico = 0
                    
                    for (ini, fin, es_clase) in tiempos_completos:
                        etiqueta = f"{ini} - {fin}"
                        etiquetas_filas.append(etiqueta)
                        
                        fila = []
                        if es_clase:
                            # Es hora de clase: Buscamos en la matriz del algoritmo
                            for d_idx in range(len(cfg.DIAS)):
                                try:
                                    c = agenda_matriz[d_idx][idx_bloque_academico]
                                    fila.append(f"{c[0]}\n({c[1]})" if c else "")
                                except IndexError:
                                    fila.append("---")
                            idx_bloque_academico += 1
                        else:
                            # Es DESCANSO: Llenamos la fila con la palabra clave
                            fila = ["DESCANSO"] * len(cfg.DIAS)
                        
                        celdas.append(fila)
                    
                    self.generar_tabla_pdf(pdf, f"HORARIO - GRADO: {g}", etiquetas_filas, celdas, '#e3f2fd')

                # --- SECCIÓN: HORARIOS POR DOCENTE (CON DESCANSOS BACHILLERATO) ---
                profesores = [d.nombre for d in dm.BASE_DATOS["docentes"]]
                tiempos_profe = cfg.TIEMPOS_BACH # Usamos la referencia de Bachillerato para profes
                
                for p in profesores:
                    agenda_p = self.obtener_horario_docente(p) # Esta función devuelve solo bloques académicos
                    
                    etiquetas_filas = []
                    celdas = []
                    idx_bloque_academico = 0
                    
                    for (ini, fin, es_clase) in tiempos_profe:
                        etiqueta = f"{ini} - {fin}"
                        etiquetas_filas.append(etiqueta)
                        
                        fila = []
                        if es_clase:
                            for d_idx in range(len(cfg.DIAS)):
                                try:
                                    # agenda_p solo tiene datos en índices académicos
                                    val = agenda_p[d_idx][idx_bloque_academico]
                                    fila.append(val if val else "")
                                except IndexError:
                                    fila.append("")
                            idx_bloque_academico += 1
                        else:
                            fila = ["DESCANSO"] * len(cfg.DIAS)
                        
                        celdas.append(fila)
                    
                    self.generar_tabla_pdf(pdf, f"AGENDA DOCENTE: {p.upper()}", etiquetas_filas, celdas, '#f1f8e9')

            messagebox.showinfo("Éxito", "PDF generado con descansos incluidos.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Detalle del error: {e}")
            print(e) # Para ver el error en consola si falla

