import tkinter as tk
from gui import AplicacionHorario
import sys
import datos_prueba

def main():
    datos_prueba.cargar_datos_complejos()
    
    try:
        # 1. Creamos la instancia de la aplicación principal (Tkinter)
        app = AplicacionHorario()
        
        # 2. Iniciamos el loop principal
        # Este comando mantiene la ventana abierta y escuchando eventos
        app.mainloop()
        
    except Exception as e:
        print(f"Error fatal al iniciar la aplicación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()