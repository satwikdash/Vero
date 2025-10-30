# client/hybrid_bot.py
import asyncio
import aiohttp
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from aiortc.contrib.media import MediaPlayer

BACKEND_URL = "http://localhost:8080/offer"

async def main():
    pc = RTCPeerConnection()
    # Capture local microphone or any source
    player = MediaPlayer("default", format="dshow")  # Windows mic input
    pc.addTrack(player.audio)

    # Create local offer
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    # Send offer to backend recorder
    async with aiohttp.ClientSession() as session:
        async with session.post(BACKEND_URL, json={
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }) as resp:
            answer = await resp.json()
            print("Received answer:", answer["recording_id"])
            await pc.setRemoteDescription(RTCSessionDescription(
                sdp=answer["sdp"], type=answer["type"]
            ))

    # Keep connection alive
    await asyncio.sleep(10)  # Record for 10 seconds (for test)
    await pc.close()

asyncio.run(main())
