# This script creates an office assistive robot application with a GUI.
# It uses PyQt6 for the GUI, OpenCV for face recognition, and Ollama for
# natural language processing. It also includes voice input and output
# capabilities.

# =========================================================================
# PREREQUISITES AND SETUP
# =========================================================================
# 1. Install required Python packages:
#    pip install PyQt6 opencv-python-headless ollama pyttsx3 SpeechRecognition pyaudio
#
#    Note: For 'pyaudio', you might need to install 'portaudio' first on some systems.
#    On Debian/Ubuntu: sudo apt-get install portaudio19-dev
#    On Windows, pre-compiled wheels can often be found online if `pip install` fails.
#
# 2. Set up Ollama:
#    a. Download and install the Ollama server from https://ollama.com.
#    b. Start the server (it usually runs in the background automatically).
#    c. Pull a language model (e.g., Llama 3):
#       ollama pull llama3
#
# 3. Create the 'known_faces' directory:
#    Create a folder named 'known_faces' in the same directory as this script.
#    Inside this folder, create sub-folders for each person, named with their
#    name (e.g., 'known_faces/Mr_Sharma'). Place a single JPG or PNG image
#    of the person inside their folder. The file name doesn't matter.
#
#    Example structure:
#    .
#    ├── office_robot.py
#    └── known_faces/
#        ├── Mr_Sharma/
#        │   └── sharma_photo.jpg
#        └── Ms_Anjali/
#            └── anjali_profile.png
#
# =========================================================================

import os
import sys
import threading
import cv2
import ollama
import pyttsx3
import speech_recognition as sr
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QCoreApplication
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QFileDialog

