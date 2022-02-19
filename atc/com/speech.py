import re

import pyttsx3
import speech_recognition as sr

# obtain audio from the microphone
r = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty("rate", 200)


class SpeechCom:
    def get_input(self):
        while True:
            input("Press a key to continue...")
            with sr.Microphone() as source:
                print("Say something!")
                audio = r.listen(source)

            try:
                text = r.recognize_google(audio)
                text = text.lower()
                print("< {}".format(text))
                yield text
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
        engine.say(text)
        engine.runAndWait()
