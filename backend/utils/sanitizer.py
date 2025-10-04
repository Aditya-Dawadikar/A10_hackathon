# ---------- Sanitization Agent ----------
import os
import re
from typing import Dict, Any, Optional
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

    async def process(self, prompt: str, group_id: Optional[str] = None, group_name: Optional[str] = None) -> Dict[str, Any]:
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
                "action": "blocked",
                "intent": intent,
                "original_prompt": prompt,
                "redacted_prompt": None,
                "message": "Content blocked due to malicious intent",
                "evidence": {
                    "reason": "llm_classified_malicious",
                    "violations": [],
                    "categories": ["malicious_intent"]
                },
                "applied_policies": []
            }

        # --- Step 2: Load group + policies ---
        group = await get_group_with_policies(group_id=group_id, name=group_name)
        if not group:
            return {
                "status": "blocked",
                "action": "blocked",
                "intent": intent,
                "original_prompt": prompt,
                "redacted_prompt": None,
                "message": "No matching security group found",
                "evidence": {
                    "reason": "no_group_found",
                    "violations": [],
                    "categories": ["configuration_error"]
                },
                "applied_policies": []
            }

        # Separate block vs redact policies based on policy name and replacement text
        block_policies = []
        redact_policies = []
        applied_policies = []
        
        for p in group.get("policies", []):
            if not p.get("active", True):
                continue
                
            try:
                compiled = re.compile(p["pattern"], re.IGNORECASE)
                
                # Determine if this is a blocking or redacting policy
                policy_name = p.get("name", "").lower()
                replacement = p.get("replacement", "").lower()
                
                # Check if it's a blocking policy
                if any(keyword in policy_name for keyword in ["block", "reject", "deny", "prevent"]):
                    block_policies.append((compiled, p))
                elif any(keyword in replacement for keyword in ["block", "reject", "deny"]):
                    block_policies.append((compiled, p))
                else:
                    # Default to redact policy
                    redact_policies.append((compiled, p))
                    
            except re.error:
                print(f"⚠️ Invalid regex in policy {p.get('name', 'unknown')}: {p.get('pattern', '')}")

        # --- Step 3: Apply block policies first ---
        violations = []
        for pattern, policy in block_policies:
            matches = list(pattern.finditer(prompt))
            if matches:
                for match in matches:
                    violations.append({
                        "pattern": policy["pattern"],
                        "match": match.group(),
                        "policy": policy["name"],
                        "action": "block",
                        "position": [match.start(), match.end()]
                    })
                
                applied_policies.append({
                    "name": policy["name"],
                    "pattern": policy["pattern"],
                    "replacement": policy.get("replacement", ""),
                    "action": "block"
                })
                
                return {
                    "status": "blocked",
                    "action": "blocked",
                    "intent": intent,
                    "group": {"id": group["id"], "name": group["name"]},
                    "original_prompt": prompt,
                    "redacted_prompt": None,
                    "message": f"Content blocked by policy: {policy['name']}",
                    "evidence": {
                        "reason": "policy_violation_blocked",
                        "violations": violations,
                        "categories": ["policy_violation"]
                    },
                    "applied_policies": applied_policies
                }

        # --- Step 4: Apply redact policies ---
        redacted = prompt
        redactions_made = False
        
        for pattern, policy in redact_policies:
            matches = list(pattern.finditer(redacted))
            if matches:
                redactions_made = True
                for match in matches:
                    violations.append({
                        "pattern": policy["pattern"],
                        "match": match.group(),
                        "policy": policy["name"],
                        "action": "redact",
                        "position": [match.start(), match.end()]
                    })
                
                # Apply the redaction
                redacted = pattern.sub(policy["replacement"], redacted)
                
                applied_policies.append({
                    "name": policy["name"],
                    "pattern": policy["pattern"], 
                    "replacement": policy["replacement"],
                    "action": "redact"
                })

        # --- Step 5: Return appropriate status ---
        if redactions_made:
            return {
                "status": "redacted",
                "action": "redacted",
                "intent": intent,
                "group": {"id": group["id"], "name": group["name"]},
                "original_prompt": prompt,
                "redacted_prompt": redacted,
                "message": f"Content sanitized by {len(applied_policies)} policies",
                "evidence": {
                    "reason": "policy_violation_redacted", 
                    "violations": violations,
                    "categories": ["sensitive_content"]
                },
                "applied_policies": applied_policies
            }
        else:
            # No redactions needed - content is allowed
            return {
                "status": "allowed",
                "action": "allowed", 
                "intent": intent,
                "group": {"id": group["id"], "name": group["name"]},
                "original_prompt": prompt,
                "redacted_prompt": redacted,  # Same as original
                "message": "Content approved - no policy violations detected",
                "evidence": {
                    "reason": "no_policy_violations",
                    "violations": [],
                    "categories": []
                },
                "applied_policies": []
            }

