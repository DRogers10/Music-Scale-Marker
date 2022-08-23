## Music-Scale-Marker

A project to automatically mark music scales using just python.

This project can be divided into 2 components:
'music-scale-marker.py': A real time implementation of the music scale marker
'recorded-scale-debugger.py': Similar code used to work on a set of recorded scales, allowing me optimise some constants and keep a record of erroneous scales

The code uploaded here is an initial attempt at the problem (it takes the strongest frequency from the fft transformation).
However, this method is not 100% accurate. I hope to implement the project using the Harmonic Product Spectrum (HPS) algorithm as an addition to this project.
