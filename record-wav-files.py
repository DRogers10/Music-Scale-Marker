import wave
import pyaudio
import keyboard
import numpy
import os
pa = pyaudio.PyAudio()
frames = []
filename = input("Enter file name: ") + ".wav"
print("Press q to exit")
FORMAT = pyaudio.paInt16
BANDWIDTH = 1
SAMPLING_RATE = 48000
NUM_SAMPLES=2048
_stream = pa.open(format=pyaudio.paInt16, channels=1, rate=48000, input=True, frames_per_buffer=2048, output=True)
#numpy.frombuffer(_stream.read(NUM_SAMPLES), dtype=numpy.short)[-NUM_SAMPLES:] / 32768.0
while True:
    #data = _stream.read(2048)
    data = numpy.frombuffer(_stream.read(NUM_SAMPLES), dtype=numpy.short)[-NUM_SAMPLES:] # Take audio input
    frames.append(data)
    try:
        if keyboard.is_pressed("q"):
            break
    except Exception:
        pass
print("Finished recording.")
# stop and close stream
_stream.stop_stream()
_stream.close()
# terminate pyaudio object
pa.terminate()
# save audio file
# open the file in 'write bytes' mode

wf = wave.open(filename, 'wb')
# set the channels
wf.setnchannels(1)
# set the sample format
wf.setsampwidth(pa.get_sample_size(FORMAT))
# set the sample rate
wf.setframerate(48000)
# write the frames as bytes
wf.writeframes(b"".join(frames))
# close the file
wf.close()
