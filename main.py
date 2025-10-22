#///script
# requires-python=">=3.8"
# dependencies=[
#    "fastapi[standard]",
#    "uvicorn",
#    "requests",
#    "openai"
# ]
#///

import os
import requests
import base64
from fastapi import FastAPI, Request
from openai import OpenAI

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),
                 base_url="https://aipipe.org/openai/v1"
                 )

def validate_secret(secret: str) -> bool:
    # Placeholder for secret validation logic
    expected_secret  = os.getenv("secret") 
    return secret == expected_secret 
#secret =shreya

def write_code_with_llm(prompt: str, round_num: int):
    """Use AI Pipe (LLM) to generate HTML project code."""
    print(f"🧠 Generating code with LLM (Round {round_num})...")
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert web developer. "
                    "Always output valid, complete HTML/CSS/JS code that can run directly in the browser. "
                    "Do NOT include markdown syntax, code fences, or explanations — only pure HTML output."
                )
            },
            {"role": "user", "content": prompt}
        ]
    )
    code = completion.choices[0].message.content.strip()
    return [{"name": "index.html", "content": code}]


def create_git_repo(repo_name: str):
    # use githut to create a repo 
    payload ={"name": repo_name, 
              "private": False,
              "auto_init": True, 
              "license_template": "mit"
              }
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}",
              "Accept": "application/vnd.github+json"
              }
    response = requests.post(
        "https://api.github.com/user/repos", headers={
        "Authorization": f"token {GITHUB_TOKEN}"},
        json=payload
    )
    if response.status_code != 201:
        raise Exception(f"Failed to create repo: {response.status_code}, {response.text}")
    else:
        print(f"✅ Repository '{repo_name}' created successfully.")
        return response.json()


def enable_git_repo(repo_name: str):
    """Enable GitHub Pages for a repository (safe even if already enabled)."""
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "build_type": "legacy",
        "source": {
            "branch": "main",
            "path": "/"
        }
    }

    response = requests.post(
        f"https://api.github.com/repos/23f3000686/{repo_name}/pages",
        headers=headers, json=payload
    )

    if response.status_code in (201, 204):
        print("✅ GitHub Pages enabled successfully!")
    elif response.status_code == 409 and "already enabled" in response.text:
        print("ℹ️ GitHub Pages already enabled — continuing.")
    else:
        raise Exception(f"Failed to enable GitHub Pages: {response.status_code}, {response.text}")
    

def get_sha_of_lastest_commit(repo_name: str, branch:str ="main") -> str:
    """Get SHA of the latest commit on the main branch."""
    url = f"https://api.github.com/repos/23f3000686/{repo_name}/git/refs/heads/main"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data["object"]["sha"]
    elif response.status_code == 404:
        raise Exception(f"❌ Repo or branch not found. Check repo name and branch.\nURL: {url}")
    elif response.status_code == 401:
        raise Exception("❌ Unauthorized. Check if your GitHub token is valid or expired.")
    else:
        raise Exception(f"⚠️ Unexpected error ({response.status_code}): {response.text}")
        
def push_to_git_repo(repo_name: str, files: list[dict], round: int):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    for file in files:
        file_name = file.get("name")
        file_content = file.get("content")

        # Always Base64-encode content
        file_content_encoded = base64.b64encode(file_content.encode("utf-8")).decode("utf-8")

        # 🔍 Check if the file already exists (to get SHA)
        url = f"https://api.github.com/repos/23f3000686/{repo_name}/contents/{file_name}"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            file_sha = response.json()["sha"]
            print(f"Updating existing file {file_name} (sha={file_sha})")
        else:
            file_sha = None
            print(f"Creating new file {file_name}")

        # Prepare payload
        payload = {
            "message": f"Update {file_name}" if file_sha else f"Add {file_name}",
            "content": file_content_encoded
        }
        if file_sha:
            payload["sha"] = file_sha

        # PUT request to create/update file
        put_resp = requests.put(url, headers=headers, json=payload)

        if put_resp.status_code not in (200, 201):
            raise Exception(
                f"Failed to push file {file_name}: "
                f"{put_resp.status_code}, {put_resp.text}"
            )
        else:
            print(f"✅ {file_name} pushed successfully!")


