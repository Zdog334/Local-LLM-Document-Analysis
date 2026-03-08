import PyInstaller.__main__
import os

# Configuración para crear el ejecutable
args = [
    'ui.py',                        # Tu script principal
    '--name=LocalAI_Studio',        # Nombre del ejecutable resultante
    '--windowed',                   # Modo GUI: no muestra la consola negra de fondo
    '--onefile',                    # Empaqueta todo en un solo archivo .exe
    '--clean',                      # Limpia caché de construcciones previas
    '--noconfirm',                  # No pide confirmación para sobrescribir
    
    # Recolectar dependencias complejas (necesario para IA/Ciencia de datos)
    '--collect-all=sentence_transformers',
    '--collect-all=torch',
    '--collect-all=faiss',
    '--collect-all=pypdf',
    
    # Si tienes un icono para la app o imágenes como 'pdf.png', descomenta y ajusta:
    # '--add-data=pdf.png;.', 
    # '--icon=app_icon.ico',
]

print("🔨 Iniciando construcción del ejecutable... Esto puede tardar unos minutos.")

PyInstaller.__main__.run(args)

print("✅ Construcción finalizada. Busca tu ejecutable en la carpeta 'dist'.")