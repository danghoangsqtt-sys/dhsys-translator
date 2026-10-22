# Stack decisions for ENH-004

Accessed: 2026-10-05. These are implementation constraints, not new mandatory runtime dependencies.

| Component | Decision | Do | Do not | Source |
| --- | --- | --- | --- | --- |
| PySide6 / Qt Widgets | Preserve current desktop stack | Use standard item-view focus, selection and edit triggers; cover with Qt tests | Invent a parallel web editor or put media logic in widgets | https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTableWidget.html |
| FFmpeg | Preserve media assembly pipeline | Verify hard subtitle pixels and soft subtitle streams separately | Treat a soft subtitle stream as visibly rendered in every player | https://ffmpeg.org/ffmpeg.html |
| VieNeu-TTS v3 Turbo | Local opt-in pilot through existing OpenAI TTS adapter | Isolate the server on loopback and benchmark Turbo voices | Bundle its runtime or make Nano the En–Vi default before a pilot | https://github.com/pnnbao97/VieNeu-TTS |
| sea-g2p | Use through a controlled TTS-text preparation layer | Keep original SRT; annotate/detect code-switch spans and honor glossary overrides | Rewrite displayed subtitles into phonetic Vietnamese | https://github.com/pnnbao97/sea-g2p |
| Gemini API | Optional translation/STT profile | Pin a tested model and disclose quota/data behavior | Claim the free tier is unlimited or use it without a fallback | https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite |
| OpenRouter | Advanced compatible endpoint | Let users select a model and show rate-limit/failure state | Treat free routing as the primary production backend | https://openrouter.ai/docs/faq |

## ENH-009 additions

Accessed: 2026-10-22.

| Component | Decision | Do | Do not | Source |
| --- | --- | --- | --- | --- |
| Qt Multimedia (PySide6) | Result panel playback | Use `QMediaPlayer` + `QAudioOutput` + `QVideoWidget`; clear the source when hidden so Windows releases the file; verify the FFmpeg backend plugin in the frozen build | Assume codecs work in `dist/sp` because they work from source | https://doc.qt.io/qtforpython-6/PySide6/QtMultimedia/QMediaPlayer.html |
| ASS / libass | Animated captions | Use `\kf` karaoke (centiseconds), `\t` transforms, `\fad`, BorderStyle 3 boxes; set PlayResX/Y to the video size | Rely on soft `mov_text` tracks to keep effects | https://aegisub.org/docs/latest/ass_tags/ |
| FFmpeg `subtitles` filter | Burn styled ASS | Pass `fontsdir` to the bundled font folder and escape `:`/`\` in Windows paths | Depend on system fonts for Vietnamese diacritics | https://ffmpeg.org/ffmpeg-filters.html#subtitles-1 |
| Be Vietnam Pro | Caption font | Ship TTF + OFL.txt and list it in the license inventory | Rename the font family (OFL reserved-name rules) | https://fonts.google.com/specimen/Be+Vietnam+Pro |
