# ---------- Sanitization Agent ----------
import os
import re
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnableSequence
from policy_controller import get_group_with_policies  # import your DB helper

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("❌ Missing GOOGLE_API_KEY in environment variables or .env file")


class PromptSanitizationAgent:
    def __init__(self):
        # LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",   # ✅ adjust if needed
            temperature=0,
            google_api_key=GOOGLE_API_KEY
        )

        # Intent classifier
        self.intent_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a security classifier. Return ONLY 'malicious' or 'safe'. No other text."),
            ("human", "Prompt: {user_prompt}")
        ])
        self.intent_classifier = RunnableSequence(
            self.intent_prompt | self.llm | StrOutputParser()
        )

        # LLM redactor fallback
        self.redact_prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "You are a redactor. Rewrite the user prompt by masking sensitive info "
             "(emails, SSNs, phones, API keys, commands, overrides). Replace with [REDACTED]. "
             "Keep everything else unchanged."),
            ("human", "{user_prompt}")
        ])
        self.llm_redactor = RunnableSequence(
            self.redact_prompt | self.llm | StrOutputParser()
        )

    async def process(self, prompt: str, group_id: str = None, group_name: str = None) -> dict:
        """
        Sanitize a prompt by:
        1. Checking intent (safe/malicious)
        2. If safe, applying policies defined in the group
        - Redact policies → mask matched info
        - Block policies → block if matched
        """
        # --- Step 1: Intent classification ---
        intent = self.intent_classifier.invoke({"user_prompt": prompt}).strip().lower()
        if intent not in ["safe", "malicious"]:
            intent = "safe"

        if intent == "malicious":
            return {
                "status": "blocked",
                "intent": intent,
                "original_prompt": prompt
            }

        # --- Step 2: Load group + policies ---
        group = await get_group_with_policies(group_id=group_id, name=group_name)
        if not group:
            return {
                "status": "blocked",
                "intent": "malicious",
                "original_prompt": prompt,
                "reason": "No matching group found"
            }

        # Separate block vs redact policies
        block_policies = []
        redact_policies = []
        for p in group["policies"]:
            if not p["active"]:
                continue
            try:
                compiled = re.compile(p["pattern"], re.IGNORECASE)
                if p.get("type") == "block":
                    block_policies.append((compiled, p))
                else:  # default = redact
                    redact_policies.append((compiled, p))
            except re.error:
                print(f"⚠️ Invalid regex in policy {p['name']}")

        # --- Step 3: Apply block policies first ---
        for pattern, policy in block_policies:
            if pattern.search(prompt):
                return {
                    "status": "blocked",
                    "intent": "malicious",
                    "group": {"id": group["id"], "name": group["name"]},
                    "original_prompt": prompt,
                    "reason": f"Blocked by policy: {policy['name']}"
                }

        # --- Step 4: Apply redact policies ---
        redacted = prompt
        regex_applied = False
        for pattern, policy in redact_policies:
            if pattern.search(redacted):
                regex_applied = True
                redacted = pattern.sub(policy["replacement"], redacted)

        if redact_policies and not regex_applied:
            redacted = prompt

        # --- Step 6: If no redact policies → return original ---
        return {
            "status": "allowed",
            "intent": intent,
            "group": {"id": group["id"], "name": group["name"]},
            "original_prompt": prompt,
            "redacted_prompt": redacted
        }

