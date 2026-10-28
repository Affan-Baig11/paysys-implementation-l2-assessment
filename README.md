# Paysys Labs – Implementation & L2 Support Engineer Technical Assessment

**Time window:** Submit within 48 hours of receiving the assessment.  
**Expected hands-on effort:** Approximately 6–10 hours.  
**Submission:** Public GitHub repository.

## Objective
This assessment evaluates practical ability to implement, operate, troubleshoot, test, and automate support for a small enterprise-style application. We value investigation, engineering judgement, automation, documentation, and effective use of AI more than memorized commands.

## Scenario
You are joining an implementation/L2 support team responsible for **MiniPay**, a small payment-processing application. It consists of a web UI, REST services, and a relational database. Your assignment is to deploy and operate the environment, demonstrate database and web-service proficiency, automate testing, build a support utility, and investigate production-style incidents.

## Skills assessed
1. Linux
2. Git
3. SQL
4. Kubernetes
5. Rancher
6. Python utilities/automation
7. Web services
8. API test automation
9. GUI test automation
10. L2 troubleshooting and documentation
11. Effective and responsible use of AI tools

Read `INSTRUCTIONS.md` before starting. The files under `requirements/` define the tasks. The `incidents/` folder contains support incidents to investigate.

## L2 support CLI

Install the CLI dependency with `python -m pip install -r python/requirements.txt`. With the API running, diagnose a transaction using `python python/support_tool.py --transaction TXN000123`; add `--json` for machine-readable output or use `--health` for API/database health. Set `MINIPAY_API_URL`, optional `MINIPAY_API_KEY`, and `MINIPAY_TIMEOUT` through the environment. Run unit tests with `python -m pytest -q tests/python` after installing `tests/python/requirements.txt`.

## Git workflow and release

Work was developed incrementally on `work/linux-git`, branched from the starter `main`, with separate commits for the API/tests and subsequent assessment components. The work branch has been pushed to the public GitHub repository for review. After the final documentation/evidence commit is reviewed, tag that final commit `submission-v1.0` and push the tag to GitHub.


