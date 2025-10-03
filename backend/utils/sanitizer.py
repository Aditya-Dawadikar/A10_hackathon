# ---------- Sanitization Agent ----------
import os
from dotenv import load_dotenv
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnableSequence

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("❌ Missing GOOGLE_API_KEY in environment variables or .env file")


class PromptSanitizationAgent:
    def __init__(self):
        # Regex rules
        self.redaction_rules = {
            "ssn": (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
            "credit_card": (re.compile(r"\b\d{16}\b"), "[REDACTED_CARD]"),
            "api_key": (re.compile(r"\b[A-Za-z0-9+/=]{32,}\b"), "[REDACTED_KEY]"),
            "email": (re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"), "[REDACTED_EMAIL]"),
            "system_override": (re.compile(r"(ignore\s+previous\s+instructions|system\s+prompt|jailbreak)", re.IGNORECASE), "[REDACTED_OVERRIDE]"),
            "shell_cmd": (re.compile(r"(rm\s+-rf\s+/|shutdown\s+-h|del\s+/f\s+/s|wget\s+http|curl\s+http)", re.IGNORECASE), "[REDACTED_CMD]")
        }

        # LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",   # Replace with valid model
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
             "(emails, SSNs, API keys, commands, overrides). Replace with [REDACTED]. "
             "Keep everything else unchanged."),
            ("human", "{user_prompt}")
        ])
        self.llm_redactor = RunnableSequence(
            self.redact_prompt | self.llm | StrOutputParser()
        )

    def process(self, prompt: str) -> dict:
        # Step 1: Intent classification
        intent = self.intent_classifier.invoke({"user_prompt": prompt}).strip().lower()
        if intent not in ["safe", "malicious"]:
            intent = "safe"

        # Step 2: Block malicious
        if intent == "malicious":
            return {
                "status": "blocked",
                "intent": intent,
                "original_prompt": prompt
            }

        # Step 3: Redact safe prompts
        redacted = prompt
        regex_applied = False
        for _, (pattern, replacement) in self.redaction_rules.items():
            if pattern.search(redacted):
                regex_applied = True
                redacted = pattern.sub(replacement, redacted)

        if not regex_applied:
            redacted = self.llm_redactor.invoke({"user_prompt": prompt})

        return {
            "status": "allowed",
            "intent": intent,
            "original_prompt": prompt,
            "redacted_prompt": redacted
        }