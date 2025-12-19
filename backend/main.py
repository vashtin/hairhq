from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json
import os
import re
from pathlib import Path

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


app = FastAPI()

# Local dev CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent


# ---------------- FLEXIBLE INPUT MODELS ----------------
class HairProfileIn(BaseModel):
    # Keep this flexible because your frontend uses mixed key styles
    mode: Optional[str] = "women"
    source: Optional[str] = None

    hair_type: Optional[str] = Field(default=None, alias="hairType")
    hair_length: Optional[str] = Field(default=None, alias="hairLength")

    porosity: Optional[str] = None
    density: Optional[str] = None

    strand_width: Optional[str] = Field(default=None, alias="strandWidth")
    scalp: Optional[str] = None
    scalp_condition: Optional[str] = Field(default=None, alias="scalpCondition")
    dryness_level: Optional[str] = Field(default=None, alias="dryness")

    main_issues: Optional[List[str]] = Field(default_factory=list, alias="issues")
    goals: Optional[List[str]] = Field(default_factory=list)

    wash_frequency: Optional[str] = Field(default=None, alias="washFrequency")
    routine_level: Optional[str] = Field(default=None, alias="routineLevel")
    heat_usage: Optional[str] = Field(default=None, alias="heatUsage")
    chemical_treatments: Optional[str] = Field(default=None, alias="chemicals")
    nighttime_care: Optional[str] = Field(default=None, alias="nightCare")

    curiosity: Optional[str] = "detailed"
    extra_details: Optional[str] = Field(default=None, alias="extraDetails")

    class Config:
    
        populate_by_name = True
        extra = "allow"


class HairChatIn(BaseModel):
    message: str
    history: Optional[List[Dict[str, Any]]] = None
    profile: Optional[Dict[str, Any]] = None
    plan_context: Optional[Dict[str, Any]] = None
    previous_response_id: Optional[str] = None


# ---------------- HELPERS ----------------
def safe_mode(mode: Optional[str]) -> str:
    m = (mode or "").strip().lower()
    return m if m in {"women", "men"} else "women"


def coalesce(*vals):
    for v in vals:
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def clean_list(x):
    if isinstance(x, list):
        return [i.strip() for i in x if isinstance(i, str) and i.strip()]
    if isinstance(x, str):
        s = x.strip()
        if not s:
            return []
        parts = re.split(r"\r?\n|•|\u2022|,|;|-", s)
        return [p.strip() for p in parts if p.strip()]
    return []


def extract_json(raw: str) -> Dict[str, Any]:
    raw = (raw or "").strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return {}
    return {}


def normalize_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "summary": plan.get("summary", "") if isinstance(plan.get("summary", ""), str) else "",
        "routine": clean_list(plan.get("routine")),
        "products": clean_list(plan.get("products")),
        "ingredients": clean_list(plan.get("ingredients")),
        "avoid": clean_list(plan.get("avoid")),
    }


def get_openai():
    if OpenAI is None:
        return None
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key)


def load_info_file(mode: str) -> Dict[str, Any]:
    mode = safe_mode(mode)
    path = BASE_DIR / f"info_{mode}.json"
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ---------------- BASIC ----------------
@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------- INFO ENDPOINTS (fixes your 404) ----------------
@app.get("/api/info")
def api_info(mode: str = Query(default="women")):
    return load_info_file(mode)


@app.get("/api/hair-info/{mode}")
def api_hair_info(mode: str):
    return load_info_file(mode)


