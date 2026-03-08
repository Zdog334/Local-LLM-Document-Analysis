# Local AI Document Analysis

Una aplicación local centrada en la privacidad para analizar y comparar documentos utilizando Grandes Modelos de Lenguaje (LLMs) a través de Ollama.

## 1. Requisitos Previos: Ollama

Esta aplicación depende de **Ollama** para ejecutar los modelos de IA localmente.

1.  **Descargar e Instalar**: Ve a ollama.com y descarga el instalador para tu sistema.
2.  **Descargar un Modelo**: Abre tu terminal o símbolo del sistema y ejecuta:
    ```bash
    ollama pull llama3
    ```
    *(Puedes reemplazar `llama3` con `mistral`, `gemma`, etc.)*
3.  **Verificar ejecución**: Asegúrate de que la aplicación Ollama se esté ejecutando en segundo plano (en la bandeja del sistema).

## 2. Instalación (Código Fuente)

Si deseas ejecutar el código directamente o construir el ejecutable tú mismo:

1.  **Instalar Python**: Asegúrate de tener Python (3.10 o superior).
2.  **Instalar Dependencias**:
    Abre una terminal en la carpeta del proyecto y ejecuta:
    ```bash
    pip install -r requirements.txt
    ```

## 3. Ejecución del Programa

### Opción A: Usando el Ejecutable (.exe)
Si has generado la aplicación (o descargado una versión):
1.  Ve a la carpeta `dist`.
2.  Haz doble clic en **`LocalAI_Studio.exe`**.
3.  *Nota: La primera ejecución puede tardar un momento mientras se descarga el modelo de embeddings.*

**Para generar el .exe tú mismo:**
Ejecuta el script de construcción incluido:
```bash
python build_app.py
```

### Opción B: Ejecutar desde Código (Script/.bat)
Para correr la aplicación directamente con Python (o mediante un archivo `.bat` que ejecute este comando):
```bash
python ui.py
```

## 4. Funcionamiento

Esta aplicación utiliza **RAG (Generación Aumentada por Recuperación)** para permitirte chatear con tus documentos sin enviar datos a la nube.

-   **Biblioteca (Library)**:
    -   **Importar**: Selecciona archivos PDF o de texto. Se copian a la carpeta `documents/` y se procesan en vectores (guardados en `vector_store/`).
    -   **Gestionar**: Elimina o busca entre tus documentos importados.
-   **Análisis (Analysis)**:
    -   Selecciona un documento en la Biblioteca para abrirlo.
    -   **Visor**: Lee el PDF o texto a la izquierda.
    -   **Chat**: Haz preguntas específicas sobre ese documento. La IA citará las fuentes (página y puntuación).
-   **Comparar (Compare)**:
    -   Selecciona múltiples documentos en la Biblioteca (Ctrl+Clic) y haz clic en "Compare Selected".
    -   Haz preguntas que requieran sintetizar información de todos los archivos seleccionados.
-   **Configuración (Settings)**:
    -   Cambia el modelo de Ollama activo.
    -   Fuerza a la IA a responder en un idioma específico (ej. Español, Inglés).