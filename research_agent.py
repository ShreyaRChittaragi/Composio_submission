import os
import json
import csv
import asyncio
import httpx
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from dotenv import load_dotenv
from composio import Composio
from openai import AsyncOpenAI
import time

load_dotenv()

# ============ ENUMS ============

class AccessEnum(str, Enum):
    SELF_SERVE = "self_serve"
    PAID = "paid"
    ADMIN_GATED = "admin_gated"
    PARTNER_GATED = "partner_gated"
    CONTACT_SALES = "contact_sales"
    UNKNOWN = "unknown"

class APIEnum(str, Enum):
    REST = "rest"
    GRAPHQL = "graphql"
    BOTH = "both"
    OTHER = "other"
    NONE = "none"
    UNKNOWN = "unknown"

class BreadthEnum(str, Enum):
    BROAD = "broad"
    MODERATE = "moderate"
    NARROW = "narrow"
    NONE = "none"
    UNKNOWN = "unknown"

class MCPEnum(str, Enum):
    OFFICIAL = "official"
    COMMUNITY = "community"
    NONE = "none"
    UNKNOWN = "unknown"

class BuildabilityEnum(str, Enum):
    READY = "ready"
    READY_WITH_CONSTRAINTS = "ready_with_constraints"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"

class ComposioStatusEnum(str, Enum):
    EXISTING_TOOLKIT = "existing_toolkit"
    EXISTING_MCP = "existing_mcp"
    TOOLKIT_GAP = "toolkit_gap"
    UNKNOWN = "unknown"

class EvidenceSourceQuality(str, Enum):
    OFFICIAL_DOCS = "official_docs"
    OFFICIAL_AUTH = "official_auth"
    OFFICIAL_PRICING = "official_pricing"
    OFFICIAL_GITHUB = "official_github"
    COMPOSIO_TOOLKIT = "composio_toolkit"
    THIRD_PARTY = "third_party"
    INFERRED = "inferred"

# ============ PYDANTIC MODELS ============

class Evidence(BaseModel):
    claim: str
    value: str
    url: str
    source_title: str
    supporting_text: str
    source_quality: EvidenceSourceQuality

class AppResearch(BaseModel):
    app: str
    category: str
    description: str
    auth_methods: List[str] = Field(default_factory=list)
    access: AccessEnum = AccessEnum.UNKNOWN
    api_type: APIEnum = APIEnum.UNKNOWN
    api_breadth: BreadthEnum = BreadthEnum.UNKNOWN
    mcp_status: MCPEnum = MCPEnum.UNKNOWN
    composio_status: ComposioStatusEnum = ComposioStatusEnum.UNKNOWN
    composio_actions: List[str] = Field(default_factory=list)
    composio_actions_count: int = 0
    buildability: BuildabilityEnum = BuildabilityEnum.UNKNOWN
    main_blocker: str = ""
    confidence: float = 0.0
    needs_human_review: bool = False
    evidence: List[Evidence] = Field(default_factory=list)

class ResearchResult(BaseModel):
    apps: List[AppResearch]
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

# ============ RESEARCH AGENT WITH REAL COMPOSIO INTEGRATION ============

