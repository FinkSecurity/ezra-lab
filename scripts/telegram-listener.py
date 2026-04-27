#!/usr/bin/env python3
"""
telegram-listener.py — Ezra's Fink Security Ops group chat listener
Polls the group chat for THUMBNAIL_REQUEST messages from ESTHER,
generates the image via generate_image.py, SCPs it to the VPS,
and confirms back to the group with THUMBNAIL_READY.

Usage:
    python3 telegram-listener.py           # runs continuously
    python3 telegram-listener.py --once    # process one pending request and exit

Requires:
    EZRA_BOT_TOKEN and GROUP_CHAT_ID in secrets.env
    FAL_API_KEY in secrets.env
    ezra-vps.key at ~/tools/ezra-lab/ezra-vps.key
"""

import os
import sys
import time
import subprocess
import argparse
from pathlib import Path

# ── Resolve paths ─────────────────────────────────────────────────────────────
EZRA_LAB     = Path.home() / 'tools' / 'ezra-lab'
SECRETS_FILE = EZRA_LAB / 'secrets.env'
GENERATE_IMG = EZRA_LAB / 'scripts' / 'generate_image.py'
VPS_KEY      = EZRA_LAB / 'ezra-vps.key'
OUTPUT_DIR   = EZRA_LAB / 'media' / 'thumbnails'

VPS_USER     = 'esther'
VPS_HOST     = '45.82.72.151'
VPS_PORT     = '2222'
VPS_THUMB_DIR = '~/estherops-site/static/thumbnails'

REQUEST_TAG  = '🖼️ THUMBNAIL_REQUEST'
READY_TAG    = '✅ THUMBNAIL_READY'
POLL_INTERVAL = 5   # seconds between polls

# ── Load secrets ──────────────────────────────────────────────────────────────
def load_secrets() -> dict:
    secrets = {}
    if SECRETS_FILE.exists():
        for line in SECRETS_FILE.read_text().splitlines():
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                secrets[k.strip()] = v.strip().strip('"\'')
    # Env vars override file
    for key in ['EZRA_BOT_TOKEN', 'GROUP_CHAT_ID', 'FAL_API_KEY']:
        if os.environ.get(key):
            secrets[key] = os.environ[key]
    return secrets


# ── Telegram helpers ──────────────────────────────────────────────────────────
def get_updates(bot_token: str, offset: int = 0) -> list:
    import urllib.request, json
    url = (
        f'https://api.telegram.org/bot{bot_token}/getUpdates'
        f'?offset={offset}&timeout=10'
    )
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            data = json.loads(r.read())
            return data.get('result', [])
    except Exception as e:
        print(f'[WARN] getUpdates failed: {e}')
        return []


def send_message(bot_token: str, chat_id: str, text: str):
    import urllib.request, urllib.parse, json
    payload = json.dumps({'chat_id': chat_id, 'text': text}).encode()
    req = urllib.request.Request(
        f'https://api.telegram.org/bot{bot_token}/sendMessage',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'[ERROR] sendMessage failed: {e}')
        return None


# ── Parse THUMBNAIL_REQUEST message ──────────────────────────────────────────
def parse_request(text: str) -> dict | None:
    """
    Expects format:
        🖼️ THUMBNAIL_REQUEST
        slug: xiaomi-phase4
        title: Xiaomi Phase 4
        subtitle: Manual Web App Testing
        prompt: dark cyberpunk ...
    Returns dict with keys: slug, title, subtitle, prompt
    Or None if parse fails.
    """
    if REQUEST_TAG not in text:
        return None

    fields = {}
    for line in text.splitlines():
        for key in ['slug', 'title', 'subtitle', 'prompt']:
            if line.lower().startswith(f'{key}:'):
                fields[key] = line.split(':', 1)[1].strip()

    if 'slug' not in fields or 'prompt' not in fields or 'title' not in fields:
        print(f'[WARN] Malformed thumbnail request — missing required fields: {text}')
        return None

    fields.setdefault('subtitle', '')
    return fields


