import sys
import cv2
import threading
import numpy as np
import speech_recognition as sr
import google.generativeai as genai
from deepface import DeepFace
from PyQt5.QtWidgets import  QScrollArea,QApplication, QWidget, QVBoxLayout, QLabel, QTextBrowser, QPushButton, QHBoxLayout
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtCore import Qt, QMetaObject, Q_ARG
from PyQt5.QtGui import QTextCursor  




# Configure Google Generative AI (Replace 'YOUR_API_KEY' with your actual key)
genai.configure(api_key="AIzaSyAqogEyMCExffBBKTzbglxVTB8jhMOdJDc")
model = genai.GenerativeModel("gemini-1.5-flash")  # Change model if needed
chat_session = model.start_chat(
    history=[
        {
            "role": "user",
            "parts": [
                "You are a Mock Interviewer. Ask the candidate questions and reply accordingly based on his/her career choice. Begin with asking him/her the Career option.ask short questions.ask one at a time.",
            ],
        },
    ]
)
class MockInterviewApp(QWidget):
    def __init__(self):
        super().__init__()
        self.running=True
        self.setWindowTitle("AI Mock Interview")
        self.setGeometry(100, 100, 900, 500)
           
        # Layout
        self.layout = QHBoxLayout(self)

        # Left Column: Camera Feed & Emotion Display
        self.left_layout = QVBoxLayout()
        self.camera_label = QLabel(self)
        self.camera_label.setFixedSize(400, 400)
        self.camera_label.setStyleSheet("border: 2px solid black;")
        self.emotion_label = QLabel("Emotion: Analyzing...")
        self.emotion_label.setFont(QFont("Arial", 12, QFont.Bold))

        self.confidence_label = QLabel("Confidence: Analyzing...")
        self.confidence_label.setFont(QFont("Arial", 12, QFont.Bold))

        self.left_layout.addWidget(self.camera_label)
        self.left_layout.addWidget(self.emotion_label)
        self.left_layout.addWidget(self.confidence_label)
        self.layout.addLayout(self.left_layout)




        # Make Right Layout Scrollable
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Container for Right Layout
        self.scroll_widget = QWidget()
        self.right_layout = QVBoxLayout(self.scroll_widget)

        self.chat_display = QTextBrowser()
        self.chat_display.setFont(QFont("Arial", 11))
        self.start_button = QPushButton("Start Interview")
        self.stop_button = QPushButton("Stop Interview")

        self.right_layout.addWidget(self.chat_display)
        self.right_layout.addWidget(self.start_button)
        #self.right_layout.addWidget(self.stop_button)

        self.scroll_widget.setLayout(self.right_layout)
        self.scroll_area.setWidget(self.scroll_widget)

        self.layout.addWidget(self.scroll_area)

        # Right Column: Chat Messages & Controls
        '''self.right_layout = QVBoxLayout()
        self.chat_display = QTextBrowser()
        self.chat_display.setFont(QFont("Arial", 11))
        self.start_button = QPushButton("Start Interview")
        self.stop_button = QPushButton("Stop Interview")

        self.right_layout.addWidget(self.chat_display)
        self.right_layout.addWidget(self.start_button)
        self.right_layout.addWidget(self.stop_button)
        self.layout.addLayout(self.right_layout)'''


        

        # Timer for camera updates & emotion detection
        self.timer = QTimer(self)

        # Button Connections
        self.start_button.clicked.connect(self.start_interview)
        #self.stop_button.clicked.connect(self.stop_interview)

        # Speech Recognizer
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
            

    def analyze_emotion(self):
        """Detects the candidate's emotion from the video frame"""
        while(self.running):
            ret, frame = self.cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                q_img = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
                self.camera_label.setPixmap(QPixmap.fromImage(q_img))

                try:
                    analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                    dominant_emotion = analysis[0]['dominant_emotion']
                    emotion=analysis[0]['emotion']
                    self.emotion_label.setText(f"Emotion: {dominant_emotion.capitalize()}")
                    self.confidence_label.setText(f"Confidence: {round((100-emotion['fear'])*emotion['happy']*emotion['neutral']%100)}% ")
                except Exception as e:
                    self.emotion_label.setText("Emotion: Not detected")
                    self.confidence_label.setText("Confidence: Not detected")

    def start_interview(self):
        self.cap = cv2.VideoCapture(0)
        self.running=True
        self.timer.start(30)  # Start camera feed
        self.add_message("Interviewer", "Welcome to the mock interview! Please introduce yourself.")

        # Start speech recognition in a separate thread
        threading.Thread(target=self.speech_recognition, daemon=True).start()

        threading.Thread(target=self.analyze_emotion, daemon=True).start()

    def stop_interview(self):
        self.running=False
        self.timer.stop()
        self.cap.release()
        self.add_message("Interviewer", "Interview Ended.")

    def speech_recognition(self):
        while(self.running):
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                self.add_message("Interviewer", "Listening...")

                try:
                    audio = self.recognizer.listen(source)
                    text = self.recognizer.recognize_google(audio)
                    self.add_message("You", text)

                    # Get AI response
                    ai_response = self.get_ai_response(text)
                    self.add_message("Interviewer", ai_response)

                except sr.UnknownValueError:
                    self.add_message("Interviewer", "Sorry, I couldn't understand.")
                except sr.RequestError:
                    self.add_message("Interviewer", "Network error. Please check your connection.")

    def get_ai_response(self, text):
        """Sends user input to Google Generative AI and gets a response"""
        try:
            response = chat_session.send_message(text)
            return response.text
        except Exception as e:
            return f"AI Error: {str(e)}"

    from PyQt5.QtCore import QMetaObject, Qt, Q_ARG

    def add_message(self, sender, message):
        if sender == "You":
            self.chat_display.append(f'<p style="color: blue; text-align: right;"><b>{sender}:</b> {message}</p>')
        else:
            self.chat_display.append(f'<p style="color: green; text-align: left;"><b>{sender}:</b> {message}</p>')


   

    def closeEvent(self, event):
        self.cap.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MockInterviewApp()
    window.show()
    sys.exit(app.exec_())