# ---------------- PLAN ENDPOINT (detailed, non-generic) ----------------
@app.post("/api/hair-plan")
def generate_hair_plan(profile_in: HairProfileIn):
    client = get_openai()
    mode = safe_mode(profile_in.mode)

    canonical = {
        "mode": mode,
        "source": profile_in.source,
        "hair_type": coalesce(profile_in.hair_type),
        "hair_length": coalesce(profile_in.hair_length),
        "porosity": coalesce(profile_in.porosity),
        "density": coalesce(profile_in.density),
        "strand_width": coalesce(profile_in.strand_width),
        "scalp": coalesce(profile_in.scalp, profile_in.scalp_condition),
        "dryness_level": coalesce(profile_in.dryness_level),
        "main_issues": clean_list(profile_in.main_issues),
        "goals": clean_list(profile_in.goals),
        "wash_frequency": coalesce(profile_in.wash_frequency),
        "routine_level": coalesce(profile_in.routine_level),
        "heat_usage": coalesce(profile_in.heat_usage),
        "chemical_treatments": coalesce(profile_in.chemical_treatments),
        "nighttime_care": coalesce(profile_in.nighttime_care),
        "curiosity": coalesce(profile_in.curiosity) or "detailed",
        "extra_details": coalesce(profile_in.extra_details),
    }

    if client is None:
        return {
            "summary": "OpenAI not configured.",
            "routine": [],
            "products": [],
            "ingredients": [],
            "avoid": [],
            "profile_received": canonical,
        }

    system = (
        "You are HairHQ Hair Plan Generator, a professional stylist + hair educator.\n"
        "Be inclusive across hair types 1–4 and do NOT assume ethnicity.\n"
        "Recommend product TYPES (not brands).\n"
        "Be specific and avoid generic routines.\n"
        "Use the hair profile details (especially length, porosity, scalp, goals, issues).\n\n"
        "Return ONLY valid JSON with exactly these keys:\n"
        "summary (string), routine (array of strings), products (array of strings), "
        "ingredients (array of strings), avoid (array of strings).\n"
        "No markdown. No extra keys.\n"
    )

    mode_line = (
        "MEN MODE: keep routine practical; include scalp/hair loss/dandruff considerations if relevant."
        if mode == "men"
        else "WOMEN MODE: include styling + washday flow; align with length + goals."
    )

    user_msg = (
        f"{mode_line}\n\n"
        f"HAIR_PROFILE_JSON:\n{json.dumps(canonical, indent=2)}\n\n"
        "Create a DETAILED plan that feels unique to this profile.\n"
        "Routine should be step-by-step and actionable (frequency + what to do).\n"
        "Include specific guidance for porosity/length/scalp.\n"
        "Avoid one-size-fits-all advice.\n"
    )

    try:
        resp = client.responses.create(
            model="gpt-4o-mini",
            instructions=system,
            input=user_msg,
            temperature=0.7,
        )

        parsed = extract_json(resp.output_text)
        plan = normalize_plan(parsed)

        # Guard against empty/low-detail output
        if not plan["routine"] or len(plan["routine"]) < 4:
            # Ask again once, stricter
            resp2 = client.responses.create(
                model="gpt-4o-mini",
                instructions=system + "\nIMPORTANT: Provide at least 6 routine steps with frequencies.",
                input=user_msg,
                temperature=0.7,
            )
            parsed2 = extract_json(resp2.output_text)
            plan = normalize_plan(parsed2)

        return {**plan, "profile_received": canonical}

    except Exception as e:
        print(f"OpenAI Error (plan): {e}")
        return {
            "summary": "Could not generate plan right now.",
            "routine": [],
            "products": [],
            "ingredients": [],
            "avoid": [],
            "profile_received": canonical,
        }


# ---------------- CHAT ENDPOINT (styles + searches) ----------------
@app.post("/api/hair-chat")
def hair_chat(payload: HairChatIn):
    client = get_openai()
    if client is None:
        return {"reply": "OpenAI not configured", "style_ideas": [], "style_details": []}

    profile = payload.profile or {}
    history = payload.history or []
    message = (payload.message or "").strip()
    prev_id = payload.previous_response_id

    # Allows your frontend to pre-load context without the user typing “real” text
    if message == "INIT_CONTEXT":
        message = "Based on my hair profile, suggest styles that usually work best for me."

    system = (
        "You are HairHQ Style Assist, a professional stylist.\n"
        "The hair profile is authoritative and must be used.\n\n"
        "Respond ONLY in valid JSON with EXACT structure:\n"
        "{\n"
        '  \"reply\": string,\n'
        '  \"style_ideas\": [string, string, ...],\n'
        '  \"style_details\": [\n'
        "    {\n"
        '      \"title\": string,\n'
        '      \"why\": string,\n'
        '      \"image_search\": string,\n'
        '      \"youtube_search\": string\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "RULES:\n"
        "- Generate 4–7 styles.\n"
        "- style_ideas must be short, clear style names someone would actually search.\n"
        "- style_details titles must match style_ideas exactly.\n"
        "- Use hair length + hair type/texture + porosity + goals + user intent.\n"
        "- image_search must work in Google Images.\n"
        "- youtube_search must work in YouTube search.\n"
        "- Include hair length + hair type in searches.\n"
        "- No brands. No vague aesthetic-only terms.\n"
    )

    convo_parts = [f"HAIR_PROFILE_JSON:\n{json.dumps(profile, indent=2)}"]

    # Keep history short so it stays relevant
    for m in history[-8:]:
        role = (m.get("role") or "").strip().lower()
        content = (m.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            convo_parts.append(f"{role.upper()}: {content}")

    if payload.plan_context:
        convo_parts.append(f"PLAN_CONTEXT_JSON:\n{json.dumps(payload.plan_context)[:2000]}")

    convo_parts.append(f"USER: {message}")

    try:
        resp = client.responses.create(
            model="gpt-4o-mini",
            instructions=system,
            input="\n".join(convo_parts),
            previous_response_id=prev_id,
            temperature=0.7,
        )

        parsed = extract_json(resp.output_text)

        reply = parsed.get("reply", "") or ""
        style_ideas = parsed.get("style_ideas", []) or []
        style_details = parsed.get("style_details", []) or []

        # Soft validation to prevent “random” mismatched results
        if isinstance(style_ideas, list) and isinstance(style_details, list) and style_ideas:
            # Keep only details whose title appears in style_ideas
            allowed = {str(s).strip() for s in style_ideas if str(s).strip()}
            style_details = [d for d in style_details if isinstance(d, dict) and str(d.get("title", "")).strip() in allowed]

        return {
            "reply": reply,
            "style_ideas": style_ideas if isinstance(style_ideas, list) else [],
            "style_details": style_details if isinstance(style_details, list) else [],
            "response_id": resp.id,
        }

    except Exception as e:
        print(f"OpenAI Error (chat): {e}")
        return {"reply": "Something went wrong generating a response. Try again.", "style_ideas": [], "style_details": []}
