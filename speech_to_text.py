# `pip3 install assemblyai` (macOS)
# `pip install assemblyai` (Windows)
# pip install python-dotenv
import sys

from dotenv import load_dotenv
import os
import assemblyai as aai
from pathlib import Path
from assemblyai import LanguageCode
from gui_select_file import select_file
import pyperclip


class SpeechToText:
    def __init__(self, path_to_file, single_speaker=True):
        self.transcriber_result = None
        self.config = None
        self.path_to_file = path_to_file
        self.file_name = Path(path_to_file).stem
        self.single_speaker = single_speaker

    @classmethod
    def configuration(cls):
        load_dotenv()
        api_key = os.getenv("ASSEMBLYAI_API_KEY")
        if not api_key:
            raise RuntimeError("API key not found in environment variables.")
        aai.settings.api_key = api_key
        config = aai.TranscriptionConfig(language_code=LanguageCode.ru,
                                         speaker_labels=True)
        return config

    def save_to_text_file(self):
        with open(f'{self.file_name}.txt', 'w', encoding='utf-8') as text_file:
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
        config = self.configuration()
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
    path_to_file = select_file()
    speaker = SpeechToText(path_to_file)
    speaker.speech_to_text()


if __name__ == '__main__':
    main()
