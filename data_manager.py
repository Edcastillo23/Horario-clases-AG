# data_manager.py

class Docente:
    def __init__(self, nombre, grados_habilitados):
        self.nombre = nombre
        self.grados_habilitados = grados_habilitados

class Asignacion:
    def __init__(self, materia, docente, horas, grupos_asignados):
        self.materia = materia
        self.docente = docente # Objeto Docente
        self.horas = horas
        self.grupos = grupos_asignados # Lista de strings ej: ['6°', '7°']

# Variable global para almacenar datos ingresados en la GUI
BASE_DATOS = {
    "docentes": [],
    "asignaciones": []
}