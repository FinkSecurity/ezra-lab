# Ezra — Fink Security Media Agent

Ezra is an autonomous media creation agent running on a MacBook Pro via OpenClaw. She works alongside ESTHER (Fink Security's VPS-based security research agent) to create visual content — thumbnails, social graphics, and video assets — based on ESTHER's security findings.

## Stack
- OpenClaw 2026.4.1 (macOS)
- qwen2.5:14b via Ollama (primary)
- Claude Haiku via OpenRouter (fallback)
- LanceDB vector memory
- ImageMagick + Pillow + FFmpeg
- Luminar Neo 1.26.1 (AppleScript)

## Companion Agent
- [ESTHER](https://github.com/FinkSecurity/esther-lab) — autonomous security research agent
- [estherops.tech](https://estherops.tech) — published findings
- [finksecurity.com](https://finksecurity.com) — commercial services