class ResearchAgent:
    def __init__(self):
        # Use Groq for LLM
        self.openai = AsyncOpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        
        # Initialize Composio
        self.composio = Composio(
            api_key=os.getenv("COMPOSIO_API_KEY")
        )
        
        self.httpx_client = httpx.AsyncClient(timeout=30.0)
        self.results: List[AppResearch] = []
        self.semaphore = asyncio.Semaphore(2)
        
        # Cache for Composio toolkits
        self._composio_cache = {}

    async def research_app(self, app_name: str, category: str, website_hint: str) -> AppResearch:
        """Research a single app using Composio and Groq."""
        
        # Step 1: Use Composio to discover if this app is already a toolkit
        composio_result = await self._check_composio_coverage(app_name)
        
        # Step 2: Use Groq to research with context
        research_data = await self._llm_research_with_context(
            app_name, 
            website_hint,
            composio_result
        )

        # Step 3: Combine all results
        return AppResearch(
            app=app_name,
            category=category,
            description=research_data.get("description", ""),
            auth_methods=research_data.get("auth_methods", []),
            access=research_data.get("access", AccessEnum.UNKNOWN),
            api_type=research_data.get("api_type", APIEnum.UNKNOWN),
            api_breadth=research_data.get("api_breadth", BreadthEnum.UNKNOWN),
            mcp_status=research_data.get("mcp_status", MCPEnum.UNKNOWN),
            composio_status=composio_result.get("status", ComposioStatusEnum.UNKNOWN),
            composio_actions=composio_result.get("actions", []),
            composio_actions_count=composio_result.get("actions_count", 0),
            buildability=research_data.get("buildability", BuildabilityEnum.UNKNOWN),
            main_blocker=research_data.get("main_blocker", ""),
            confidence=research_data.get("confidence", 0.5),
            evidence=research_data.get("evidence", []),
            needs_human_review=research_data.get("confidence", 0.5) < 0.65
        )

    async def _check_composio_coverage(self, app_name: str) -> Dict[str, Any]:
        """Check if app exists as a Composio toolkit."""
        toolkit_name = app_name.lower().replace(" ", "_").replace("-", "_").replace(".", "_")
        
        if toolkit_name in self._composio_cache:
            return self._composio_cache[toolkit_name]
        
        result = {
            "status": ComposioStatusEnum.TOOLKIT_GAP,
            "actions": [],
            "actions_count": 0
        }
        
        try:
            # Try to create a session with this toolkit
            session = self.composio.create(
                user_id="research_agent",
                mcp=True,
                toolkits=[toolkit_name]
            )
            
            # If we get here, the toolkit exists
            result["status"] = ComposioStatusEnum.EXISTING_TOOLKIT
            
            # Try to get available tools/actions
            try:
                # The session has tools property
                if hasattr(session, 'tools'):
                    tools = session.tools
                    if tools:
                        action_names = [str(t) for t in tools[:10]]
                        result["actions"] = action_names
                        result["actions_count"] = len(tools)
                        print(f"   📦 Composio toolkit found: {toolkit_name} with {len(tools)} tools")
                
                # Check for MCP
                if hasattr(session, 'mcp') and session.mcp:
                    result["status"] = ComposioStatusEnum.EXISTING_MCP
                    
            except Exception as e:
                print(f"   ⚠️ Could not enumerate tools: {e}")
                
        except Exception as e:
            # Toolkit doesn't exist - expected for most apps
            pass
        
        self._composio_cache[toolkit_name] = result
        return result

    async def _llm_research_with_context(
        self, 
        app_name: str, 
        website_hint: str,
        composio_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use Groq with Composio context to research the app."""
        
        composio_context = ""
        if composio_info.get("status") != ComposioStatusEnum.TOOLKIT_GAP:
            composio_context = f"""
            ✅ Composio already has this toolkit!
            - Status: {composio_info.get('status')}
            - Available actions: {', '.join(composio_info.get('actions', [])[:5])}
            - Total actions: {composio_info.get('actions_count', 0)}
            """
        
        prompt = f"""
        Research the following app for AI agent integration:

        App: {app_name}
        Website: {website_hint}
        
        {composio_context}

        Return a JSON object with these fields:
        - description: one-line what the app does (max 120 chars)
        - auth_methods: list of auth methods (OAuth2, API Key, Basic, Token, etc.)
        - access: one of "self_serve", "paid", "admin_gated", "partner_gated", "contact_sales", "unknown"
        - api_type: one of "rest", "graphql", "both", "other", "none", "unknown"
        - api_breadth: one of "broad", "moderate", "narrow", "none", "unknown" 
        - mcp_status: one of "official", "community", "none", "unknown"
        - buildability: one of "ready", "ready_with_constraints", "blocked", "unknown"
        - main_blocker: string describing main blocker if any (empty string if none)
        - confidence: float 0-1 based on how confident you are in the research
        - evidence: list of dicts with fields:
          - claim: what this evidence supports
          - value: the specific value
          - url: real documentation URL
          - source_title: title of the source
          - supporting_text: brief quote or summary
          - source_quality: one of "official_docs", "official_auth", "official_pricing", "official_github", "composio_toolkit", "third_party", "inferred"

        Use only real documentation URLs you know exist. Be honest about what you can't confirm.
        If Composio already has a toolkit, mark it as evidence with source_quality "composio_toolkit".
        """

        try:
            response = await self.openai.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a technical researcher analyzing API documentation. Return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            
            # Add Composio evidence if toolkit exists
            if composio_info.get("status") != ComposioStatusEnum.TOOLKIT_GAP:
                if "evidence" not in result:
                    result["evidence"] = []
                result["evidence"].append({
                    "claim": "Composio toolkit exists",
                    "value": composio_info.get("status"),
                    "url": "https://app.composio.dev",
                    "source_title": "Composio Platform",
                    "supporting_text": f"Toolkit with {composio_info.get('actions_count', 0)} actions available",
                    "source_quality": "composio_toolkit"
                })
            
            # Ensure all required fields exist
            required_fields = ["description", "auth_methods", "access", "api_type", 
                             "api_breadth", "mcp_status", "buildability", "main_blocker", 
                             "confidence", "evidence"]
            for field in required_fields:
                if field not in result:
                    if field in ["auth_methods", "evidence"]:
                        result[field] = []
                    elif field == "main_blocker":
                        result[field] = ""
                    else:
                        result[field] = "unknown"
            
            return result
            
        except Exception as e:
            print(f"❌ LLM research failed for {app_name}: {str(e)}")
            return {
                "description": f"Research failed for {app_name}",
                "auth_methods": [],
                "access": AccessEnum.UNKNOWN,
                "api_type": APIEnum.UNKNOWN,
                "api_breadth": BreadthEnum.UNKNOWN,
                "mcp_status": MCPEnum.UNKNOWN,
                "buildability": BuildabilityEnum.UNKNOWN,
                "main_blocker": f"Research error: {str(e)}",
                "confidence": 0.2,
                "evidence": [],
                "needs_human_review": True
            }

    async def research_batch(self, apps: List[tuple]) -> List[AppResearch]:
        """Research a batch of apps."""
        async def research_one(app_name, category, website_hint):
            async with self.semaphore:
                print(f"🔍 Researching {app_name}...")
                result = await self.research_app(app_name, category, website_hint)
                print(f"✅ Completed {app_name}: {result.composio_status.value} | {result.buildability.value} | conf={result.confidence:.2f}")
                return result

        tasks = [research_one(name, cat, hint) for name, cat, hint in apps]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for r in results:
            if isinstance(r, Exception):
                print(f"⚠️ Error in research: {str(r)}")
            else:
                valid_results.append(r)
        
        return valid_results

    async def close(self):
        await self.httpx_client.aclose()

# ============ MAIN ============

async def main():
    # Load apps from CSV
    apps = []
    try:
        with open("data/apps.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                apps.append((row["app"], row["category"], row["website_hint"]))
        print(f"📚 Loaded {len(apps)} apps from CSV")
    except FileNotFoundError:
        print("❌ data/apps.csv not found. Please create it first.")
        return
    except KeyError as e:
        print(f"❌ CSV missing column: {e}")
        print("Required columns: app, category, website_hint")
        return

    # Check for checkpoint
    checkpoint_file = "data/results_checkpoint.json"
    processed_apps = set()
    all_results = []
    
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
                processed_apps = {app["app"] for app in checkpoint["apps"]}
                all_results = checkpoint["apps"]
            print(f"🔄 Found checkpoint with {len(processed_apps)} apps already processed")
            
            # Remove processed apps from the list
            apps = [(name, cat, hint) for name, cat, hint in apps 
                    if name not in processed_apps]
            print(f"📝 {len(apps)} apps remaining to research")
        except Exception as e:
            print(f"⚠️ Error loading checkpoint: {e}, starting fresh")

    if not apps:
        print("✅ All apps already processed!")
        # Load final results
        if os.path.exists("data/results.json"):
            with open("data/results.json", "r", encoding="utf-8") as f:
                final_data = json.load(f)
                all_results = final_data["apps"]
                print(f"📊 Loaded {len(all_results)} results from final file")
        else:
            print("⚠️ No final results found.")
        return

    # Process all remaining apps
    BATCH_SIZE = 10  # Process 10 at a time to avoid rate limits
    total_batches = (len(apps) + BATCH_SIZE - 1) // BATCH_SIZE
    
    agent = ResearchAgent()
    try:
        for i in range(0, len(apps), BATCH_SIZE):
            batch = apps[i:i+BATCH_SIZE]
            batch_num = i//BATCH_SIZE + 1
            print(f"\n🚀 Processing batch {batch_num}/{total_batches} ({len(batch)} apps)...")
            
            results = await agent.research_batch(batch)
            
            # Add to all results
            for r in results:
                if isinstance(r, AppResearch):
                    all_results.append(r.model_dump())
                else:
                    print(f"⚠️ Skipping invalid result: {r}")
            
            # Save checkpoint after each batch
            checkpoint_data = {
                "apps": all_results,
                "generated_at": datetime.now().isoformat(),
                "batch": batch_num,
                "total_batches": total_batches
            }
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, indent=2, default=str)
            print(f"💾 Checkpoint saved ({len(all_results)} apps processed)")
            
            # Small delay between batches
            if batch_num < total_batches:
                print("⏳ Waiting 2 seconds before next batch...")
                await asyncio.sleep(2)

        # Final save
        result = ResearchResult(apps=[AppResearch(**a) for a in all_results])
        with open("data/results.json", "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=2, default=str)
        
        print(f"\n✅ All {len(all_results)} apps researched and saved to data/results.json")
        
        # Stats
        ready = sum(1 for a in all_results if a["buildability"] == "ready")
        ready_with_constraints = sum(1 for a in all_results if a["buildability"] == "ready_with_constraints")
        blocked = sum(1 for a in all_results if a["buildability"] == "blocked")
        unknown = sum(1 for a in all_results if a["buildability"] == "unknown")
        with_composio = sum(1 for a in all_results if a["composio_status"] in ["existing_toolkit", "existing_mcp"])
        gaps = sum(1 for a in all_results if a["composio_status"] == "toolkit_gap")
        
        print("\n" + "="*80)
        print("📊 FINAL STATS:")
        print(f"   Total researched: {len(all_results)}")
        print(f"   Buildable now: {ready} ({ready/len(all_results)*100:.1f}%)")
        print(f"   Buildable with constraints: {ready_with_constraints} ({ready_with_constraints/len(all_results)*100:.1f}%)")
        print(f"   Blocked: {blocked} ({blocked/len(all_results)*100:.1f}%)")
        print(f"   Unknown: {unknown} ({unknown/len(all_results)*100:.1f}%)")
        print(f"   Already in Composio: {with_composio} ({with_composio/len(all_results)*100:.1f}%)")
        print(f"   Composio gaps: {gaps} ({gaps/len(all_results)*100:.1f}%)")
        
        # Show apps that might already have Composio coverage
        if with_composio > 0:
            composio_apps = [a for a in all_results if a["composio_status"] in ["existing_toolkit", "existing_mcp"]]
            print(f"\n📦 Apps with Composio coverage:")
            for a in composio_apps[:5]:
                print(f"   - {a['app']}: {a['composio_status']} ({a.get('composio_actions_count', 0)} actions)")
        
        # Show top opportunities
        opportunities = [
            a for a in all_results 
            if a["buildability"] == "ready" 
            and a["access"] == "self_serve"
            and a["composio_status"] == "toolkit_gap"
            and a["confidence"] >= 0.7
        ]
        if opportunities:
            print(f"\n🚀 Top 5 immediate build opportunities:")
            for a in opportunities[:5]:
                print(f"   - {a['app']} ({a['category']})")
        print("="*80)

    finally:
        await agent.close()

if __name__ == "__main__":
    asyncio.run(main())