# ── Generate image ────────────────────────────────────────────────────────────
def generate_thumbnail(fields: dict, secrets: dict) -> Path | None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{fields['slug']}.png"

    cmd = [
        sys.executable, str(GENERATE_IMG),
        '--prompt',   fields['prompt'],
        '--title',    fields['title'],
        '--out',      str(out_path),
    ]
    if fields.get('subtitle'):
        cmd += ['--subtitle', fields['subtitle']]

    env = os.environ.copy()
    env['FAL_API_KEY'] = secrets.get('FAL_API_KEY', '')

    print(f'[INFO] Generating thumbnail for slug: {fields["slug"]}')
    print(f'[INFO] Running: {" ".join(cmd)}')

    result = subprocess.run(cmd, env=env, capture_output=True, text=True)

    if result.returncode != 0:
        print(f'[ERROR] generate_image.py failed:\n{result.stderr}')
        return None

    if not out_path.exists():
        print(f'[ERROR] Output file not created: {out_path}')
        return None

    print(f'[OK] Thumbnail generated: {out_path}')
    return out_path


# ── SCP to VPS ────────────────────────────────────────────────────────────────
def scp_to_vps(local_path: Path, slug: str) -> bool:
    remote = f'{VPS_USER}@{VPS_HOST}:{VPS_THUMB_DIR}/{slug}.png'
    cmd = [
        'scp',
        '-i', str(VPS_KEY),
        '-P', VPS_PORT,
        '-o', 'StrictHostKeyChecking=no',
        str(local_path),
        remote
    ]

    print(f'[INFO] SCPing to VPS: {remote}')
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f'[ERROR] SCP failed:\n{result.stderr}')
        return False

    print(f'[OK] SCP complete: {remote}')
    return True


# ── Main loop ─────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Ezra Telegram group listener')
    parser.add_argument('--once', action='store_true', help='Process one request and exit')
    args = parser.parse_args()

    secrets = load_secrets()
    poll_token = secrets.get('RELAY_BOT_TOKEN', '')   # poll with relay bot — no conflict with OpenClaw on either agent
    send_token = secrets.get('EZRA_BOT_TOKEN', '')    # send confirmations with EZRA's token
    chat_id    = secrets.get('GROUP_CHAT_ID', '-5225506150')

    if not poll_token:
        print('[ERROR] RELAY_BOT_TOKEN not found in secrets.env — needed for polling', file=sys.stderr)
        sys.exit(1)
    if not send_token:
        print('[ERROR] EZRA_BOT_TOKEN not found in secrets.env — needed for sending', file=sys.stderr)
        sys.exit(1)

    print(f'[INFO] Ezra listener started — polling group chat {chat_id}')
    print(f'[INFO] Polling via relay bot (avoids OpenClaw 409 conflict on both agents)')
    print(f'[INFO] Watching for: {REQUEST_TAG}')

    # Get current offset so we skip old messages on startup
    updates = get_updates(poll_token)
    offset  = (updates[-1]['update_id'] + 1) if updates else 0
    print(f'[INFO] Starting from update offset: {offset}')

    while True:
        updates = get_updates(poll_token, offset)

        for update in updates:
            offset = update['update_id'] + 1
            msg    = update.get('message', {})
            text   = msg.get('text', '')
            from_chat = str(msg.get('chat', {}).get('id', ''))

            # Only process messages from our group
            if from_chat != chat_id:
                continue

            # Only process THUMBNAIL_REQUEST messages
            if REQUEST_TAG not in text:
                continue

            print(f'\n[INFO] Thumbnail request received')
            fields = parse_request(text)
            if not fields:
                continue

            slug = fields['slug']
            print(f'[INFO] Processing: {slug}')

            # Step 1: Generate
            thumb_path = generate_thumbnail(fields, secrets)
            if not thumb_path:
                send_message(send_token, chat_id,
                    f'❌ THUMBNAIL_FAILED\nslug: {slug}\nReason: image generation failed — check Ezra logs')
                if args.once:
                    sys.exit(1)
                continue

            # Step 2: SCP to VPS
            if not scp_to_vps(thumb_path, slug):
                send_message(send_token, chat_id,
                    f'❌ THUMBNAIL_FAILED\nslug: {slug}\nReason: SCP to VPS failed — check Ezra logs')
                if args.once:
                    sys.exit(1)
                continue

            # Step 3: Confirm back to group with EZRA's token
            send_message(send_token, chat_id,
                f'{READY_TAG}\n'
                f'slug: {slug}\n'
                f'path: {VPS_THUMB_DIR}/{slug}.png\n'
                f'ESTHER: thumbnail is on disk, ready to stage and commit')

            print(f'[OK] Full pipeline complete for: {slug}')

            if args.once:
                sys.exit(0)

        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n[INFO] Ezra listener stopped')
        sys.exit(0)