class FaceRecognitionWorker(QThread):
    """
    Worker thread to handle face recognition, preventing the GUI from freezing.
    """
    face_detected_signal = pyqtSignal(str)

    def __init__(self, known_faces_dir='known_faces'):
        super().__init__()
        self.known_faces_dir = known_faces_dir
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.known_faces = self.load_known_faces()
        self.running = True

    def load_known_faces(self):
        """Loads face data from the 'known_faces' directory."""
        known_faces = {}
        if not os.path.exists(self.known_faces_dir):
            os.makedirs(self.known_faces_dir)
            return known_faces

        print("Loading known faces...")
        for name in os.listdir(self.known_faces_dir):
            person_dir = os.path.join(self.known_faces_dir, name)
            if os.path.isdir(person_dir):
                for filename in os.listdir(person_dir):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                        image_path = os.path.join(person_dir, filename)
                        image = cv2.imread(image_path)
                        if image is not None:
                            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                            faces = self.face_cascade.detectMultiScale(gray_image, 1.3, 5)
                            if len(faces) > 0:
                                x, y, w, h = faces[0]
                                known_faces[name] = gray_image[y:y+h, x:x+w]
                                print(f"Loaded face for: {name}")
                            break # Assume one face per person for simplicity
        return known_faces

    def run(self):
        self.running = True
        while self.running:
            # This is where a more robust recognition logic would go.
            # For this example, we'll just emit a signal for testing.
            # In a real app, you would compare a captured face with known_faces.
            QCoreApplication.processEvents()
            self.msleep(100)

    def detect_and_recognize(self, frame):
        """Detects faces in a frame and attempts to recognize them."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) > 0:
            x, y, w, h = faces[0]
            # Simple "recognition" by checking if a face is detected
            # In a real app, you'd perform a comparison with `known_faces`
            if self.known_faces:
                # This is a placeholder for a more advanced face matching algorithm.
                # For this simple example, we'll just say a face is detected.
                self.face_detected_signal.emit("Anjali") # Simulate recognizing 'Anjali'
                return "Anjali"
            else:
                self.face_detected_signal.emit("Unknown")
                return "Unknown"
        return None

    def stop(self):
        self.running = False


class RobotWindow(QWidget):
    """
    Main application window for the robot.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Amrita Office Robot")
        self.setGeometry(100, 100, 800, 600)
        self.setFixedSize(800, 600)

        # Initialize speech components
        self.tts_engine = pyttsx3.init()
        self.r = sr.Recognizer()

        # Initialize Ollama client
        self.ollama_client = ollama.Client(host='http://localhost:11434')
        self.model = 'llama3' # Change this if you pulled a different model
        self.conversation_history = [
            {"role": "system", "content": "You are an office assistive robot named 'Aadi' at Amrita Vishwa Vidyapeetham, Chennai campus. You are helpful, friendly, and polite. Your primary purpose is to greet visitors and provide information about the campus. Keep your responses concise and to the point. When asked a question, answer it and ask how you can help further."}
        ]

        # Initialize UI
        self.init_ui()

        # Setup video stream
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open webcam.")
            sys.exit()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30) # 30 ms for ~33 FPS

        # Start face recognition worker thread
        self.face_worker = FaceRecognitionWorker()
        self.face_worker.face_detected_signal.connect(self.on_face_detected)
        self.face_worker.start()

    def init_ui(self):
        """Sets up the GUI layout and widgets."""
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()

        # Left side: Camera feed and status
        left_panel = QVBoxLayout()
        self.camera_label = QLabel("Camera Feed")
        self.camera_label.setFixedSize(640, 480)
        self.camera_label.setStyleSheet("border: 2px solid #333; background-color: #000;")
        self.status_label = QLabel("Waiting for a user...")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4CAF50;")
        left_panel.addWidget(self.camera_label)
        left_panel.addWidget(self.status_label)
        top_layout.addLayout(left_panel)

        # Right side: Interaction panel
        right_panel = QVBoxLayout()
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText("The robot's conversation will appear here.")
        self.chat_history.setStyleSheet("font-size: 14px; background-color: #f0f0f0; padding: 10px; border-radius: 8px;")

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Type your message here...")
        self.user_input.returnPressed.connect(self.send_text_message)
        self.user_input.setStyleSheet("font-size: 14px; padding: 8px; border-radius: 8px; border: 1px solid #ccc;")

        button_layout = QHBoxLayout()
        self.listen_button = QPushButton("Speak to Aadi")
        self.listen_button.clicked.connect(self.listen_and_process)
        self.listen_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; border-radius: 8px; font-weight: bold; }"
                                         "QPushButton:hover { background-color: #45a049; }")

        self.register_button = QPushButton("Register Face")
        self.register_button.clicked.connect(self.register_face)
        self.register_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 10px; border-radius: 8px; font-weight: bold; }"
                                           "QPushButton:hover { background-color: #1e87e3; }")

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_text_message)
        self.send_button.setStyleSheet("QPushButton { background-color: #007BFF; color: white; padding: 10px; border-radius: 8px; font-weight: bold; }"
                                       "QPushButton:hover { background-color: #0056b3; }")

        button_layout.addWidget(self.listen_button)
        button_layout.addWidget(self.send_button)
        button_layout.addWidget(self.register_button)

        right_panel.addWidget(self.chat_history)
        right_panel.addWidget(self.user_input)
        right_panel.addLayout(button_layout)
        top_layout.addLayout(right_panel)

        main_layout.addLayout(top_layout)
        self.setLayout(main_layout)

    def update_frame(self):
        """Captures a frame from the webcam and updates the GUI."""
        ret, frame = self.cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)

            # Resize the pixmap to fit the label, maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(self.camera_label.size(), aspectRatioMode=2)
            self.camera_label.setPixmap(scaled_pixmap)

            # This part can be more robust by running face detection in a separate thread for performance
            self.face_worker.detect_and_recognize(frame)

    def on_face_detected(self, name):
        """Slot for the signal emitted by the face recognition worker."""
        if name == "Unknown":
            self.status_label.setText("Hello, I see an unknown person. How can I help you?")
            self.speak("Hello, I see an unknown person. How can I help you?")
        else:
            self.status_label.setText(f"Hello, {name}! Welcome to Amrita Vishwa Vidyapeetham.")
            self.speak(f"Hello, {name}! Welcome to Amrita Vishwa Vidyapeetham.")

    def speak(self, text):
        """Converts text to speech and plays it."""
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"Text-to-speech error: {e}")

    def listen_and_process(self):
        """Listens for user voice input and processes it."""
        self.status_label.setText("Listening...")
        self.speak("Listening...")
        try:
            with sr.Microphone() as source:
                self.r.adjust_for_ambient_noise(source)
                audio = self.r.listen(source, timeout=5, phrase_time_limit=5)
            self.status_label.setText("Recognizing...")
            text = self.r.recognize_google(audio)
            self.add_message_to_chat("You: " + text)
            self.user_input.setText(text)
            self.process_chat(text)
        except sr.UnknownValueError:
            self.status_label.setText("Sorry, could not understand audio.")
            self.speak("Sorry, could not understand audio.")
        except sr.RequestError as e:
            self.status_label.setText(f"Could not request results; {e}")
            self.speak("Sorry, there was a problem with my speech recognition service.")
        except Exception as e:
            self.status_label.setText(f"An unexpected error occurred: {e}")
            self.speak("An unexpected error occurred.")
        finally:
            self.status_label.setText("Ready.")

    def process_chat(self, user_text):
        """Sends the user's message to Ollama and gets a response."""
        self.status_label.setText("Thinking...")
        try:
            self.conversation_history.append({"role": "user", "content": user_text})
            response = self.ollama_client.chat(model=self.model, messages=self.conversation_history)
            ai_response = response['message']['content']
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            self.add_message_to_chat("Aadi: " + ai_response)
            self.speak(ai_response)
        except ollama.OllamaAPIError as e:
            error_message = f"Ollama API Error: {e.error}"
            self.status_label.setText(error_message)
            self.add_message_to_chat("Aadi: " + error_message)
            self.speak("Sorry, there was a problem connecting to my language model.")
        except Exception as e:
            error_message = f"Chat processing error: {e}"
            self.status_label.setText(error_message)
            self.add_message_to_chat("Aadi: " + error_message)
            self.speak("An unexpected error occurred while processing your request.")
        finally:
            self.status_label.setText("Ready.")

    def send_text_message(self):
        """Processes text input from the QLineEdit."""
        user_text = self.user_input.text().strip()
        if user_text:
            self.add_message_to_chat("You: " + user_text)
            self.user_input.clear()
            # Run chat processing in a thread to keep the GUI responsive
            chat_thread = threading.Thread(target=self.process_chat, args=(user_text,))
            chat_thread.start()

    def register_face(self):
        """Captures a frame and registers a new face."""
        name, ok = QLineEdit.getText(self, "Register New User", "Enter name:")
        if ok and name:
            ret, frame = self.cap.read()
            if ret:
                user_dir = os.path.join(self.face_worker.known_faces_dir, name.replace(" ", "_"))
                os.makedirs(user_dir, exist_ok=True)
                file_path = os.path.join(user_dir, f"{name.replace(' ', '_')}.jpg")
                cv2.imwrite(file_path, frame)
                self.face_worker.known_faces = self.face_worker.load_known_faces()
                self.speak(f"Thank you, {name}. Your face has been registered.")
                self.status_label.setText(f"Face of {name} registered successfully.")
            else:
                self.speak("Sorry, I could not capture an image to register your face.")
                self.status_label.setText("Error: Could not capture image.")

    def add_message_to_chat(self, message):
        """Adds a message to the chat history and scrolls to the bottom."""
        self.chat_history.append(message)
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())

    def closeEvent(self, event):
        """Handles application shutdown."""
        self.timer.stop()
        self.cap.release()
        self.face_worker.stop()
        self.face_worker.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RobotWindow()
    window.show()
    sys.exit(app.exec())
