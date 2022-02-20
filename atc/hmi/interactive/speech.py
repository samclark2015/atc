import re
from io import BytesIO

import speech_recognition as sr
from gtts import gTTS
from PyQt5 import QtCore, QtMultimedia
from PyQt5.QtTextToSpeech import QTextToSpeech

# obtain audio from the microphone
r = sr.Recognizer()
engineNames = QTextToSpeech.availableEngines()

if len(engineNames) > 0:
    engineName = engineNames[0]
    engine = QTextToSpeech(engineName)

# player = QtMultimedia.QMediaPlayer()


class SpeechCom:
    def get_input(self):
        with sr.Microphone() as source:
            print("Say something!")
            audio = r.listen(source)

        try:
            text = r.recognize_google(audio)
            text = text.lower()
            print("< {}".format(text))
            return text
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print(
                "Could not request results from Google Speech Recognition service; {0}".format(
                    e
                )
            )

    def respond(self, text: str):
        print(">", text)

        # buffer = QtCore.QBuffer()
        # buffer.open(QtCore.QIODevice.ReadWrite)
        # gTTS(text).write_to_fp(buffer)
        # buffer.seek(0)

        # content = QtMultimedia.QMediaContent()
        # player.setMedia(content, buffer)
        # player.play()

        engine.say(text)
