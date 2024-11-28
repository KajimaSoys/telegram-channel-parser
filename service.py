from typing import List, Dict, Any
from telethon import TelegramClient
from telethon.tl.types import InputPeerChannel, Channel, User
from telethon.errors import SessionPasswordNeededError
import csv
import os
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
SESSION_NAME = 'onedudeadam'  # Название файла сессии


async def authorize() -> TelegramClient:
    """
    Авторизуется в Telegram и возвращает объект клиента. Сессия сохраняется в файл.

    :return: TelegramClient
    """

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    if not os.path.exists(f"{SESSION_NAME}.session"):
        await client.start()
        if not await client.is_user_authorized():
            phone = input("Введите ваш номер телефона (в формате +123456789): ")
            await client.send_code_request(phone)
            try:
                code = input("Введите код из Telegram: ")
                await client.sign_in(phone, code)
            except SessionPasswordNeededError:
                password = input("Введите ваш пароль двухфакторной аутентификации: ")
                await client.sign_in(password=password)
    else:
        await client.start()
    return client


async def get_chats(client: TelegramClient) -> List[Channel]:
    """
    Получает список чатов и каналов.

    :param client: TelegramClient
    :return: Список объектов Channel
    """

    dialogs = await client.get_dialogs()
    channels = [dialog.entity for dialog in dialogs if isinstance(dialog.entity, Channel)]
    for idx, channel in enumerate(channels, 1):
        print(f"{idx}. {channel.title}")
    return channels


def select_channels(channels: List[Channel]) -> List[Channel]:
    """
    Запрашивает у пользователя выбор каналов.

    :param channels: Список объектов Channel
    :return: Список выбранных объектов Channel
    """

    choices = input("Введите номера каналов через пробел или запятую: ")
    indices = set()
    for item in choices.replace(',', ' ').split():
        if item.isdigit():
            idx = int(item) - 1
            if 0 <= idx < len(channels):
                indices.add(idx)
    return [channels[i] for i in indices]


async def get_participants(client: TelegramClient, channel: Channel) -> List[Dict[str, Any]]:
    """
    Получает список участников канала.

    :param client: TelegramClient
    :param channel: Объект Channel
    :return: Список словарей с информацией о пользователях
    """

    participants = []
    async for user in client.iter_participants(channel):
        participants.append({
            'user_id': user.id,
            'username': user.username or '',
            'full_name': f"{user.first_name or ''} {user.last_name or ''}".strip(),
            'is_premium': 'Да' if getattr(user, 'premium', False) else 'Нет',
        })
    return participants


def sanitize_filename(filename: str) -> str:
    """
    Удаляет или заменяет недопустимые символы в имени файла.

    :param filename: Исходное имя файла
    :return: Очищенное имя файла
    """

    return re.sub(r'[<>:"/\\|?*]', '_', filename)


def write_to_csv(channel_title: str, participants: List[Dict[str, Any]]) -> None:
    """
    Записывает список участников в CSV-файл, добавляя новые уникальные записи.

    :param channel_title: Название канала
    :param participants: Список словарей с информацией о пользователях
    """

    sanitized_title = sanitize_filename(channel_title)
    filename = f"{datetime.now().strftime('%Y-%m-%d')} Список участников {sanitized_title}.csv"

    # Словарь для хранения уникальных пользователей по user_id
    participants_dict = {}

    # Если файл существует, читаем существующих участников
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                user_id = int(row['user_id'])
                participants_dict[user_id] = row

    # Добавляем новых участников, проверяя на уникальность по user_id
    for participant in participants:
        user_id = participant['user_id']
        if user_id not in participants_dict:
            participants_dict[user_id] = {
                'user_id': user_id,
                'username': participant['username'],
                'full_name': participant['full_name'],
                'is_premium': participant['is_premium'],
            }

    # Записываем объединенный список уникальных участников обратно в файл
    with open(filename, 'w', encoding='utf-8', newline='') as csvfile:
        fieldnames = ['user_id', 'username', 'full_name', 'is_premium']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for participant in participants_dict.values():
            writer.writerow(participant)
