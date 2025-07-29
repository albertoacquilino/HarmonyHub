<div align="center"> <img src="https://gist.github.com/user-attachments/assets/495d85e3-287f-499a-a1b3-40a1636c278b" alt="Centered Image" width="600"> </div>

## GSoC 2025 Report

### Project Title: HarmonyHub: Using Generative AI for Adaptive Learning in Music

**Organization**: INCF

**Contributor**: Priyanshu Tiwari

**Mentors**: Alberto Acquilino, Mirko D'Andrea, Keerthi Reddy Kambham, Thrun, Oscar

**Hugging Face Repo**: [Music LLM](https://huggingface.co/spaces/SHIKARICHACHA/adaptive-music-exercise-generator)

---

## Project Overview

**HarmonyHub** addresses the need for personalized and adaptive music learning by leveraging Generative AI to dynamically create music exercises tailored to individual learners. It empowers educators through a no-code, interactive platform where exercises are generated based on parameters like difficulty level, instrument, time signature, and rhythm complexity — all processed through the **Mistral LLM API**.

This tool is especially useful for students at different learning stages and offers exports in MIDI, MP3, and JSON formats. With a Gradio-based web interface and integrated AI assistant, HarmonyHub is designed to be highly accessible for both teachers and students.

<img width="1173" height="643" alt="Screenshot 2025-07-08 at 10 43 43 PM" src="https://gist.github.com/user-attachments/assets/e47a7bf1-e51b-4e79-8c95-9bc0aaf5be3b" />

---

## What I Have Accomplished So Far (By Midterm)

| Milestone | Description                                                                                                                                                                                 |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Week 1–2  | Completed literature review on music theory and generative music systems. Designed high-level architecture and selected required tools (Mistral API, Gradio, FluidSynth).                   |
| Week 3–4  | Integrated Mistral API to generate rhythmically and melodically consistent music exercises. Built strict duration scaling system (matching exact number of measures).                       |
| Week 5–6  | Created multi-format output support (MIDI, MP3, JSON). Enabled MP3 synthesis using SoundFont and FluidSynth. Added automatic package installation and SoundFont fetching.                   |
| Week 7    | Developed and launched a Gradio-based web interface. Enabled user inputs for instrument, time signature, key, difficulty, and rhythmic pattern. Integrated AI assistant for theory queries. |

---

## Features Implemented

* Strict Measure-Length Enforcement (No timing drift)
* Multi-Instrument Support (Piano, Flute, Violin, Trumpet, Clarinet)
* Beginner, Intermediate, and Advanced Modes
* Export in MIDI / MP3 / JSON Formats
* Interactive Gradio Web UI (no coding required)
* AI Assistant Chat (for practice help & music theory)
* Automatic Dependency & SoundFont Handling
* Fallback Logic on API Errors

---

## Deliverables So Far

* Working GitHub Repository
* MP3/MIDI/JSON Output Sample Files
* Gradio UI Demo
* User Guide & Documentation (Initial)
* Screenshots (stored in `/docs/screenshots/`)
* Midterm Blog Draft (to be finalized before submission)

---
## 📸 Screenshots & Images

Here are selected images showcasing the current progress and functionality of **HarmonyHub**:

### 1. 🖥️ Gradio Web Interface – Home Panel
<img width="1493" height="704" alt="image" src="https://gist.github.com/user-attachments/assets/aa9b02f8-4f35-48f7-8699-2b3b38dca17c" />

---

### 2. 🎛️ Parameter-Based Exercise Generation
<img width="1483" height="682" alt="image" src="https://gist.github.com/user-attachments/assets/27c27c7d-3053-4da0-a189-f4e3085acf05" />
<div style="display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap;"> <img src="https://gist.github.com/user-attachments/assets/0ab56bf5-7d7b-4151-a4db-9288fe50615d" alt="Left Image" width="48%"> <img src="https://gist.github.com/user-attachments/assets/ed4aa441-5d39-4be3-b858-520e1af35e8e" alt="Right Image" width="48%"> </div>


---

### 3. 💬 AI Chat Assistant Interface

<img width="974" height="628" alt="image" src="https://gist.github.com/user-attachments/assets/844d8ed4-0772-46a2-ac18-3d66883e1cae" />

---

### 4. 🎼 JSON Output Structure (Exercise Preview)

<img width="1466" height="682" alt="image" src="https://gist.github.com/user-attachments/assets/27801d11-a8b0-4682-b2b3-f5112c6243ac" />

---

### 5. 🎹 MIDI File Imported in DAW

<img width="1521" height="591" alt="image" src="https://gist.github.com/user-attachments/assets/b958f0b3-8a18-45cd-8917-326b11f160cc" />

---

## Challenges Faced

* Managing time drift and scaling note durations while preserving rhythm quality
* Ensuring MIDI conversion preserved timing and instrument assignment correctly
* API key security (temporarily hardcoded — need secure handling soon)
* SoundFont compatibility and dependency management across OS environments (macOS/Linux)

---

## What’s Left to Do (For Final Evaluation)

| Task                                                               | Description |
| ------------------------------------------------------------------ | ----------- |
| Add Visual Sheet Music Output (Music21/Lilypond integration)       |             |
| Support for Polyphonic MIDI (Chords) and advanced dynamics         |             |
| Implement Error Logging & More Descriptive Error Messages          |             |
| Enable Real-Time Exercise Editing via Chat                         |             |
| Add more instruments (Saxophone, Cello, Guitar, etc.)              |             |
| Improve API Key Handling and explore offline mode using local LLM  |             |
| Add User Progress Tracking and Saved Exercises (Phase 2 post-GSoC) |             |

---

## Acknowledgments

I’m deeply grateful to my mentors Alberto Acquilino, Mirko D'Andrea, Keerthi Reddy Kambham, Thrun, and Oscar for their guidance and encouragement. Their support has helped me translate abstract AI concepts into a functioning tool that serves real pedagogical value.

---

## Final Note

HarmonyHub has the potential to democratize adaptive music learning by making exercise creation accessible, intelligent, and personalized. The midterm phase has solidified the foundation of this tool, and I look forward to building the advanced features and polishing the platform by the final evaluation.



