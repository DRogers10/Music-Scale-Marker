import numpy
import time
import pyaudio
import wave
import scipy
import math
import collections
import matplotlib.pyplot as plt
import pytest
from scipy.io import wavfile
import os

os.chdir("Regression_Testing")

SENSITIVITY = 0.1
BANDWIDTH = 1
SAMPLING_RATE = 48000
NUM_SAMPLES=2048
RELATIVE_FREQ=440
MAX_FREQUENCY = -20
MIN_FREQUENCY = 20
ALTERED_SIGNAL_IGNORE = 7
FLAG = 999999
REPEATS = 3 # Number of rolling averages to produce note
pa = pyaudio.PyAudio()
_stream = pa.open(format=pyaudio.paInt16, channels=1, rate=SAMPLING_RATE, input=True, frames_per_buffer=NUM_SAMPLES)
pa.terminate()
count = 0
lst = []
z = []
intensity = 0
linear_frequency = 0
note = ""
differences = []
scale = []
first_sector = ""
last_sector = ""
error = False
data = []
samplerate = 0
sampling = 0
scales = {
  0: "B",
  11: "C",
  10: "C#",
  9: "D",
  8: "Eb",
  7: "E",
  6: "F",
  5: "F#",
  4: "G",
  3: "G#",
  2: "A",
  1: "Bb"
}
fixed = {
  "2 2 1 2 2 2 1": "Major",
  "4 3 5": "Major Arpeggio",
  "2 1 2 2 1 3 1": "Minor Harmonic",
  "3 4 5": "Minor Arpeggio",
  "2 1 2 2 2 2 1 2 2 1 2 2 1 2": "Minor Melodic",
  ("1 " * 12)[:-1]: "Chromatic"
}

def sample():
  #audio_data = numpy.frombuffer(_stream.read(NUM_SAMPLES), dtype=numpy.short)[-NUM_SAMPLES:] / 32768.0 # Take audio input
  audio_data = numpy.array(data[sampling-NUM_SAMPLES:sampling]) # Take audio input
  w = numpy.hamming(2048) # Window Input
  intensity = abs(w*numpy.fft.fft(audio_data))
  return intensity

def note_frequency():
  maximum = list(intensity).index(max(intensity[1:]))
  y0 = numpy.log(intensity[maximum - 1])
  y1 = numpy.log(intensity[maximum])
  y2 = numpy.log(intensity[maximum + 1])
  estimated_maximum_frequency = 0.5 * ((y0 - y2) / (y0 - (2 * y1) + y2)) # Quadratic interpolation of max frequency
  #estimated_maximum_magnitude = y1 - (0.25 * (y0 - y2) * estimated_maximum_frequency) # Quadratic interpolation of max amplitude
  frequency = (maximum + estimated_maximum_frequency)*SAMPLING_RATE/NUM_SAMPLES
  if frequency == 0 or numpy.isnan(frequency):
    return FLAG
  try:
    linear_frequency = (1200 * numpy.log2(RELATIVE_FREQ/frequency)) / 100 # Linearize frequency to semitone values for processing
  except Exception:
    return FLAG
  return linear_frequency

def filtered_scale_graph():
  plt.plot(z)
  plt.title("Final filtered scale")
  plt.xlabel("Sample number")
  plt.ylabel("Frequency (in semitones)")
  plt.show()

def unfiltered_scale_graph():
  plt.plot(lst)
  plt.title("With fluctuations")
  plt.xlabel("Sample number")
  plt.ylabel("Frequency (in semitones)")
  plt.show()

def calc_scale():
  scale = [80070000]
  for i in range(len(z) - (REPEATS - 1)):
    if len(set(z[i:i + (REPEATS - 1)])) == 1 and z[i] != scale[-1]: # Add unique note if recorded REPEATS times
      scale.append(z[i])
  scale = scale[1:]
  print(scale) # List of notes (in numbers)
  note = scales[scale[0] % 12] # Find key of scale (first note)
  differences = [scale[i] - scale[i + 1] for i in range(0, len(scale) - 1)]
  return [note, differences, scale]

