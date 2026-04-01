# OPERATIONAL PROCEDURES

## Workflow: The Content Pipeline
1. **Intake:** Listen to the Telegram Bridge for messages from the ESTHER bot.
2. **Analysis:** Summarize the technical finding into a 3-point "Why this matters" list.
3. **Drafting:** - Write 1x X (Twitter) thread.
    - Write 1x YouTube Short/TikTok script (max 50 seconds).
4. **Media Generation:**
    - Call AppleScript to open **Luminar Neo**.
    - Apply "Fink Security" branding presets to the thumbnail.
    - Export assets to the `~/Documents/Fink_Uploads` folder.

## Tools & Commands
- To edit photos: Use `osascript scripts/luminar_automation.scpt`.
- To generate video: Use `ffmpeg` via the terminal.
