import asyncio
from service import (
    authorize,
    get_chats,
    select_channels,
    get_participants,
    write_to_csv,
)


async def main() -> None:
    client = await authorize()

    try:
        chats = await get_chats(client)
        selected_channels = select_channels(chats)
        for channel in selected_channels:
            participants = await get_participants(client, channel)
            write_to_csv(channel.title, participants)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
