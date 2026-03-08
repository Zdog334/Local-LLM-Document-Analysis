# Local AI Document Analysis

A local, privacy-focused application for analyzing and comparing documents using Large Language Models (LLMs) via Ollama.

## 1. Prerequisites: Ollama

This application relies on **Ollama** to run the AI models locally.

1.  **Download & Install**: Go to [ollama.com](https://ollama.com) and download the installer for your system.
2.  **Pull a Model**: Open your terminal/command prompt and run:
    ```bash
    ollama pull llama3
    ```
    *(You can replace `llama3` with `mistral`, `gemma`, etc.)*
3.  **Ensure it's running**: Make sure the Ollama app is running in the background (check your system tray).

## 2. Installation (For Developers/Source)

If you want to run the code directly or build the executable yourself:

1.  **Install Python**: Ensure Python (3.10 or newer) is installed.
2.  **Install Dependencies**:
    Open a terminal in the project folder and run:
    ```bash
    pip install -r requirements.txt
    ```

## 3. How to Run

### Option A: Using the Executable (.exe)
If you have built the application (or downloaded a release):
1.  Navigate to the `dist` folder.
2.  Double-click **`LocalAI_Studio.exe`**.
3.  *Note: The first run might take a moment to download the embedding model.*

**To build the .exe yourself:**
Run the build script provided in the repository:
```bash
python build_app.py
```

### Option B: Running from Source (Script/.bat)
To run the application directly via Python (or a `.bat` file that executes this command):
```bash
python ui.py
```

## 4. How it Works

This application uses **RAG (Retrieval-Augmented Generation)** to let you chat with your documents without sending data to the cloud.

-   **Library**:
    -   **Import**: Select PDF or Text files. They are copied to `documents/` and processed into vector embeddings (stored in `vector_store/`).
    -   **Manage**: Delete or search through your imported documents.
-   **Analysis**:
    -   Select a document in the Library to open it.
    -   **Viewer**: Read the PDF or text file on the left.
    -   **Chat**: Ask questions specific to that document. The AI cites its sources (page and score).
-   **Compare**:
    -   Select multiple documents in the Library (Ctrl+Click) and click "Compare Selected".
    -   Ask questions that require synthesizing information from all selected files.
-   **Settings**:
    -   Change the active Ollama model.
    -   Force the AI to respond in a specific language (e.g., Spanish, French).