def minor_melodic(differences, first_sector, last_sector):
  i = ["2 1 2 2 2 2 1", "2 2 1 2 2 1 2"] #Up, down
  if len(first_sector) % len(i[0]) != 0 or len(last_sector) % len(i[1]) != 0:
    #print("sectors not divisble")
    return False
  for j in [first_sector[octave * len(i[0]):(octave + 1) * len(i[0])] for octave in range((len(first_sector) // len(i[0])) - 1)]:
    if j != i[0]:
      #print("first sector")
      return False
  for j in [last_sector[octave * len(i[1]):(octave + 1) * len(i[1])] for octave in range((len(last_sector) // len(i[1])) - 1)]:
    j = [each * -1 for each in j]
    if j != i[1]:
      #print("Second sector")
      return False
  return True

def correct():
  global differences
  global z
  #return f'You played {note} {fixed[" ".join(list(map(str, differences)))]}' # Correct Scale (then outputted)
  return f'{note} {fixed[" ".join(list(map(str, differences)))]}' # Correct Scale (then outputted)
  differences = []
  z = []

def incorrect():
  global differences
  global z
  return "Incorrect"
  differences = []
  z = []

def is_correct(fixed):
  global error
  global differences
  error = True
  for i in fixed.keys():
    i = list(map(int, i.split()))
    if len(differences) % len(i) == 0:
      for j in range(0, len(differences), len(i)):
        if differences[j:j + len(i)] != i and [negative * -1 for negative in differences[j:j + len(i)][::-1]] != i: # Check what scale type (major arpeggio, minor, etc...)
          break
        elif j == len(differences) - len(i):
          differences = differences[0:len(i)]
          return correct()
          error = False
          break
    if error == False:
      break

def invalid_notes(frequency):
  #print(frequency)
  optimise = round(frequency)
  if optimise == 17 or optimise == 18:
    if frequency <= 17.24:
      return 17.0
    else:
      return 18.0
  if optimise == 16 or optimise == 15:
    if frequency <= 15.3:
      return 15.0
    else:
      return 16.0
  if optimise == 10 or optimise == 9:
    if frequency <= 9.3:
      return 9.0
    else:
      return 10.0
  if optimise == -12 or optimise == -18:
    return 16.0
  if optimise == -6:
    return 13.0
  if optimise == -9:
    return 10.0
  return frequency

def update_scale():
  global lst
  global z
  global count
  count = 0 # Reset "gap" count between samples
  lst.append(linear_frequency)
  if len(lst) <= 2:
    pass
  elif abs(lst[-1] - lst[-2]) < 0.5:
    increased = round(lst[-1])
    if increased == 18 or increased == 17 or increased == 16 or increased == 15:
      lst[-1] = invalid_notes(lst[-1])
    z.append((numpy.convolve(lst[-3:], numpy.ones(3), 'valid') / 3)[0])
  elif len(lst) == 3:
    lst = [lst[-1]]
  elif abs(lst[-1] - lst[-2]) > ALTERED_SIGNAL_IGNORE:
    lst[-1] = invalid_notes(lst[-1])
    if abs(lst[-1] - lst[-2]) < ALTERED_SIGNAL_IGNORE:
      pass
    else:
      lst.pop(-1)


def main(filename):
  global _stream
  global count
  global lst
  global z
  global scales
  global fixed
  global intensity
  global linear_frequency
  global note
  global differences
  global scale
  global first_sector
  global last_sector
  global error
  global sampling
  global data
  pa = pyaudio.PyAudio()
  _stream = pa.open(format=pyaudio.paInt16, channels=1, rate=SAMPLING_RATE, input=True, frames_per_buffer=NUM_SAMPLES)
  count = 0
  lst = []
  z = []
  intensity = 0
  linear_frequency = 0
  note = ""
  differences = []
  scale = []
  first_sector = ""
  last_sector = ""
  error = False


  try:
    samplerate, data = wavfile.read(filename)
    print(data, samplerate)
    for sampling in range(NUM_SAMPLES, len(data), NUM_SAMPLES):
      intensity = sample()
      #print(intensity)
      #print(max(intensity))
      linear_frequency = note_frequency()
      #print(linear_frequency)
      if linear_frequency == FLAG: # FLAG for invalid samples
        continue
      print(round(linear_frequency))


      if linear_frequency < MAX_FREQUENCY or linear_frequency > MIN_FREQUENCY: # Outside of frequency range (background noise)
        count += 1
        if count <= 15 or len(z) < 1: # If gap not long enough or no scale played yet
          #print(count, len(z))
          pass
        else: # Scale was played and has ended
          error = False
          z = list(map(round, z))
          if len(z) <= REPEATS - 1 or len(z) == 1:
            z = []
            count = 0
            continue


          
          note, differences, scale = calc_scale()
          if len(differences) <= 2:
            return incorrect()
          else:
            first_sector = scale[:(len(scale) // 2) + 1]
            last_sector = scale[(len(scale) // 2):]
            last_sector = last_sector[::-1]
            if first_sector != last_sector:
              if minor_melodic(differences, first_sector, last_sector):
                differences = list(map(int, list(fixed.keys())[4].split())) # Set differences to give minor melodic
                return correct()
              else:
                return incorrect()
            else:
              result = is_correct(fixed)
              if result != None:
                return result
              if error == False:
                continue
          if error:
            return incorrect()
          else:
            return correct()
      if linear_frequency < MAX_FREQUENCY or linear_frequency >= MIN_FREQUENCY or numpy.isnan(linear_frequency):
        continue

      update_scale()
  # except Exception as e:
  #   print(e)

  finally:
    pa.terminate()

def test_c_major_arpeggio():
  assert main() == "C Major Arpeggio"
def test_c_major():
  assert main() == "C Major"
def test_incorrect():
  assert main() == "Incorrect"

print(main("updated.wav"))