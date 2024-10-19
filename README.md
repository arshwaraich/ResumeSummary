# ResumeSummary
 An api to write resume summary based on resume data and job description, using llama3.1 API

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
# Download PDF directly
curl -X POST \
  http://localhost:8000/generate-resume \
  -H "Content-Type: application/json" \
  -d '{
    "job_url": "https://job-boards.greenhouse.io/faire/jobs/7585808002?gh_jid=7585808002"
  }' \
  --output resume.pdf

# Get only the summary text
curl -X POST \
  http://localhost:8000/generate-summary \
  -H "Content-Type: application/json" \
  -d '{
    "job_url": "https://job-boards.greenhouse.io/faire/jobs/7585808002?gh_jid=7585808002"
  }'
```