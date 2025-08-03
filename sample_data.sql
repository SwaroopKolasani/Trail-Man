-- Sample job data for Trail-Man application
USE trail_man_db;

-- Insert sample jobs
INSERT INTO jobs (title, company, location, description, requirements, salary_range, job_type, remote_type, external_url, posted_date) VALUES
('Senior Software Engineer', 'TechCorp', 'San Francisco, CA', 'We are looking for a senior software engineer to join our growing team. You will be responsible for developing scalable web applications and mentoring junior developers.', 'Bachelor''s degree in Computer Science, 5+ years of experience with React, Node.js, and Python. Experience with cloud platforms preferred.', '$120,000 - $150,000', 'full-time', 'hybrid', 'https://techcorp.com/careers/senior-software-engineer', '2024-01-15 10:00:00'),

('Frontend Developer', 'StartupXYZ', 'New York, NY', 'Join our innovative startup as a frontend developer. Build beautiful and responsive user interfaces using modern web technologies.', 'Experience with React, TypeScript, and CSS frameworks. Portfolio of previous work required.', '$80,000 - $100,000', 'full-time', 'remote', 'https://startupxyz.com/jobs/frontend-developer', '2024-01-14 09:30:00'),

('Full Stack Developer', 'InnovateLabs', 'Austin, TX', 'Looking for a versatile full stack developer to work on exciting projects. You''ll work with both frontend and backend technologies in an agile environment.', 'Proficiency in JavaScript, Python, SQL databases, and REST APIs. 3+ years of full stack development experience.', '$90,000 - $110,000', 'full-time', 'onsite', 'https://innovatelabs.io/careers/fullstack', '2024-01-13 14:20:00'),

('Python Developer Intern', 'DataSoft', 'Seattle, WA', 'Summer internship opportunity for aspiring Python developers. Work on real-world projects and learn from experienced mentors.', 'Currently pursuing Computer Science degree, basic knowledge of Python and databases.', '$25 - $30 per hour', 'internship', 'hybrid', 'https://datasoft.com/internships/python-developer', '2024-01-12 11:45:00'),

('DevOps Engineer', 'CloudTech', 'Remote', 'We need a DevOps engineer to help streamline our deployment processes and maintain our cloud infrastructure.', 'Experience with AWS/Azure, Docker, Kubernetes, CI/CD pipelines. Linux administration skills required.', '$100,000 - $130,000', 'full-time', 'remote', 'https://cloudtech.com/jobs/devops-engineer', '2024-01-11 16:10:00'),

('UI/UX Designer', 'DesignStudio', 'Los Angeles, CA', 'Creative UI/UX designer needed to craft beautiful and intuitive user experiences for web and mobile applications.', 'Proficiency in Figma, Adobe Creative Suite, user research methodologies. Portfolio showcasing mobile and web designs.', '$70,000 - $95,000', 'full-time', 'hybrid', 'https://designstudio.com/careers/ui-ux-designer', '2024-01-10 13:25:00'),

('Backend Developer', 'ScaleTech', 'Chicago, IL', 'Join our backend team to build robust and scalable APIs. Work with microservices architecture and handle high-traffic applications.', 'Strong experience with Node.js, Python, or Java. Database design and optimization skills. Experience with microservices.', '$95,000 - $125,000', 'full-time', 'hybrid', 'https://scaletech.com/jobs/backend-developer', '2024-01-09 10:15:00'),

('Data Scientist', 'AnalyticsPro', 'Boston, MA', 'Data scientist position focusing on machine learning and predictive analytics. Work with large datasets to drive business insights.', 'PhD or Masters in Data Science, Statistics, or related field. Experience with Python, R, SQL, and ML frameworks.', '$110,000 - $140,000', 'full-time', 'remote', 'https://analyticspro.com/careers/data-scientist', '2024-01-08 12:40:00'),

('React Developer', 'WebFlow Inc', 'Portland, OR', 'Frontend specialist needed to build modern React applications. Join a team that values clean code and user experience.', '3+ years of React experience, familiarity with Redux, testing frameworks, and modern build tools.', '$85,000 - $105,000', 'full-time', 'remote', 'https://webflowinc.com/jobs/react-developer', '2024-01-07 15:30:00'),

('Software Engineer Contractor', 'TechConsulting', 'Various Locations', 'Contract position for experienced software engineers. Work on diverse projects across different industries and technologies.', 'Bachelor''s degree in Computer Science or equivalent experience. Flexibility to work with various tech stacks.', '$65 - $85 per hour', 'contract', 'remote', 'https://techconsulting.com/contractors/software-engineer', '2024-01-06 08:50:00'),

('Mobile App Developer', 'AppMakers', 'San Diego, CA', 'Develop cutting-edge mobile applications for iOS and Android platforms. Work with cross-functional teams to deliver amazing user experiences.', 'Experience with React Native or Flutter, native iOS/Android development knowledge preferred.', '$90,000 - $115,000', 'full-time', 'onsite', 'https://appmakers.com/careers/mobile-developer', '2024-01-05 11:20:00'),

('QA Engineer', 'QualityFirst', 'Phoenix, AZ', 'Quality assurance engineer to develop and execute test plans, identify bugs, and ensure software quality across our products.', 'Experience with automated testing tools, manual testing, and bug tracking systems. ISTQB certification preferred.', '$75,000 - $95,000', 'full-time', 'hybrid', 'https://qualityfirst.com/jobs/qa-engineer', '2024-01-04 14:05:00'),

('Machine Learning Engineer', 'AI Innovations', 'Denver, CO', 'ML engineer to design and implement machine learning models for production systems. Work on cutting-edge AI projects.', 'Masters in Machine Learning, Computer Science, or related field. Experience with TensorFlow, PyTorch, and MLOps.', '$115,000 - $145,000', 'full-time', 'remote', 'https://aiinnovations.com/careers/ml-engineer', '2024-01-03 09:15:00'),

('Part-time Web Developer', 'LocalBusiness', 'Miami, FL', 'Part-time web developer to maintain and update company websites. Perfect for someone looking for flexible work arrangements.', 'HTML, CSS, JavaScript, WordPress experience. Previous freelance or part-time development experience preferred.', '$30 - $40 per hour', 'part-time', 'hybrid', 'https://localbusiness.com/jobs/web-developer-pt', '2024-01-02 16:45:00'),

('Technical Lead', 'Enterprise Solutions', 'Dallas, TX', 'Technical leadership role overseeing a team of developers. Guide technical decisions and mentor team members while contributing to code.', '7+ years of software development experience, 2+ years in leadership roles. Strong communication and technical skills.', '$130,000 - $160,000', 'full-time', 'onsite', 'https://enterprisesolutions.com/careers/tech-lead', '2024-01-01 10:30:00'); 