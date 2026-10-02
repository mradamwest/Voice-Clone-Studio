# Voice Clone Studio

Modern Windows desktop voice cloning and speech generation application.

## Direction
- Approved dark premium desktop UI
- Local-first voice cloning and speech generation
- Chatterbox engine integration
- English and Arabic workflow
- CPU fallback with optional NVIDIA acceleration
- WAV/MP3 export
- Packaged Windows application tested in CI

## Development principle
Dependencies are pinned and upgraded only after compatibility testing. CI tests the packaged application, not only source imports.


## Build validation

Release builds are gated on packaged application startup and the exact multilingual Chatterbox engine import. The engine readiness check deliberately avoids importing the Chatterbox package initializer because it loads optional engines that Voice Clone Studio does not use.
