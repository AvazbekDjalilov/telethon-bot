from telethon import TelegramClient, events
from telethon.tl.types import (
    MessageEntityBold, MessageEntityItalic, MessageEntityUnderline,
    MessageEntityStrike, MessageEntityCode, MessageEntityPre
)
import html
import asyncio
import os
from collections import defaultdict

api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")

source_channels = ['CodeAntipova', 'ecotopor']
target_channel = 'nuwseco'

client = TelegramClient('session_name', api_id, api_hash)
album_groups = defaultdict(list)

def render_html(text, entities):
    if not entities:
        return html.escape(text)

    result = []
    last_offset = 0

    skip_types = (
        'MessageEntityTextUrl', 'MessageEntityUrl', 'MessageEntityMention',
        'MessageEntityMentionName', 'MessageEntityHashtag'
    )

    for entity in sorted(entities, key=lambda e: e.offset):
        entity_type = type(entity).__name__

        if last_offset < entity.offset:
            result.append(html.escape(text[last_offset:entity.offset]))

        entity_text = text[entity.offset:entity.offset + entity.length]

        if entity_type in skip_types:
            last_offset = entity.offset + entity.length
            continue

        entity_html = html.escape(entity_text)
        result.append(entity_html)
        last_offset = entity.offset + entity.length

    if last_offset < len(text):
        result.append(html.escape(text[last_offset:]))

    return ''.join(result)

@client.on(events.NewMessage(chats=source_channels))
async def handler(event):
    message = event.message
    grouped_id = message.grouped_id

    if grouped_id:
        album_groups[grouped_id].append(message)
        await asyncio.sleep(1.5)

        if len(album_groups[grouped_id]) > 1:
            messages = album_groups.pop(grouped_id)
            media_files = [m.media for m in messages if m.media]
            first_msg = messages[0]
            html_text = render_html(first_msg.text or '', first_msg.entities or [])

            try:
                await client.send_file(
                    target_channel,
                    file=media_files,
                    caption=html_text,
                    parse_mode='html'
                )
            except Exception as e:
                print(f"Ошибка при пересылке альбома: {e}")
    else:
        text = message.text or ''
        html_text = render_html(text, message.entities or [])

        try:
            if message.media:
                await client.send_file(
                    target_channel,
                    file=message.media,
                    caption=html_text,
                    parse_mode='html'
                )
            else:
                await client.send_message(
                    target_channel,
                    html_text,
                    parse_mode='html'
                )
        except Exception as e:
            print(f"Ошибка при пересылке сообщения: {e}")

client.start()
print("✅ Бот запущен.")
client.run_until_disconnected()
