from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = ['mido','rtmidi','obswebsocket','confuse'], excludes = [], include_files=['X-TOUCH-MINI.png'])

import sys
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('obs-midi-controller.py', base=base, targetName = 'obs-midi-controller')
]

setup(name='obs-midi-controller',
      version = '1.0',
      description = 'Python module to read from midi controllers and control obs studio',
      options = dict(build_exe = buildOptions),
      executables = executables
      )
