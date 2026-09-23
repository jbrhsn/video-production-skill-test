# Voice selection

Default to af_heart for English smoke tests. Offer af_bella or am_michael for American English, or bf_emma / bm_george for British English when a choice helps. Use --lang en-gb for British English. Voice descriptions are listening preferences, not measured quality rankings.

The downloaded voices-v1.0.bin archive is the authority for available IDs. 01_tts.py rejects unknown IDs and prints the available list. Do not invent IDs or promise a fixed voice count across releases.

For other languages, consult the [upstream voice guide](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) and [kokoro-onnx examples](https://github.com/thewh1teagle/kokoro-onnx/tree/main/examples). A voice existing in the archive does not establish that the default English phonemizer supports its language; verify the appropriate phonemization path with a short sample.

Model/archive downloads must use the compatible [kokoro-onnx model release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0). Individual onnx-community voice files have a different format.
