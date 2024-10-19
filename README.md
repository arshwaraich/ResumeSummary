# ResumeSummary
 An api to write resume summary based on resume data and job description

## Requirements:

1. Receive job posting URL as POST request
2. Parse the job posting URL into text
3. Pull LaTeX resume from Github
4. Generate resume summary based on resume data and job description, using llama3.1 API
5. Insert resume summary into LaTeX template
6. Return resume summary as a PDF file (created from Latex template)


## Test data

Test URL: https://job-boards.greenhouse.io/faire/jobs/7585808002?gh_jid=7585808002

LaTex Resume link: https://github.com/arshwaraich/Resume/blob/master/LaTeX/resume.tex

## Usage

```bash
# Basic curl request
curl -X POST \
  http://localhost:8000/generate-resume \
  -H "Content-Type: application/json" \
  -d '{
    "job_url": "https://www.example.com/job-posting",
    "github_token": "ghp_your_github_personal_access_token",
    "github_repo": "username/resume-repo",
    "latex_path": "resume.tex",
    "ollama_host": "http://localhost:11434"
  }'

# Save response to file (includes both summary text and PDF)
curl -X POST \
  http://localhost:8000/generate-resume \
  -H "Content-Type: application/json" \
  -d '{
    "job_url": "https://www.example.com/job-posting",
    "github_token": "ghp_your_github_personal_access_token",
    "github_repo": "username/resume-repo",
    "latex_path": "resume.tex",
    "ollama_host": "http://localhost:11434"
  }' \
  -o response.json

# Extract and save just the PDF from the response
curl -X POST \
  http://localhost:8000/generate-resume \
  -H "Content-Type: application/json" \
  -d '{
    "job_url": "https://www.example.com/job-posting",
    "github_token": "ghp_your_github_personal_access_token",
    "github_repo": "username/resume-repo",
    "latex_path": "resume.tex",
    "ollama_host": "http://localhost:11434"
  }' \
  | jq -r .pdf_base64 | base64 -d > resume.pdf

# Extract and save just the summary text
curl -X POST \
  http://localhost:8000/generate-resume \
  -H "Content-Type: application/json" \
  -d '{
    "job_url": "https://www.example.com/job-posting",
    "github_token": "ghp_your_github_personal_access_token",
    "github_repo": "username/resume-repo",
    "latex_path": "resume.tex",
    "ollama_host": "http://localhost:11434"
  }' \
  | jq -r .summary_text > summary.txt
```