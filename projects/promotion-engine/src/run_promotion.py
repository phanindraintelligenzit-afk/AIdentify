"""Promotion Engine Runner — orchestrates full promotion pipeline for AIdentify projects."""
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "image-pipeline" / "src"))

from promoter import (
    generate_posts, schedule_post, _ist_to_utc,
    OCoYA_BASE, OCoYA_KEY, OCoYA_WORKSPACE, PROFILE_IDS, MARKETPLACE_URL,
    IST
)
from image_gen import generate_all_platforms
from github_uploader import upload_image

# Tracking file
POSTED_TRACKING = Path(__file__).resolve().parent / "output" / "posted_projects.json"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

def load_projects():
    projects_file = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "data" / "projects.json"
    with open(projects_file) as f:
        data = json.load(f)
    return data.get("projects", [])

def load_posted():
    if POSTED_TRACKING.exists():
        with open(POSTED_TRACKING) as f:
            return json.load(f)
    return {"posted": [], "last_run": None}

def save_posted(data):
    data["last_run"] = datetime.now(IST).isoformat()
    with open(POSTED_TRACKING, "w") as f:
        json.dump(data, f, indent=2)

def get_agents_for_project(project):
    tags = project.get("tags", [])
    agents = []
    for tag in tags:
        if "Agent" in tag or "agent" in tag:
            agents.append(tag)
    category = project.get("category", "marketing")
    if not agents:
        if category == "healthcare":
            agents = ["Patient Data Extractor", "Insurance Checker", "Risk Assessor", "Package Generator"]
        elif category == "realestate":
            agents = ["Market Scout", "Lead Qualifier", "Prospect Scorer", "Outreach Generator"]
        elif category == "ecommerce":
            agents = ["Product Analyzer", "Competitor Researcher", "Listing Optimizer", "Review Manager"]
        elif category == "legal":
            agents = ["Contract Parser", "Redline Identifier", "Risk Assessor", "Negotiation Summarizer"]
        elif category == "hr":
            agents = ["Resume Screener", "Candidate Scorer", "Outreach Writer", "Onboarding Generator"]
        elif category == "marketing":
            agents = ["Prospector", "Contact Finder", "Outreach Drafter", "Lead Scorer"]
        elif category == "security":
            agents = ["Policy Enforcer", "Sandbox Executor", "Audit Logger"]
        else:
            agents = ["Researcher", "Builder", "Tester", "Deployer"]
    return agents

def generate_images_for_project(project_name, description):
    print(f"  Generating images for: {project_name}")
    image_paths = generate_all_platforms(project_name, description)
    image_urls = {}
    for platform, local_path in image_paths.items():
        try:
            url = upload_image(local_path)
            image_urls[platform] = url
            print(f"    {platform}: {url}")
        except Exception as e:
            print(f"    {platform} upload failed: {e}")
            image_urls[platform] = None
    return image_urls

def schedule_project_posts(project, image_urls):
    name = project["name"]
    desc = project.get("description", "")
    github_url = project.get("github_url", "")
    category = project.get("category", "AI")
    agents = get_agents_for_project(project)
    
    print(f"\nScheduling posts for: {name}")
    
    posts = generate_posts({
        "name": name,
        "description": desc,
        "github_url": github_url,
        "category": category,
        "agents": agents,
    })
    
    results = {}
    schedule = [
        ("linkedin", posts["linkedin"], "08:00", image_urls.get("linkedin")),
        ("twitter", "\n\n".join(posts["twitter"]), "09:00", image_urls.get("twitter")),
        ("instagram", posts["instagram"], "10:00", image_urls.get("instagram")),
        ("facebook", posts["facebook"], "11:00", image_urls.get("facebook")),
    ]
    
    for platform, content, time_ist, media_url in schedule:
        if platform == "instagram" and not media_url:
            print(f"  {platform}: Skipped (no image available)")
            results[platform] = {"status": "skipped", "reason": "no_image"}
            continue
            
        print(f"  {platform} at {time_ist} IST...")
        result = schedule_post(platform, content, time_ist, media_url=media_url, project_name=name)
        
        if "error" in result:
            print(f"    Failed: {result['error']}")
            results[platform] = {"status": "error", "error": result['error']}
        else:
            post_id = result.get("postGroupId", "unknown")
            print(f"    Scheduled: {post_id}")
            results[platform] = {"status": "scheduled", "post_id": post_id}
    
    return results

def main():
    print("=" * 60)
    print("AIdentify Promotion Engine - Auto-Scheduler")
    print("=" * 60)
    
    projects = load_projects()
    posted_data = load_posted()
    posted_ids = set(posted_data.get("posted", []))
    
    print(f"\nFound {len(projects)} projects in marketplace")
    print(f"Already posted: {len(posted_ids)}")
    
    unposted = [p for p in projects if p["id"] not in posted_ids]
    print(f"Unposted projects: {len(unposted)}")
    
    if not unposted:
        print("\nAll projects already posted!")
        return
    
    all_results = {}
    for project in unposted:
        name = project["name"]
        project_id = project["id"]
        
        print(f"\n{'='*60}")
        print(f"Processing: {name} ({project_id})")
        print(f"{'='*60}")
        
        try:
            image_urls = generate_images_for_project(name, project.get("description", ""))
            results = schedule_project_posts(project, image_urls)
            
            all_results[project_id] = {
                "name": name,
                "results": results,
                "image_urls": image_urls,
            }
            
            posted_ids.add(project_id)
            posted_data["posted"] = list(posted_ids)
            save_posted(posted_data)
            
            print(f"\nCompleted: {name}")
            
        except Exception as e:
            print(f"\nFailed for {name}: {e}")
            all_results[project_id] = {"name": name, "error": str(e)}
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for project_id, data in all_results.items():
        print(f"\n{data['name']} ({project_id})")
        if "error" in data:
            print(f"   Error: {data['error']}")
        else:
            for platform, result in data["results"].items():
                status = result.get("status", "unknown")
                if status == "scheduled":
                    print(f"   {platform}: {result.get('post_id', 'ok')}")
                elif status == "skipped":
                    print(f"   {platform}: skipped ({result.get('reason', '')})")
                else:
                    print(f"   {platform}: {result.get('error', 'failed')}")
    
    results_file = OUTPUT_DIR / f"promotion_results_{datetime.now(IST).strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nDetailed results saved to: {results_file}")

if __name__ == "__main__":
    main()