def round_1(data):
    repo_name = f"{data['task']}_{data['nonce']}"
    prompt = f"""
    Create a simple static webpage that matches this project description:

    Task: {data['task']}
    Brief: {data['brief']}

    Output a fully functional HTML page (index.html) — no Markdown or code fences.
    """

    files = write_code_with_llm(prompt, round_num=1)
    files.append({
        "name": "README.md",
        "content": f"# {data['task']}\n\n{data['brief']}"
    })

    create_git_repo(f"{data['task']}_{data['nonce']}")
    enable_git_repo(f"{data['task']}_{data['nonce']}")
    push_to_git_repo(f"{data['task']}_{data['nonce']}", files, 1)
    github_url = f"https://23f3000686.github.io/{repo_name}/"
    print(f"✅ Round 1 deployment done → {github_url}")

    # ✅ Notify evaluation server after deployment
    if eval_url := data.get("evaluation_url"):
        try:
            callback_url = data.get("evaluation_url")
            if callback_url:
                requests.post(callback_url, json={
                "message": "✅ Round 1 task completed",
                "url": github_url
            })
            print(f"📤 Sent completion callback to {callback_url}")
        except Exception as e:
            print(f"⚠️ Evaluation callback failed: {e}")


def round_2(data):
    repo_name = f"{data['task']}_{data['nonce']}"
    prompt = f"""
    Improve and complete the existing web project '{data['task']}'.

    {data['brief']}

    Generate a complete index.html file with improved layout, design, and functionality.
    """
    files = write_code_with_llm(prompt, round_num=2)
    files.append({
        "name": "README.md",
        "content": f"# {data['task']}\n\n{data['brief']}"
    })
    push_to_git_repo(repo_name, files, round=2)
    enable_git_repo(repo_name)
    page_url = f"https://23f3000686.github.io/{repo_name}/"
    print(f"✅ Round 2 completed for {repo_name}")
    github_url = f"https://23f3000686.github.io/{repo_name}/"
    if eval_url := data.get("evaluation_url"):
        try:
            callback_url = data.get("evaluation_url")
            if callback_url:
                requests.post(callback_url, json={
                "message": "✅ Round 1 task completed",
                "url": github_url
            })
            print(f"📤 Sent completion callback to {callback_url}")
        except Exception as e:
            print(f"⚠️ Evaluation callback failed: {e}")
    try:
        response = requests.post(data['evaluation_url'], json={"round": 2})
        print(f"📤 Evaluation notified: {response.status_code}")
        print(f"🌐 View it here: {page_url}\n")
    except Exception as e:
        print(f"⚠️ Evaluation callback failed: {e}")
    


app = FastAPI()

# post endpoint that takes a json object with following email secret task reound breif etc
#check is array evaluation url and  attachment 

from fastapi import BackgroundTasks
@app.post("/handle_task/")
async def handle_task(data: dict, background_tasks: BackgroundTasks):
    if not validate_secret(data.get("secret", "")):
        return {"error": "Invalid secret"}

    task = data.get("task", "")
    round_number = data.get("round")
    brief = data.get("brief", "")
    nonce = data.get("nonce", "")
     # Start background processing
    background_tasks.add_task(process_task, data)
    
    # Check if we already have a completed URL (optional caching logic)
    # e.g., check a database or in-memory dict
    # If task was already completed, return the URL immediately
    completed_tasks = {}  # This could be a global or external store
    repo_name = f"{task}_{nonce}"
    
    if repo_name in completed_tasks:
        # ✅ Task completed → send URL
        return {
            "message": f"✅ Round {round_number} already completed",
            "status": "completed",
            "url": completed_tasks[repo_name]
        }
    else:
        # 🕒 Task not done yet → return processing
        return {
            "message": f"✅ Round {round_number} task accepted",
            "status": "processing",
            "url": None
        }

def process_task(data: dict):
    """Run round logic and callback after completion."""
    round_number = data["round"]
    task = data["task"]
    nonce = data["nonce"]
    repo_name = f"{task}_{nonce}"
    github_url = f"https://23f3000686.github.io/{repo_name}/"

    print(f"🚀 Processing Round {round_number} for {repo_name}")

    try:
        if round_number == 1:
            round_1(data)
        elif round_number == 2:
            round_2(data)
        else:
            print(f"⚠️ Invalid round number: {round_number}")
            return
    except Exception as e:
        print(f"❌ Error during round {round_number}: {e}")
        return

    # ✅ Send callback to client/instructor
    callback_url = data.get("callback_url") or data.get("evaluation_url")

    if callback_url:
        try:
            print(f"📤 Sending completion callback to {callback_url}")
            resp = requests.post(callback_url, json={
                "message": f"✅ Round {round_number} task completed",
                "url": github_url
            }, timeout=10)
            print(f"📬 Callback response: {resp.status_code}")
        except Exception as e:
            print(f"⚠️ Callback failed: {e}")

@app.post("/send_task/")
async def receive_callback(request: Request):
    data = await request.json()
    round_number = data["round"]
    task = data["task"]
    nonce = data["nonce"]
    repo_name = f"{task}_{nonce}"
    github_url = f"https://23f3000686.github.io/{repo_name}/"

    print("📬 Callback received:", data)
    return {"status": "✅ Callback received successfully", "round":round_number, "url":github_url}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
