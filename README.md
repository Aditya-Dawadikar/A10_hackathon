# A10 Hackathon Project

### Installation
#### Backend

Create a `.env` file in the `backend` folder.

```
GOOGLE_API_KEY=YOUR_GOOGLE_GEMINI_API_KEY
```

Installation and Run
```
cd backend
python -m venv venv

.\venv\Scripts\activate # for windows users
source venv/bin/activate # for linux users

pip install -r requirements.txt
uvicorn main:app --host=0.0.0.0 --port=8000 --reload

```

