# EduMate
Edumate is a fully offline, privacy-preserving document intelligence platform designed to help students to efficiently understand large textual documents. The system allows users to upload a document once and generate concise summaries, key concepts, multilingual outputs, flashcards, and semantic insights without requiring an internet connection.

# For Offline Execution
Due to large pretrained NLP models(5-10GB),models are not tracked in this repository.
For offline execution , models are downloaded once andmounted into docker container as a image.

# 🚀Features

->Offline document summarization (Transformer-based)
->Multilingual translation (English ↔ Telugu and others)
->TXT,PDF & DOCX support
->Dockerized deployment for portability
->Privacy-first, zero-internet execution

# 🛠Tech Stack

->Python, Flask
->Hugging Face Transformers
->PyTorch (CPU)
->Docker

# 📦 Models

Models are downloaded once and stored locally. They are mounted into the container for fully offline execution.

# 📂 Project Structure

Edumate/
├── app.py
├── Dockerfile
├── requirements.txt
├── README.md
├── templates/
├── static/
├── models/        # Local models directory (not tracked in GitHub)
└── uploads/

# 🪜 Push the image from DockerHub & Follow the below steps

1️⃣ Build the Docker image

docker build -t edumate .

2️⃣ Run the container

docker run -d -p 5000:5000 edumate

3️⃣ Access the application

Open your browser and go to:

 # http://localhost:5000
