from fastapi import FastAPI, UploadFile
from .stt_vosk import transcribe_wav
from .nlp_pipeline import analyze_text

app = FastAPI()

@app.post("/upload_audio/")
async def upload_audio(file: UploadFile):
    with open("temp.wav", "wb") as f:
        f.write(await file.read())

    transcript = transcribe_wav("temp.wav")
    insights = analyze_text(transcript)

    return {"transcript": transcript, "insights": insights}
