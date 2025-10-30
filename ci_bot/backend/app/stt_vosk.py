from vosk import Model, KaldiRecognizer
import wave, json, os

model_path = os.path.abspath("models/vosk-model-small-en-us-0.15")
model = Model(model_path)

def transcribe_wav(filepath):
    wf = wave.open(filepath, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    result = ""
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result += rec.Result()
    result += rec.FinalResult()
    return json.loads(result).get("text", "")
