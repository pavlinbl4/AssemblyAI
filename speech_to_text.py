# `pip3 install assemblyai` (macOS)
# `pip install assemblyai` (Windows)
# pip install python-dotenv
import logging
import os
import sys
from pathlib import Path
from typing import Optional, List, Union

import assemblyai as aai
import pyperclip
from dotenv import load_dotenv

from gui_select_file import select_file

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SpeechToText:
    """
    A convenient class for transcribing audio files to text using AssemblyAI.
    Supports both single speaker and multi-speaker modes with various output options.
    """

    # Default configuration
    DEFAULT_LANGUAGE = "ru"
    DEFAULT_SPEAKER_LABELS = True
    DEFAULT_SUMMARIZATION = False
    DEFAULT_SUMMARIZATION_MODEL = "informative"
    DEFAULT_SUMMARIZATION_TYPE = "paragraphs"
    DEFAULT_SUMMARIZATION_QUESTION = None
    TRANSCRIPTION_FOLDER = "Transcription"  # Имя папки для сохранения

    def __init__(self, path_to_file: str,
                 language: str = DEFAULT_LANGUAGE,
                 single_speaker: bool = False,
                 speaker_labels: bool = DEFAULT_SPEAKER_LABELS,
                 summarization: bool = DEFAULT_SUMMARIZATION,
                 summarization_model: str = DEFAULT_SUMMARIZATION_MODEL,
                 summarization_type: str = DEFAULT_SUMMARIZATION_TYPE,
                 summarization_question: Optional[str] = DEFAULT_SUMMARIZATION_QUESTION):
        """
        Initialize the SpeechToText class.
        """
        self.transcriber_result = None
        self.summarization_result = None
        self.config = None
        self.transcript = None  # Store the full transcript object
        self.path_to_file = path_to_file
        self.file_name = Path(path_to_file).stem
        self.single_speaker = single_speaker
        self.language = language
        self.speaker_labels = speaker_labels
        self.summarization = summarization
        self.summarization_model = summarization_model
        self.summarization_type = summarization_type
        self.summarization_question = summarization_question

        # Validate file exists
        if not os.path.exists(path_to_file):
            raise FileNotFoundError(f"Audio file not found: {path_to_file}")

    @staticmethod
    def get_transcription_folder_path() -> Path:
        """
        Get the path to the Transcription folder in the user's home directory.
        Creates the folder if it doesn't exist.

        Returns:
            Path: Path object pointing to the Transcription folder
        """
        # Get user's home directory
        home_dir = Path.home()

        # Create path to Transcription folder
        transcription_folder = home_dir / SpeechToText.TRANSCRIPTION_FOLDER

        # Create folder if it doesn't exist
        if not transcription_folder.exists():
            transcription_folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created Transcription folder at: {transcription_folder}")

        return transcription_folder

    def configuration(self, api_key: Optional[str] = None) -> aai.TranscriptionConfig:
        """
        Configure AssemblyAI with API key and return transcription config.
        """
        load_dotenv()

        # Use provided API key or get from environment
        api_key = api_key or os.getenv("ASSEMBLYAI_API_KEY")
        if not api_key:
            raise RuntimeError("API key not found in environment variables or provided as argument.")

        aai.settings.api_key = api_key

        # Create configuration with summarization settings if enabled
        config_params = {
            "language_code": self.language,
            "speaker_labels": self.speaker_labels
        }

        # Add summarization configuration if enabled
        if self.summarization:
            config_params["summarization"] = True
            config_params["summary_model"] = self.summarization_model
            config_params["summary_type"] = self.summarization_type

        config = aai.TranscriptionConfig(**config_params)

        return config

    def transcribe(self, show_progress: bool = True) -> aai.Transcript:
        """
        Transcribe the audio file.
        """
        try:
            if show_progress:
                logger.info(f"Starting transcription for: {self.path_to_file}")

            config = self.configuration()
            transcriber = aai.Transcriber()

            # Start transcription
            self.transcript = transcriber.transcribe(self.path_to_file, config)

            # Check for errors
            if self.transcript.status == aai.TranscriptStatus.error:
                logger.error(f"Transcription failed: {self.transcript.error}")
                raise RuntimeError(f"Transcription failed: {self.transcript.error}")

            if show_progress:
                logger.info("Transcription completed successfully!")

            return self.transcript

        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            raise

    def process_transcription(self, transcript: aai.Transcript) -> None:
        """
        Process the transcription result based on configuration.
        """
        self.transcript = transcript  # Store the transcript for later use

        if self.single_speaker:
            # If single speaker mode is enabled, get transcribed sentences
            self.transcriber_result = transcript.get_sentences()
        else:
            # If multiple speaker mode, get utterances
            self.transcriber_result = transcript.utterances

        # Get summary if it was requested and generated during transcription
        if self.summarization and transcript.summary:
            self.summarization_result = transcript.summary
            logger.info("Summary retrieved successfully!")

        # Save to file and copy to clipboard
        self.save_to_text_file()


        logger.info("Processing completed successfully!")

    def save_to_text_file(self) -> None:
        """
        Save the transcription to a text file in the Transcription folder.
        """
        # Get the Transcription folder path
        transcription_folder = self.get_transcription_folder_path()

        # Create output filename with timestamp to avoid overwriting
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{self.file_name}_{timestamp}.txt"
        output_path = transcription_folder / output_filename

        try:
            with open(output_path, 'w', encoding='utf-8') as text_file:
                # Write header with file information
                text_file.write("=" * 60 + "\n")
                text_file.write("TRANSCRIPTION\n")
                text_file.write("=" * 60 + "\n\n")

                # Write metadata
                from datetime import datetime
                text_file.write(f"Source file: {self.path_to_file}\n")
                text_file.write(f"Transcription date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                text_file.write(f"Language: {self.language}\n")
                text_file.write(f"Mode: {'Single speaker' if self.single_speaker else 'Multiple speakers'}\n\n")

                # Write transcription content
                text_file.write("=" * 60 + "\n")
                text_file.write("TRANSCRIPTION CONTENT\n")
                text_file.write("=" * 60 + "\n\n")

                for sentence in self.transcriber_result:
                    if self.single_speaker:
                        text_file.write(f"{sentence.text}\n")
                        print(sentence.text)
                    else:
                        line = f'Speaker {sentence.speaker}: {sentence.text}\n'
                        text_file.write(line)
                        print(f'Speaker {sentence.speaker}: {sentence.text}')

                # Write summary if available
                if self.summarization_result:
                    text_file.write("\n" + "=" * 60 + "\n")
                    text_file.write("SUMMARY\n")
                    text_file.write("=" * 60 + "\n\n")
                    text_file.write(str(self.summarization_result))
                    print("\n=== SUMMARY ===")
                    print(self.summarization_result)

                # Write footer
                text_file.write("\n\n" + "=" * 60 + "\n")
                text_file.write("End of transcription\n")
                text_file.write("=" * 60 + "\n")

            logger.info(f"Transcription saved to: {output_path}")

        except Exception as e:
            logger.error(f"Error saving transcription: {str(e)}")
            raise

    def copy_to_clipboard(self) -> None:
        """
        Copy the transcription to the clipboard.
        """
        try:
            if self.single_speaker:
                text_to_copy = ' '.join([sentence.text for sentence in self.transcriber_result])
            else:
                text_to_copy = ' '.join([f'Speaker {sentence.speaker}: {sentence.text}'
                                         for sentence in self.transcriber_result])

            pyperclip.copy(text_to_copy)
            logger.info("Transcription copied to clipboard")
        except Exception as e:
            logger.error(f"Error copying to clipboard: {str(e)}")

    def speech_to_text(self, show_progress: bool = True) -> None:
        """
        Complete process: transcribe, process, save, and copy to clipboard.
        """
        try:
            # Step 1: Transcribe the audio
            transcript = self.transcribe(show_progress=show_progress)

            # Step 2: Process the transcription
            self.process_transcription(transcript)

        except Exception as e:
            logger.error(f"Error in speech-to-text processing: {str(e)}")
            raise

    @staticmethod
    def quick_transcribe(path_to_file: str,
                         api_key: Optional[str] = None,
                         language: str = DEFAULT_LANGUAGE,
                         single_speaker: bool = True,
                         save_file: bool = True,
                         copy_to_clip: bool = True) -> List[Union[aai.Sentence, aai.Utterance]]:
        """
        Quick method for simple transcription tasks.
        """
        # Create instance with basic settings
        stt = SpeechToText(
            path_to_file=path_to_file,
            language=language,
            single_speaker=single_speaker
        )

        # Transcribe
        transcript = stt.transcribe()

        # Process results
        if single_speaker:
            result = transcript.get_sentences()
        else:
            result = transcript.utterances

        # Save and copy if requested
        if save_file:
            stt.transcriber_result = result
            stt.save_to_text_file()

        if copy_to_clip:
            stt.transcriber_result = result
            stt.copy_to_clipboard()

        return result


def gui_select_file():
    """GUI file selection interface wrapper."""
    return select_file()


def main():
    """Main execution function with improved error handling and user feedback."""
    try:
        # Get file path through GUI
        path_to_file = gui_select_file()
        if not path_to_file:
            logger.warning("No file selected. Exiting.")
            return

        logger.info(f"Processing file: {path_to_file}")

        # Create SpeechToText instance with default settings
        speaker = SpeechToText(path_to_file)
        speaker.speech_to_text()

        logger.info("Processing completed successfully!")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()