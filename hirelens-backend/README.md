# HireLens Backend

The backend server for the HireLens application, providing APIs for interview recording, analysis, and reporting.

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- MongoDB (running on default port 27017)
- FFmpeg (required for audio processing)

### Installing FFmpeg

#### macOS
```bash
brew install ffmpeg
```

#### Windows
1. Download FFmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extract the files to a folder (e.g., `C:\ffmpeg`)
3. Add the `bin` folder to your system's PATH environment variable

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

### Setting Up Python Environment

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. Install dependencies:
```bash
pip install -r requirements.txt
```

Note: If you encounter issues installing PyAudio, you might need to install portaudio first:
- macOS: `brew install portaudio`
- Ubuntu/Debian: `sudo apt-get install portaudio19-dev`
- Windows: PyAudio might require Microsoft Visual C++ Build Tools

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# API Keys
OPENROUTER_API_KEY=your_openrouter_api_key

# Flask Configuration
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret_key

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
```

## Running the Server

To start the server:

```bash
python run.py
```

The server will be available at http://localhost:5000

## API Endpoints

- `POST /api/interview/start`: Start a new interview session
- `POST /api/interview/record`: Record frames during an interview
- `POST /api/interview/process-audio`: Process audio recordings and return transcriptions
- `POST /api/interview/stop`: Stop and process an interview
- `GET /api/interview/questions`: Get random interview questions
- `GET /api/interview/history`: Get interview history
- `GET /api/interview/results`: Get interview results 