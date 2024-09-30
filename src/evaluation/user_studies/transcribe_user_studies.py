import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

audio_dir = "./audios"
transcription_path = "./transcriptions"
os.makedirs(transcription_path, exist_ok=True)
# Loop through all .m4a files in the directory
for audio_file_name in os.listdir(audio_dir):
    if audio_file_name.endswith(".m4a"):
        print(f"{audio_file_name}")
        audio_path = os.path.join(audio_dir, audio_file_name)
        # Transcribe the audio file
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=audio_file, model="whisper-1"
            )

        # Save the transcription to a text file
        with open(
            os.path.join(transcription_path, audio_file_name.removesuffix(".m4a") + ".txt"),
            "w",
        ) as f:
            f.write(transcript.text)

        print(f"Transcription saved for {audio_file_name}")
