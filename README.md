# HairHQ

HairHQ is a web application that provides hair information and styling assistance using a frontend and backend setup.

## Project Structure
frontend/ – user interface (HTML/CSS/JS)
backend/ – FastAPI backend

markdown
Copy code

## Run Locally

### Backend Setup
1. Open a terminal in the project root.
2. Navigate to the backend folder:
```bash
cd backend
(Recommended) Create and activate a virtual environment:

bash
Copy code
python -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Create a .env file in the backend folder and add your API key:

ini
Copy code
OPENAI_API_KEY=your_api_key_here
Run the backend server:

bash
Copy code
uvicorn main:app --reload
The API will run at:

cpp
Copy code
http://127.0.0.1:8000
Frontend Setup
Open the frontend folder using VS Code Live Server (recommended) or another local web server.

Notes
This repository does not include API keys.

.env files should never be committed to GitHub.

Virtual environment folders (venv/) are intentionally excluded.

yaml
Copy code
