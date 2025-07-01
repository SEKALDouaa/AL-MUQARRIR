# AL-MUQARRIR

**AL-MUQARRIR** is an AI-powered web application for real-time meeting transcription, speaker diarization, semantic analysis, and automated generation/export of meeting minutes (PV) and analyses in Arabic and other languages.

---

## 🏗️ Project Structure

```
AL-MUQARRIR/
├── frontend/   # Angular web application (user interface)
├── backend/    # Flask API (Data management, export, user auth)
├── backend_generative-AI-for-chat-transcription/ # AI models & audio processing
└── README.md   # This file
```

---

## 🚀 Getting Started

### 1. Frontend (Angular)

```bash
cd frontend
npm install
ng serve
```
Visit [http://localhost:4200](http://localhost:4200)

### 2. Backend (Flask)

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # or source venv/bin/activate on Linux/Mac
pip install -r requirements.txt
python run.py
```
API available at [http://localhost:5000](http://localhost:5000)

### 3. Generative AI Backend (Audio Processing)

```bash
cd backend_generative-AI-for-chat-transcription
pip install -r requirements.txt
python run.py
```
This service handles audio diarization, transcription, and refinement.

---

## 🧠 Features

- Real-time & batch meeting transcription (Arabic, French, English, Darija, etc.)
- Speaker diarization (identifies who spoke when)
- Semantic analysis (themes, problems, opportunities, sentiment)
- Automated PV (procès-verbal) & analysis generation
- Export to PDF (via PDFShift API) and DOCX
- User management & authentication (JWT)
- Modern, responsive Angular frontend
- Multilingual & RTL support

---

## 📦 Main Folders

- `frontend/`  
  Angular app: user authentication, dashboard, transcription, PV/analysis management, export, documentation.

- `backend/`  
  Flask API: user management, meeting CRUD, export endpoints, PDF/DOCX generation, database (SQLite).

- `backend_generative-AI-for-chat-transcription/`  
  AI pipelines: audio preprocessing, diarization (pyannote.audio), transcription (Whisper), text refinement (Gemini), API endpoints for audio processing.

- `static/`  
  Fonts (e.g., Amiri for Arabic PDF export).

---

## 🛠️ Technologies

- **Frontend:** Angular, Bootstrap, FontAwesome
- **Backend:** Flask, Flask-JWT-Extended, Flask-SQLAlchemy, Flask-RESTful, python-docx, requests
- **AI/NLP:** Whisper, pyannote.audio, Gemini, GPT, scikit-learn, spaCy
- **PDF Export:** PDFShift API (HTML to PDF, Arabic/RTL support)
- **Database:** SQLite (dev), PostgreSQL/MySQL (prod-ready)
- **Other:** Ngrok (API tunneling), Jupyter Notebook (prototyping), Git, VS Code

---

## 📄 Usage Overview

1. **Login/Register** via the Angular frontend.
2. **Create a new transcription** (upload audio or record in real-time).
3. **Assign speakers** and edit the transcription if needed.
4. **Generate PV and analysis** automatically.
5. **Export** PV/analysis as PDF or DOCX.
6. **Browse, search, and manage** meetings, analyses, and users.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## 📚 Documentation

- See the in-app documentation page for user guidance and feature overview.
- For developers:  
  - `frontend/README.md` for Angular commands  
  - `backend/requirements.txt` and `backend_generative-AI-for-chat-transcription/requirements.txt` for dependencies

---

## 📧 Contact

For questions or support, open an issue or contact the maintainers.
