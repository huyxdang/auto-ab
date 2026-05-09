# auto-ab

Autonomous website optimization demo. The app analyzes visitor behavior signals, diagnoses conversion friction, generates an improved website variant, and shows the next A/B optimization loop.

## Project Structure

- `frontend/` - React + Vite demo UI.
- `backend/` - local AI generation backend.
- `website2/` - target website used by the demo analysis.

## Local Frontend

```powershell
cd frontend
npm install
npm run dev
```

Production preview:

```powershell
cd frontend
npm run build
npm run preview -- --host 127.0.0.1 --port 4173
```

Open:

```text
http://127.0.0.1:4173/auto-ab/
```

## Backend

```powershell
cd backend
pip install -r requirements.txt
python auto_ab_demo.py
```

Keep API keys in `.env`. Do not commit secrets.

## Demo Flow

1. Paste a URL and choose an analytics source.
2. Simulate visitor behavior from the target page structure.
3. Send behavior signals into AI analysis.
4. Show friction diagnosis before recommendations.
5. Compare original website vs generated variant.
6. Continue the optimization loop toward A/B testing.
