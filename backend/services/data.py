from __future__ import annotations

SKILL_ALIASES: dict[str, list[str]] = {
    "Python": ["python", "pandas", "numpy", "scikit-learn", "sklearn"],
    "SQL": ["sql", "postgres", "postgresql", "mysql", "sqlite"],
    "React": ["react", "reactjs", "next.js", "nextjs"],
    "FastAPI": ["fastapi", "pydantic", "starlette", "uvicorn"],
    "Docker": ["docker", "container", "containers", "dockerfile"],
    "AWS": ["aws", "s3", "ec2", "lambda"],
    "TensorFlow": ["tensorflow", "keras", "deep learning"],
    "LangChain": ["langchain", "langgraph"],
    "LLM/RAG": [
        "llm",
        "rag",
        "retrieval augmented generation",
        "large language model",
        "prompt engineering",
        "vector search",
        "generative ai",
        "genai",
    ],
    "ChromaDB": ["chromadb", "chroma", "vector database", "vector db"],
    "Git": ["git", "github", "version control"],
    "JavaScript": ["javascript", "js", "node", "node.js"],
    "TypeScript": ["typescript", "ts"],
    "PostgreSQL": ["postgresql", "postgres"],
    "Machine Learning": ["machine learning", "ml", "model training"],
    "Communication": ["communication", "stakeholder", "presentation", "documentation"],
}

ROLE_PROFILES = {
    "Data Scientist": {
        "summary": "Data Scientist with a track record of turning messy data into clear decisions using Python, SQL, statistics, and model development.",
        "projects": [
            "Built a churn prediction pipeline with feature engineering, model selection, and explainability reporting.",
            "Created a resume intelligence dashboard that matched candidate profiles to job requirements with semantic search.",
        ],
        "skills": ["Python", "SQL", "Machine Learning", "TensorFlow", "Communication"],
    },
    "Frontend Engineer": {
        "summary": "Frontend Engineer focused on responsive interfaces, design systems, and product-minded implementation with React and TypeScript.",
        "projects": [
            "Built an ATS dashboard with polished role-based flows, reusable components, and responsive data cards.",
            "Implemented a recruiter analytics UI with filters, charts, and workflow-specific call to actions.",
        ],
        "skills": ["React", "TypeScript", "JavaScript", "Git", "Communication"],
    },
    "AI Engineer": {
        "summary": "AI Engineer who ships practical retrieval and generation systems, pairing clean backend workflows with model-aware product features.",
        "projects": [
            "Built a resume-to-job matching engine with keyword extraction, semantic scoring, and explanation outputs.",
            "Created an interview prep assistant that generates role-aware questions from resumes and job descriptions.",
        ],
        "skills": ["Python", "FastAPI", "LangChain", "ChromaDB", "AWS"],
    },
    "Backend Engineer": {
        "summary": "Backend Engineer with experience designing APIs, workflow automation, and data-centric services that stay easy to maintain.",
        "projects": [
            "Built a screening API that scores resumes, ranks candidates, and surfaces hiring recommendations.",
            "Designed a job description parser and assessment generator with clean request and response contracts.",
        ],
        "skills": ["FastAPI", "Python", "SQL", "Docker", "PostgreSQL"],
    },
}

SAMPLE_CANDIDATES = [
    {
        "name": "John",
        "ats": 91,
        "skill_match": 88,
        "projects": "Excellent",
        "experience": "Relevant",
        "education": "Good",
        "recommendation": "Strong Hire",
        "college": "University of Adelaide",
    },
    {
        "name": "Aisha",
        "ats": 90,
        "skill_match": 85,
        "projects": "Very Strong",
        "experience": "Relevant",
        "education": "Good",
        "recommendation": "Strong Hire",
        "college": "Monash University",
    },
    {
        "name": "Marcus",
        "ats": 86,
        "skill_match": 82,
        "projects": "Strong",
        "experience": "Solid",
        "education": "Good",
        "recommendation": "Hire",
        "college": "University of Melbourne",
    },
    {
        "name": "Nina",
        "ats": 81,
        "skill_match": 77,
        "projects": "Good",
        "experience": "Moderate",
        "education": "Good",
        "recommendation": "Interview",
        "college": "UNSW",
    },
]

PIPELINE_COUNTS = {"total": 327, "shortlisted": 58, "rejected": 190, "pending": 79}

