import os
from pathlib import Path
from loguru import logger

import assemblyai as aai
# from gui_select_file import select_file
import pyperclip
from dotenv import load_dotenv
import yaml


class SpeechToText:
    def __init__(self, path_to_file, single_speaker=True):
        self.transcriber_result = None
        self.config = None
        self.path_to_file = path_to_file
        self.file_name = Path(path_to_file).stem
        self.single_speaker = single_speaker
        self.settings = self.load_settings_from_yaml()

    @staticmethod
    def load_settings_from_yaml(settings_path="config/settings.yaml"):
        """Загружает настройки из YAML файла."""
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                logger.success("Yaml file loaded successfully")
                return yaml.safe_load(f)

        except FileNotFoundError:
            print(f"Файл настроек {settings_path} не найден. Используются настройки по умолчанию.")
            return {
                "assemblyai": {
                    "language_code": "ru",
                    "speaker_labels": True
                },
                "transcription": {
                    "single_speaker": False,
                    "output_format": "txt",
                    "encoding": "utf-8"
                },
                "paths": {
                    "output_dir": "./transcripts"
                }
            }


    @classmethod
    def configuration(cls, settings=None):
        load_dotenv()
        api_key = os.getenv("ASSEMBLYAI_API_KEY")
        if not api_key:
            raise RuntimeError("API key not found in environment variables.")
        aai.settings.api_key = api_key
        
        if settings is None:
            settings = cls.load_settings_from_yaml()
            
        assemblyai_settings = settings.get("assemblyai", {})
        config = aai.TranscriptionConfig(
            language_code=assemblyai_settings.get("language_code", "ru"),
            speaker_labels=assemblyai_settings.get("speaker_labels", True)
        )

        return config

    def save_to_text_file(self):
        # Получаем настройки из YAML
        transcription_settings = self.settings.get("transcription", {})
        paths_settings = self.settings.get("paths", {})
        encoding = transcription_settings.get("encoding", "utf-8")
        output_dir = paths_settings.get("output_dir", "./transcripts")
        output_format = transcription_settings.get("output_format", "txt")
        
        # Создаем директорию для сохранения результатов, если она не существует
        os.makedirs(output_dir, exist_ok=True)
        
        # Формируем путь к файлу
        output_path = os.path.join(output_dir, f"{self.file_name}.{output_format}")
        
        with open(output_path, 'w', encoding=encoding) as text_file:
            for sentence in self.transcriber_result:
                if self.single_speaker:
                    text_file.writelines(sentence.text + '\n')
                    print(sentence.text)
                else:
                    text_file.writelines(f'Speaker {sentence.speaker} : {sentence.text}')
                    print(f'Speaker {sentence.speaker} : {sentence.text}')

    def copy_to_clipboard(self):
        pyperclip.copy(' '.join([sentence.text for sentence in self.transcriber_result]))

    def sound_transcriber(self):
        config = self.configuration(self.settings)
        transcript = aai.Transcriber().transcribe(self.path_to_file, config)
        return transcript

    def speech_to_text(self):
        if self.single_speaker:
            # If single speaker mode is enabled, get transcribed sentences
            self.transcriber_result = self.sound_transcriber().get_sentences()
        else:
            # If multiple speaker mode, get utterances (which may include speaker identification)
            self.transcriber_result = self.sound_transcriber().utterances
        self.save_to_text_file()
        self.copy_to_clipboard()


def gui_select_file():
    pass


def main():
    # Загружаем настройки из YAML
    settings = SpeechToText.load_settings_from_yaml()
    logger.debug(f'{settings = }')
    
    # Получаем необходимые значения
    path_to_file = settings.get("paths", {}).get("test_file")
    single_speaker = settings.get("transcription", {}).get("single_speaker", False)

    if not path_to_file:
        logger.error("Путь к тестовому файлу не указан в настройках")
        return
    
    # Передаем настройки в конструктор
    speaker = SpeechToText(path_to_file, single_speaker)
    speaker.speech_to_text()


if __name__ == '__main__':
    main()
