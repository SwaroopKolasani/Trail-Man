<<<<<<< HEAD
# Trail-Man: AI-Powered Job Application Tracker

Trail-Man is a comprehensive job application tracking system built with Next.js, FastAPI, and MySQL. It helps job seekers organize their applications, manage resumes, and track their job search progress.

## Features

- 🔍 **Job Discovery**: Browse and search job opportunities with advanced filtering
- 👤 **Profile Management**: Create and manage your professional profile
- 📄 **Resume Management**: Upload PDFs and integrate with Overleaf for LaTeX resumes
- 📊 **Application Tracking**: Track application status from submission to decision
- 🔐 **Secure Authentication**: Powered by Clerk authentication

## Tech Stack

### Frontend
- Next.js 15 with TypeScript
- Tailwind CSS for styling
- Clerk for authentication
- Axios for API communication
- React Query for state management

### Backend
- FastAPI with Python
- SQLAlchemy ORM
- MySQL database
- Pydantic for data validation
- Clerk for authentication

## Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- MySQL 8.0+
- Docker and Docker Compose (optional)

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
git clone <repository-url>
cd Trail-Man
./setup.sh
```

The setup script will:
- Check prerequisites
- Set up Python virtual environment
- Install all dependencies
- Create environment files with templates
- Provide next steps

### Option 2: Manual Setup

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd Trail-Man
```

#### 2. Set Up Clerk Authentication

Before running the application, you need Clerk API keys:

1. Create an account at [Clerk.dev](https://clerk.dev)
2. Create a new application
3. Copy your publishable key and secret key
4. Configure the URLs in Clerk dashboard:
   - Sign-in URL: `/sign-in`
   - Sign-up URL: `/sign-up`
   - After sign-in URL: `/jobs`
   - After sign-up URL: `/jobs`

#### 3. Database Setup

Create a MySQL database:

```sql
CREATE DATABASE trail_man_db;
```

Import the database schema:

```bash
mysql -u root -p trail_man_db < Trail_Man_db.sql
```

Add sample job data (optional):

```bash
mysql -u root -p trail_man_db < sample_data.sql
```

#### 4. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cat > .env << EOF
MYSQL_SERVER=localhost
MYSQL_USER=root
MYSQL_PASSWORD=0428@nani
MYSQL_DB=trail_man_db

CLERK_SECRET_KEY=your_clerk_secret_key_here
CLERK_PUBLIC_KEY=your_clerk_public_key_here

AWS_ACCESS_KEY_ID=your_aws_key_optional
AWS_SECRET_ACCESS_KEY=your_aws_secret_optional
AWS_S3_BUCKET=trail-man-resumes

PROJECT_NAME=Trail-Man
VERSION=1.0.0
API_V1_STR=/api/v1
EOF

# Run the backend
uvicorn app.main:app --reload
```

#### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cat > .env.local << EOF
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key_here
CLERK_SECRET_KEY=your_clerk_secret_key_here
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
EOF

# Run the frontend
npm run dev
```

#### 6. Access the Application

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Docker Deployment

For easy deployment using Docker:

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# Stop services
docker-compose down
```

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

## Project Structure

```
Trail-Man/
├── frontend/                 # Next.js application
│   ├── src/app/
│   │   ├── (auth)/          # Authentication pages
│   │   ├── (dashboard)/     # Dashboard pages
│   │   └── page.tsx         # Landing page
│   ├── lib/                 # Utility functions
│   └── middleware.ts        # Authentication middleware
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration
│   │   ├── db/             # Database setup
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── main.py         # Application entry point
│   └── requirements.txt
├── Trail_Man_db.sql        # Database schema
└── docker-compose.yml     # Docker configuration
```

## Key Features Implementation

### Authentication
- Clerk integration for secure user authentication
- Automatic user creation on first sign-in
- Protected routes with middleware

### Job Management
- Search and filter job listings
- Apply to jobs with one click
- External job site integration

### Resume Management
- PDF upload functionality
- Primary resume designation
- Overleaf integration for LaTeX resumes

### Application Tracking
- Status tracking (Applied, Screening, Interview, Rejected, Accepted)
- Application history and analytics
- Status update notifications

## Environment Variables

### Frontend (.env.local)
```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Backend (.env)
```
MYSQL_SERVER=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=trail_man_db
CLERK_SECRET_KEY=sk_...
CLERK_PUBLIC_KEY=pk_...
AWS_ACCESS_KEY_ID=optional
AWS_SECRET_ACCESS_KEY=optional
AWS_S3_BUCKET=optional
```

## Development

### Adding New Features

1. **API Endpoints**: Add to `backend/app/api/api_v1/endpoints/`
2. **Database Models**: Update `backend/app/models/`
3. **Frontend Pages**: Add to `frontend/src/app/`
4. **Components**: Create reusable components in `frontend/src/components/`

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Production Deployment

### Backend
1. Set up production database
2. Configure environment variables
3. Use a production WSGI server like Gunicorn
4. Set up reverse proxy with Nginx

### Frontend
1. Build the application: `npm run build`
2. Deploy to Vercel, Netlify, or your preferred platform
3. Configure environment variables in your deployment platform

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Check the documentation at `/docs` endpoint
- Review the API documentation at `/docs`

## Roadmap

- [ ] AI-powered job recommendations
- [ ] Resume analysis and optimization
- [ ] Interview scheduling integration
- [ ] Email notifications
- [ ] Mobile application
- [ ] Analytics dashboard
- [ ] Team collaboration features 
=======

>>>>>>> origin/main
