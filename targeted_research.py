# targeted_research.py
"""
TARGETED RESEARCH - Only research missing fields
"""

import json
import asyncio
from research_agent import ResearchAgent

async def targeted_research():
    print("="*80)
    print("🎯 TARGETED RESEARCH - Missing Fields Only")
    print("="*80)
    
    # Load retry queue
    with open("data/retry_queue.json", "r", encoding="utf-8") as f:
        retry_queue = json.load(f)
    
    if not retry_queue["apps"]:
        print("\n✅ No apps need research!")
        return
    
    print(f"\n📋 {len(retry_queue['apps'])} apps need targeted research")
    
    # Load current results
    with open("data/results.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Create lookup
    app_lookup = {a["app"]: a for a in data["apps"]}
    
    # Research each app
    agent = ResearchAgent()
    researched = 0
    failed = 0
    
    try:
        for i, app_info in enumerate(retry_queue["apps"], 1):
            app_name = app_info["app"]
            missing_fields = app_info["missing_fields"]
            
            print(f"\n🔍 [{i}/{len(retry_queue['apps'])}] Researching {app_name}")
            print(f"   Missing: {', '.join(missing_fields)}")
            
            try:
                # Research only this app
                result = await agent.research_app(
                    app_name,
                    app_lookup[app_name].get("category", ""),
                    ""  # No website hint needed
                )
                
                # Update only missing fields
                if app_name in app_lookup:
                    app = app_lookup[app_name]
                    
                    # Update auth methods if missing
                    if "auth_methods" in missing_fields and result.auth_methods:
                        app["auth_methods"] = result.auth_methods
                    
                    # Update access if missing
                    if "access" in missing_fields and result.access.value != "unknown":
                        app["access"] = result.access.value
                    
                    # Update API type if missing
                    if "api_type" in missing_fields and result.api_type.value != "unknown":
                        app["api_type"] = result.api_type.value
                    
                    # Update API breadth if missing
                    if "api_breadth" in missing_fields and result.api_breadth.value != "unknown":
                        app["api_breadth"] = result.api_breadth.value
                    
                    # Update native MCP if missing
                    if "native_mcp_status" in missing_fields and result.mcp_status.value != "unknown":
                        # Only set if evidence supports it
                        mcp_evidence = [e for e in result.evidence if "MCP" in e.claim or "mcp" in e.claim.lower()]
                        if mcp_evidence:
                            app["native_mcp_status"] = result.mcp_status.value
                            # Add evidence
                            for e in mcp_evidence:
                                if e not in app.get("evidence", []):
                                    app["evidence"].append(e.dict())
                    
                    # Update buildability if missing
                    if "buildability" in missing_fields and result.buildability.value != "unknown":
                        # Only update if auth/access/API are known
                        if app.get("auth_methods") and app.get("access") not in ["unknown", None]:
                            app["buildability"] = result.buildability.value
                    
                    # Update confidence
                    app["confidence"] = max(app["confidence"], result.confidence)
                    
                    print(f"   ✅ Updated {app_name}")
                    researched += 1
                    
            except Exception as e:
                print(f"   ❌ Failed: {str(e)}")
                failed += 1
            
            # Checkpoint every 5 apps
            if i % 5 == 0:
                with open("data/results_checkpoint.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
                print(f"\n💾 Checkpoint saved ({i} apps processed)")
    
    finally:
        await agent.close()
    
    # Save final
    with open("data/results.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    
    print("\n" + "="*80)
    print(f"✅ Targeted research complete:")
    print(f"   Researched: {researched}")
    print(f"   Failed: {failed}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(targeted_research())