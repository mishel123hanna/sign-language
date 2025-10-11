# Sign Language Translation Application

A real-time sign language translation platform that bridges communication gaps by converting text to sign language videos and interpreting sign language gestures into text.

## 🌟 Overview

This application provides bidirectional translation between text and sign language, enabling seamless communication for the deaf and hard-of-hearing community. Built with FastAPI and leveraging AI models, it offers both text-to-sign and sign-to-text conversion capabilities.

## ✨ Features

### Core Functionality
- **Text-to-Sign Language Video Generation**: Convert written text into sign language video demonstrations
- **Real-time Sign Language Recognition**: Live video processing to interpret sign language gestures into text
- **User Authentication**: Secure authentication system to protect user data and manage sessions
- **Cloud Storage Integration**: Videos stored securely in Supabase with public URL access
- **WebSocket Support**: Real-time bidirectional communication for live sign language interpretation

### Technical Features
- RESTful API architecture
- Real-time video streaming via WebSocket
- AI model integration for sign language processing
- Scalable cloud storage solution

## 🏗️ Architecture

```
┌─────────┐         ┌─────────┐         ┌──────────┐         ┌──────────┐
│ Client  │────────▶│ FastAPI │────────▶│ AI Model │         │ Supabase │
└─────────┘         └─────────┘         └──────────┘         └──────────┘
     │                   │                     │                    │
     │  POST /generate   │                     │                    │
     │  -video           │  Call Model API     │                    │
     │──────────────────▶│────────────────────▶│                    │
     │                   │                     │                    │
     │                   │  Generated Video    │                    │
     │                   │◀────────────────────│                    │
     │                   │                     │                    │
     │                   │  Upload Video       │                    │
     │                   │────────────────────────────────────────▶│
     │                   │                     │                    │
     │                   │  Public URL         │                    │
     │                   │◀────────────────────────────────────────│
     │                   │                     │                    │
     │  Video URL        │                     │                    │
     │◀──────────────────│                     │                    │
     │                   │                     │                    │
```

### Workflow

#### Text-to-Sign Language Video
1. Client sends text via `POST /generate-video`
2. FastAPI forwards text to AI Model
3. AI Model generates sign language video (currently placeholder)
4. FastAPI uploads video to Supabase Storage
5. Supabase returns public URL
6. Client receives video URL

#### Sign Language-to-Text (Live)
1. Client establishes WebSocket connection
2. Client streams live video feed
3. FastAPI processes frames through AI Model in real-time
4. AI Model interprets sign language gestures
5. FastAPI returns translated text via WebSocket
6. Client displays text interpretation live

## 🛠️ Tech Stack

- **Backend Framework**: FastAPI
- **Database & Storage**: Supabase
- **AI/ML**: Custom AI Model (integration ready)
- **Real-time Communication**: WebSocket
- **Authentication**: JWT/OAuth (via Supabase Auth)

## 📋 Prerequisites

- Python 3.8+
- Supabase account and project
- AI model credentials (when implementing full model)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/mishel123hanna/sign-language.git
   cd sign-language
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your credentials:
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   AI_MODEL_API_KEY=your_model_key
   SECRET_KEY=your_secret_key
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Authentication Endpoints
```
POST /auth/signup     - Register new user
POST /auth/login        - Login user
POST /auth/logout       - Logout user
```

### Video Generation Endpoints
```
POST /text-to-sing/generate    - Generate sign language video from text
```

**Request Body:**
```json
{
  "text": "Hello, how are you?"
}
```

**Response:**
```json
{
  "video_url": "string",
  "translation_id": 0,
  "message": "Video uploaded successfully",
  "generation_time_ms": 0
}
```

### WebSocket Endpoints
```
WS /ws/tranlate     - Real-time sign language interpretation
```

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

## 🔮 Future Enhancements

- [ ] Integration with production-ready AI model
- [ ] Support for multiple sign languages (ASL, BSL, ISL, etc.)
- [ ] User profile and history management
- [ ] Mobile application development
- [ ] Offline mode support
- [ ] Advanced gesture recognition
- [ ] Multi-language text support
- [ ] Video quality optimization
- [ ] Performance analytics dashboard

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

Your Name - [@mishel-hanna](https://www.linkedin.com/in/mishel-hanna/)

## 🙏 Acknowledgments

- Sign language community for valuable feedback
- AI/ML researchers advancing gesture recognition technology
- Open source community for tools and libraries

## 📞 Support

For support, email mishelhanna3@gmail.com  .

---

**Note**: This project is currently in development. The AI model integration is in progress, and a default video is used for demonstration purposes.