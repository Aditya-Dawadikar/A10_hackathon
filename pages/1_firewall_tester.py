import streamlit as st
import random
import requests

# -------------------
# CONFIG (DUMMY ON)
# -------------------
PROXY_URL = "http://localhost:8000"
USE_DUMMY = True   # <<-- Dummy flag ON by default
# -------------------

st.set_page_config(page_title="Firewall Tester", page_icon="🛡️")
st.title("🛡️ Firewall Tester – Live Prompt Check (Demo Mode)")

# Inputs
prompt = st.text_area("Enter your prompt or payload", height=180)

# Security checks toggles
st.subheader("Security Checks")
col1, col2, col3 = st.columns(3)

with col1:
    check_pii = st.checkbox("PII (Personally Identifiable Information)", value=True)
    check_secrets = st.checkbox("Secrets", value=True)

with col2:
    check_prompt_injection = st.checkbox("Prompt Injection", value=True)
    check_malicious_domain = st.checkbox("Malicious Domain", value=True)

with col3:
    check_injection_attacks = st.checkbox("Injection Attacks", value=True)
    check_rate_limiting = st.checkbox("Rate Limiting", value=True)



def dummy_sanitize_request(prompt, checks):
    # Simulate different responses based on content and checks - matching backend format
    if "ignore" in prompt.lower() and "instruction" in prompt.lower() and "prompt_injection" in checks:
        return {
            "status": "blocked",
            "intent": "malicious",
            "original_prompt": prompt
        }, 200
    elif ("123-456-7899" in prompt or "AKIA" in prompt) and ("pii" in checks or "secrets" in checks):
        redacted = prompt
        if "123-456-7899" in prompt:
            redacted = redacted.replace("123-456-7899", "[REDACTED]")
        if "AKIA1234567890EXAMPLE" in prompt:
            redacted = redacted.replace("AKIA1234567890EXAMPLE", "[REDACTED_API_KEY]")
        return {
            "status": "allowed",
            "intent": "safe",
            "original_prompt": prompt,
            "redacted_prompt": redacted
        }, 200
    elif "malicious.example" in prompt and "malicious_domain" in checks:
        return {
            "status": "blocked",
            "intent": "malicious",
            "original_prompt": prompt
        }, 200
    else:
        return {
            "status": "allowed",
            "intent": "safe",
            "original_prompt": prompt,
            "redacted_prompt": prompt
        }, 200

def real_sanitize_request(prompt, checks):
    payload = {
        "prompt": prompt,
        "checks": checks
    }
    resp = requests.post(f"{PROXY_URL}/sanitize", json=payload, timeout=10)
    return resp.json(), resp.status_code

sanitize_request = dummy_sanitize_request if USE_DUMMY else real_sanitize_request

if st.button("🧹 Sanitize"):
    if not prompt.strip():
        st.warning("Enter a prompt to sanitize.")
    else:
        # Collect selected checks
        checks = []
        if check_pii:
            checks.append("pii")
        if check_secrets:
            checks.append("secrets")
        if check_prompt_injection:
            checks.append("prompt_injection")
        if check_malicious_domain:
            checks.append("malicious_domain")
        if check_injection_attacks:
            checks.append("injection_attacks")
        if check_rate_limiting:
            checks.append("rate_limiting")
        
        try:
            resp, status = sanitize_request(prompt, checks)
            
            st.subheader("🔍 Sanitization Result")
            
            # Display the full response
            st.json(resp)
            
            # Parse and display user-friendly results
            status_val = resp.get("status", "unknown")
            intent = resp.get("intent", "unknown")
            original_prompt = resp.get("original_prompt", "")
            redacted_prompt = resp.get("redacted_prompt", "")
            
            if status_val == "blocked":
                st.error("⛔ **BLOCKED** - Prompt violates security policies")
                st.error(f"**Intent**: {intent}")
                st.warning("🚫 This prompt will NOT be sent to the LLM")
                
            elif status_val == "allowed":
                if redacted_prompt and redacted_prompt != original_prompt:
                    st.warning("✂️ **ALLOWED with REDACTION** - Sensitive content removed")
                    st.info(f"**Intent**: {intent}")
                    st.subheader("📤 Original Prompt:")
                    st.code(original_prompt, language="text")
                    st.subheader("📤 Sanitized Output sent to LLM:")
                    st.code(redacted_prompt, language="text")
                else:
                    st.success("✅ **ALLOWED** - Prompt passed all security checks")
                    st.info(f"**Intent**: {intent}")
                    st.subheader("📤 Output sent to LLM:")
                    st.code(original_prompt, language="text")
            
            # Show applied checks
            st.subheader("🔧 Applied Security Checks")
            if checks:
                for check in checks:
                    st.text(f"✓ {check.replace('_', ' ').title()}")
            else:
                st.text("No security checks were applied")
                
        except Exception as e:
            st.error(f"❌ Error contacting firewall API: {e}")
            st.info("Make sure the backend server is running on localhost:8000")
