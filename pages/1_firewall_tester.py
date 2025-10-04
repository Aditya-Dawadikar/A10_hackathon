import streamlit as st
import requests

# -------------------
# CONFIG (LIVE API)
# -------------------
PROXY_URL = "http://localhost:8000"
USE_DUMMY = False   # <<-- Using real API calls
# -------------------

st.set_page_config(page_title="Firewall Tester", page_icon="🛡️")
st.title("🛡️ Sanitizer Proxy Tester – Live API Mode")

# Function to get groups from API
def get_groups():
    """Fetch all groups from the backend API"""
    try:
        response = requests.get(f"{PROXY_URL}/groups", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch groups: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
        return []

# Get groups
groups = get_groups()

if not groups:
    st.warning("⚠️ No groups available. Please check if the backend is running and groups are configured.")
    st.stop()

# Group selection
st.subheader("🔐 Select Security Group")
group_options = [f"{group['name']} (ID: {group['id']})" for group in groups]
selected_group_index = st.radio(
    "Choose a security group:",
    range(len(group_options)),
    format_func=lambda x: group_options[x],
    help="Select which security group policies to apply to your prompt"
)

selected_group = groups[selected_group_index]
st.info(f"Selected: **{selected_group['name']}** with {len(selected_group.get('policies', []))} policies")

# Prompt input
st.subheader("✍️ Enter Your Prompt")
prompt = st.text_area(
    "Enter your prompt:", 
    height=150,
    placeholder="Type your prompt here to test against security policies..."
)

def call_sanitize_api(prompt, group_id, group_name):
    """Call the sanitize API with prompt and group information"""
    payload = {
        "prompt": prompt,
        "groupId": group_id,
        "groupName": group_name,
        "agent_id": "firewall-tester-ui"
    }
    try:
        response = requests.post(f"{PROXY_URL}/sanitize", json=payload, timeout=15)
        return response.json(), response.status_code
    except Exception as e:
        return {"error": str(e)}, 500

# Sanitize button
if st.button("🛡️ Sanitize", type="primary", use_container_width=True):
    if not prompt.strip():
        st.warning("⚠️ Please enter a prompt to test.")
    else:
        with st.spinner("🔍 Analyzing prompt against security policies..."):
            result, status_code = call_sanitize_api(prompt, selected_group['id'], selected_group['name'])
            
            if status_code != 200 or "error" in result:
                st.error(f"❌ API Error: {result.get('error', 'Unknown error')}")
                st.info("Make sure the backend server is running on localhost:8000")
            else:
                st.subheader("🔍 Security Analysis Results")
                
                # Display the full API response in expandable section
                with st.expander("🔍 Raw API Response", expanded=False):
                    st.json(result)
                
                # Parse and display user-friendly results
                status_val = result.get("status", "unknown")
                intent = result.get("intent", "unknown")
                original_prompt = result.get("original_prompt", prompt)
                redacted_prompt = result.get("redacted_prompt", prompt)
                group_info = result.get("group", {})
                message = result.get("message", "")
                applied_policies = result.get("applied_policies", [])
                
                # Handle the three different statuses properly
                if status_val == "blocked":
                    st.error("### ❌ PROMPT BLOCKED")
                    st.error(f"**Reason:** {message}")
                    if intent:
                        st.error(f"**Intent Classification:** {intent}")
                    st.warning("🚫 This prompt will **NOT** be sent to the LLM")
                    
                elif status_val == "redacted":
                    st.warning("### ✂️ CONTENT REDACTED")
                    st.info(f"**Reason:** {message}")
                    if intent:
                        st.info(f"**Intent Classification:** {intent}")
                    st.info("✅ Sensitive content was detected and sanitized")
                    
                    # Show original vs redacted side by side
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("📝 Original Prompt")
                        st.code(original_prompt, language="text")
                    with col2:
                        st.subheader("✂️ Sanitized Prompt")
                        st.code(redacted_prompt, language="text")
                    
                    st.success("🔄 The sanitized version will be sent to the LLM")
                    
                elif status_val == "allowed":
                    st.success("### ✅ PROMPT ALLOWED")
                    st.success(f"**Reason:** {message}")
                    if intent:
                        st.success(f"**Intent Classification:** {intent}")
                    st.success("✅ Prompt passed all security checks")
                    
                    st.subheader("📤 Prompt sent to LLM")
                    st.code(original_prompt, language="text")
                
                else:
                    st.warning(f"### ❓ UNKNOWN STATUS: {status_val}")
                    st.json(result)
                
                # Show applied policies if any
                if applied_policies:
                    st.subheader("🔧 Applied Security Policies")
                    for policy in applied_policies:
                        action_emoji = "🚫" if policy.get("action") == "block" else "✂️"
                        st.info(f"{action_emoji} **{policy.get('name', 'Unknown Policy')}** - {policy.get('action', 'unknown').title()}")
                        if policy.get('replacement') and policy.get('action') == 'redact':
                            st.caption(f"   Replacement: `{policy['replacement']}`")
                
                # Show group information
                if group_info:
                    st.subheader("🏢 Security Group Information")
                    st.info(f"**Group:** {group_info.get('name', 'Unknown')} (ID: {group_info.get('id', 'Unknown')})")
                    
                    # Show all policies in the group
                    if selected_group.get('policies'):
                        st.subheader("📋 All Policies in Group")
                        for i, policy in enumerate(selected_group['policies'], 1):
                            status_icon = "🟢" if policy.get('active', True) else "🔴"
                            st.text(f"{status_icon} {i}. {policy.get('name', 'Unnamed Policy')}")
                            st.caption(f"   Pattern: `{policy.get('pattern', 'No pattern')}`")
                            st.caption(f"   Replacement: `{policy.get('replacement', 'No replacement')}`")
                    else:
                        st.text("No policies configured for this group")
                
                # Show performance metrics
                st.subheader("📊 Test Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Status", status_val.upper())
                with col2:
                    st.metric("Policies Applied", len(applied_policies))
                with col3:
                    if status_val == "redacted" and original_prompt and redacted_prompt:
                        redaction_pct = ((len(original_prompt) - len(redacted_prompt)) / len(original_prompt)) * 100
                        st.metric("Content Redacted", f"{redaction_pct:.1f}%")
                    else:
                        st.metric("Content Changed", "0%")
