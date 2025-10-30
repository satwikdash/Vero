import av
import numpy as np
import soundfile as sf

def webm_to_wav(input_path, output_path):
    container = av.open(input_path)
    audio_stream = next(s for s in container.streams if s.type=='audio')
    frames = []
    for packet in container.demux(audio_stream):
        for frame in packet.decode():
            pcm = frame.to_ndarray()
            if pcm.ndim > 1:
                pcm = pcm.mean(axis=0)  # stereo -> mono
            frames.append(pcm.astype(np.float32)/32768.0)
    audio = np.concatenate(frames)
    sf.write(output_path, audio, 16000)
    return output_path
