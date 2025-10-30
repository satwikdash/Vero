# recorder/server.py
import asyncio
import json
import os
import uuid
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder
from pathlib import Path
from transcribe import transcribe_and_analyze
import aiohttp_cors


ROOT = Path(__file__).parent
RECORDINGS_DIR = ROOT / "recordings"
os.makedirs(RECORDINGS_DIR, exist_ok=True)

pcs = set()

async def handle_offer(request):
    """
    POST /offer
    body: { "sdp": "...", "type": "offer" }
    returns: { "sdp": "...", "type": "answer", "recording_id": "<id>" }
    """
    params = await request.json()
    offer_sdp = params.get("sdp")
    offer_type = params.get("type", "offer")
    if not offer_sdp:
        return web.Response(status=400, text="Missing sdp")

    recording_id = str(uuid.uuid4())
    out_wav = str(RECORDINGS_DIR / f"{recording_id}.wav")

    pc = RTCPeerConnection()
    pcs.add(pc)
    recorder = MediaRecorder(out_wav)

    @pc.on("track")
    def on_track(track):
        print("Track received:", track.kind)
        if track.kind == "audio":
            recorder.addTrack(track)

        @track.on("ended")
        async def on_ended():
            print("Track ended")
    # set remote
    await pc.setRemoteDescription(RTCSessionDescription(sdp=offer_sdp, type=offer_type))
    # create answer
    await pc.setLocalDescription(await pc.createAnswer())
    # start recorder
    await recorder.start()

    # we will stop recorder when peer connection is closed (in background)
    async def monitor():
        await pc._connection_state_complete  # wait until closed
        try:
            await recorder.stop()
        except Exception as e:
            print("Recorder stop error:", e)
        # transcribe and analyze
        print("Starting transcription for", out_wav)
        try:
            analysis = transcribe_and_analyze(out_wav)
            # write result JSON next to wav
            with open(str(RECORDINGS_DIR / f"{recording_id}.json"), "w", encoding="utf-8") as fh:
                json.dump(analysis, fh, ensure_ascii=False, indent=2)
            print("Transcription complete for", recording_id)
        except Exception as exc:
            print("Transcription failed:", exc)

        # cleanup pc
        if pc in pcs:
            pcs.remove(pc)
        await pc.close()

    asyncio.ensure_future(monitor())

    answer = {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type, "recording_id": recording_id}
    return web.json_response(answer)

async def on_shutdown(app):
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

def main():
    app = web.Application()
    app.router.add_post("/offer", handle_offer)
    app.on_shutdown.append(on_shutdown)
        # Enable CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    for route in list(app.router.routes()):
        cors.add(route)

    web.run_app(app, port=8080)

if __name__ == "__main__":
    main()
