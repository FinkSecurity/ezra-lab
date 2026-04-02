# TOOLS.md — Media Tools & Tips

## Workspace
- All work happens inside: `~/tools/fink-media-automation/`
- Output goes to: `~/tools/fink-media-automation/media/output/`
- Never reference `/workspace` — that path does not exist on this Mac

## Available Tools (Installed & Ready)

### Image Creation & Editing
- **ImageMagick** (`convert`, `magick`) — command line image generation, text overlays, compositing
- **Pillow** (`python3` + `from PIL import Image`) — Python image manipulation
- **Luminar Neo** — installed at /Applications/Luminar Neo.app — ask operator for AppleScript commands

### Video & Audio
- **FFmpeg** (`ffmpeg`) — video creation, overlays, encoding, trimming, audio mixing

### Python
- `python3` — available, Pillow installed
- Scripts go in `./scripts/`

### Browser/Canvas
- `canvas.*` — live previews and snapshots

## Tool Install Process
- Need a new tool? Use `brew install <tool>` via exec or ask operator to install

## Common Workflows

### Thumbnail (ImageMagick — fastest)
```bash
convert -size 1280x720 xc:#0a0a12 \
  -font Helvetica-Bold -pointsize 72 -fill '#22d3ee' \
  -gravity Center -annotate 0 'YOUR TITLE HERE' \
  media/output/thumbnail-$(date +%Y%m%d).png
```

### Thumbnail (Python/Pillow — more control)
```python
from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGB', (1280, 720), '#0a0a12')
# draw text, shapes etc
img.save('media/output/thumbnail.png')
```

### Short video overlay (FFmpeg)
```bash
ffmpeg -i media/raw/input.mp4 \
  -vf "drawtext=text='YOUR TEXT':fontcolor=white:fontsize=48:x=100:y=100" \
  media/output/output-$(date +%Y%m%d).mp4
```

## Fink Security Brand Colors
- Background: #0a0a12
- Cyan accent: #22d3ee
- Light cyan: #67e8f9
- White text: #f3f4f6
- Muted: #94a3b8

## Notes
- Never commit binary files (png, mp4, jpg) to git
- Use descriptive filenames with dates: `xss-thumbnail-20260401.png`
- Brand colors above match finksecurity.com and estherops.tech

## Luminar Neo (AppleScript Control)
Version 1.26.1 — confirmed scriptable via AppleScript.

### Basic AppleScript pattern
```applescript
tell application "Luminar Neo"
    open POSIX file "/Users/afink/tools/fink-media-automation/media/assets/base.jpg"
end tell
```

### Export via AppleScript (example)
```applescript
tell application "Luminar Neo"
    export current document to POSIX file "/Users/afink/tools/fink-media-automation/media/output/result.jpg"
end tell
```

Use osascript to run AppleScript from exec:
```bash
osascript -e 'tell application "Luminar Neo" to ...'
```
