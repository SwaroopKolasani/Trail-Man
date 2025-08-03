#!/bin/bash

echo "🚀 Trail-Man Setup Script"
echo "=========================="

# Check if we're in the correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Please run this script from the Trail-Man root directory"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

if ! command_exists python3; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

echo "✅ All prerequisites found!"

# Setup backend environment
echo "🔧 Setting up backend environment..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating backend .env file..."
    cat > .env << 'EOF'
# Database Configuration
MYSQL_SERVER=localhost
MYSQL_USER=root
MYSQL_PASSWORD=0428@nani
MYSQL_DB=trail_man_db

# Clerk Authentication (Replace with your actual keys)
CLERK_SECRET_KEY=your_clerk_secret_key_here
CLERK_PUBLIC_KEY=your_clerk_public_key_here

# AWS Configuration (Optional)
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_S3_BUCKET=trail-man-resumes

# Application Settings
PROJECT_NAME=Trail-Man
VERSION=1.0.0
API_V1_STR=/api/v1
EOF
    echo "⚠️  Please update the Clerk keys in backend/.env file"
fi

cd ..

# Setup frontend environment
echo "🔧 Setting up frontend environment..."
cd frontend

echo "Installing frontend dependencies..."
npm install

# Create .env.local file if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "Creating frontend .env.local file..."
    cat > .env.local << 'EOF'
# Clerk Authentication (Replace with your actual keys)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key_here
CLERK_SECRET_KEY=your_clerk_secret_key_here

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
EOF
    echo "⚠️  Please update the Clerk keys in frontend/.env.local file"
fi

cd ..

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📚 Next Steps:"
echo "1. Sign up for Clerk at https://clerk.dev and get your API keys"
echo "2. Update the Clerk keys in:"
echo "   - backend/.env"
echo "   - frontend/.env.local"
echo "3. Start the application with one of these options:"
echo ""
echo "   Option A - Using Docker (Recommended):"
echo "   docker-compose up --build"
echo ""
echo "   Option B - Manual setup:"
echo "   • Start MySQL (or use Docker: docker run -p 3307:3306 -e MYSQL_ROOT_PASSWORD=0428@nani -e MYSQL_DATABASE=trail_man_db mysql:8.0)"
echo "   • Import database: mysql -u root -p trail_man_db < Trail_Man_db.sql"
echo "   • Add sample data: mysql -u root -p trail_man_db < sample_data.sql"
echo "   • Start backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "   • Start frontend: cd frontend && npm run dev"
echo ""
echo "4. Open http://localhost:3000 in your browser"
echo ""
echo "📖 For detailed instructions, see README.md"
echo ""
echo "🐛 Need help? Check the documentation or create an issue!" 