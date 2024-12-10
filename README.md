# Digital Customer Onboarding System

## Overview
This project is designed to streamline the onboarding process for banking sectors by providing a digital, secure, and efficient customer registration system. It leverages advanced verification technologies to ensure the authenticity and accuracy of customer information.

## Key Features
- **Document Upload**: Users can upload ID cards and other necessary documents for verification.
- **OCR Processing**: Utilizes Claude 3.5 Sonnet for extracting information from uploaded documents.
- **ID Verification**: Cross-references with the National Identification Authority Database.
- **Compliance Checks**: Includes AML (Anti-Money Laundering) and Credit Bureau checks.
- **Biometric Verification**: Employs Azure AI for liveness detection and AWS Rekognition for face verification.
- **User Registration**: Allows users to confirm their details and set a password for account creation.

## Technologies Used
- **FastAPI**: For building the web application and API endpoints.
- **Azure Cognitive Services**: For liveness detection.
- **AWS Rekognition**: For facial comparison and verification.
- **Claude 3.5 Sonnet**: For OCR and document information extraction.
- **SQLAlchemy**: For database interactions.

## Project Structure
- `Customer/`: Contains services, API routes, and DTOs related to customer operations.
- `auth/`: Handles authentication and authorization services.
- `persistence/`: Manages database models and repositories.
- `bootstrap/`: Includes the dependency injection container setup.
- `Library/`: Utility functions and common libraries.

## Installation
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Onboarding-Temp
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   - Copy `.env.example` to `.env.dev` and fill in the required API keys and database configurations.

5. **Run the application**
   ```bash
   uvicorn main:app --reload
   ```

## Usage
- Access the application at `http://localhost:8000`
- Use the API documentation at `http://localhost:8000/docs` for testing endpoints.



