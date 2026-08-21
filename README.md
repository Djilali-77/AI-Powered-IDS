# 🛡️ AI-Powered Intrusion Detection System (IDS)

An intelligent, full-stack Network Intrusion Detection System based on Deep Learning (Autoencoder). This system monitors network traffic features and detects anomalies (Zero-day attacks) by calculating reconstruction errors in real-time.

## 🚀 Features

- **Deep Learning Model:** Unsupervised Autoencoder built with TensorFlow/Keras to detect anomalous network patterns.
- **Fast Backend API:** High-performance RESTful API built with FastAPI.
- **Interactive Modern UI:** Responsive, animated frontend built with React, Vite, Tailwind CSS, and Framer Motion.
- **Dockerized Infrastructure:** Fully containerized using Docker and Docker Compose for seamless deployment across any environment.
- **Real-time Simulation:** Simulate both Normal Traffic (Benign) and Cyber Attacks directly from the UI.

## 🛠️ Tech Stack

**Front-end:**
- React (Vite)
- Tailwind CSS
- Framer Motion
- Axios

**Back-end & AI:**
- Python 3.10
- FastAPI & Uvicorn
- TensorFlow / Keras
- Scikit-learn & NumPy
- Weights & Biases (W&B) for model tracking

## 📁 Project Structure

    AI-Powered-IDS/
    ├── back-end/
    │   ├── main.py                  # FastAPI server and prediction logic
    │   ├── autoencoder.weights.h5   # Trained model weights
    │   ├── requirements.txt         # Python dependencies
    │   └── Dockerfile               # Backend container configuration
    ├── front-end/
    │   ├── src/                     # React components and assets
    │   ├── package.json             # Node.js dependencies
    │   ├── vite.config.js           # Vite configuration
    │   └── Dockerfile               # Frontend container (Nginx) configuration
    ├── train_model.py               # Deep Learning model training script
    └── docker-compose.yml           # Multi-container orchestration

## ⚙️ Quick Start (Running Locally)

### Prerequisites
Make sure you have [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) installed on your machine.

### 1. Clone the repository
    git clone https://github.com/YOUR_USERNAME/AI-Powered-IDS.git
    cd AI-Powered-IDS

### 2. Build and run with Docker Compose
Simply run the following command in the root directory:
    docker compose up --build

### 3. Access the Application
Once the containers are successfully running, you can access the services at:
- **Frontend UI:** http://localhost:3000
- **Backend API Docs (Swagger):** http://localhost:8000/docs

## 🧠 How it Works

1. The frontend sends simulated network packet features (78 dimensions) to the FastAPI backend.
2. The Autoencoder attempts to reconstruct the input data.
3. The **Reconstruction Error** is calculated (Mean Squared Error).
4. If the error exceeds the predefined **Threshold**, the traffic is flagged as an **Attack 🚨**. Otherwise, it is classified as **Normal Traffic ✅**.

## 🛑 Stopping the Application
To stop the running containers, simply press CTRL+C in your terminal, or run:
    docker compose down

## 👨‍💻 Author

Developed by **Djilali** - Cybersecurity & AI Enthusiast.
