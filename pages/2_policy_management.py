import streamlit as st
import requests
import json
from typing import Dict, List, Optional

st.set_page_config(page_title="Policy Management", page_icon="🛡️", layout="wide")

# Configuration
USE_DUMMY = True
API_BASE_URL = "http://localhost:8000"

# Initialize session state
if "dummy_groups" not in st.session_state:
    st.session_state.dummy_groups = [
        {
            "id": "group_1", 
            "name": "Admin Group", 
            "policies": [
                {
                    "id": "policy_1",
                    "name": "Redact PII",
                    "pattern": r"(\b\d{3}-\d{2}-\d{4}\b|\b\d{3}-\d{3}-\d{4}\b|[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
                    "replacement": "[REDACTED_PII]",
                    "active": True
                },
                {
                    "id": "policy_2",
                    "name": "Block Prompt Injection",
                    "pattern": r"(ignore\s+previous\s+instructions|system\s+prompt|jailbreak|do\s+anything\s+now)",
                    "replacement": "[REDACTED_INJECTION]",
                    "active": True
                },
                {
                    "id": "policy_3",
                    "name": "Redact Secrets",
                    "pattern": r"([A-Za-z0-9+/=]{32,})",
                    "replacement": "[REDACTED_SECRET]",
                    "active": True
                }
            ]
        },
        {
            "id": "group_2", 
            "name": "Developer Group", 
            "policies": [
                {
                    "id": "policy_4",
                    "name": "Block Prompt Injection",
                    "pattern": r"(ignore\s+previous\s+instructions|system\s+prompt|jailbreak)",
                    "replacement": "[REDACTED_INJECTION]",
                    "active": True
                },
                {
                    "id": "policy_5",
                    "name": "Redact Secrets",
                    "pattern": r"([A-Za-z0-9+/=]{32,})",
                    "replacement": "[REDACTED_SECRET]",
                    "active": True
                }
            ]
        },
        {
            "id": "group_3", 
            "name": "Basic User Group", 
            "policies": [
                {
                    "id": "policy_6",
                    "name": "Redact PII",
                    "pattern": r"(\b\d{3}-\d{2}-\d{4}\b|[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
                    "replacement": "[REDACTED_PII]",
                    "active": True
                }
            ]
        }
    ]

# Commented out user-related functionality for now
# if "dummy_users" not in st.session_state:
#     st.session_state.dummy_users = [
#         {"id": "user_1", "username": "admin_user", "description": "System Administrator", "group": "Admin Group"},
#         {"id": "user_2", "username": "dev_user", "description": "Software Developer", "group": "Developer Group"},
#         {"id": "user_3", "username": "basic_user", "description": "Regular User", "group": "Basic User Group"}
#     ]

if "show_add_group" not in st.session_state:
    st.session_state.show_add_group = False

# if "show_add_user" not in st.session_state:
#     st.session_state.show_add_user = False

if "edit_group_id" not in st.session_state:
    st.session_state.edit_group_id = None

# if "edit_user_id" not in st.session_state:
#     st.session_state.edit_user_id = None

# Available security policy templates
POLICY_TEMPLATES = [
    {
        "name": "Redact PII",
        "pattern": r"(\b\d{3}-\d{2}-\d{4}\b|\b\d{3}-\d{3}-\d{4}\b|[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
        "replacement": "[REDACTED_PII]"
    },
    {
        "name": "Block Prompt Injection",
        "pattern": r"(ignore\s+previous\s+instructions|system\s+prompt|jailbreak|do\s+anything\s+now)",
        "replacement": "[REDACTED_INJECTION]"
    },
    {
        "name": "Redact Secrets",
        "pattern": r"([A-Za-z0-9+/=]{32,})",
        "replacement": "[REDACTED_SECRET]"
    },
    {
        "name": "Block Malicious Domain",
        "pattern": r"(malicious\.example|evil\.com|bad-site\.org)",
        "replacement": "[REDACTED_DOMAIN]"
    },
    {
        "name": "Block SQL Injection",
        "pattern": r"(DROP\s+TABLE|SELECT\s+\*\s+FROM|UNION\s+SELECT|--\s*$)",
        "replacement": "[REDACTED_SQL]"
    }
]

# API Functions (ready for backend - updated for groups)
def get_groups() -> List[Dict]:
    if USE_DUMMY:
        return st.session_state.dummy_groups
    try:
        response = requests.get(f"{API_BASE_URL}/groups")
        return response.json()
    except:
        return []

def create_group(group_data: Dict) -> bool:
    if USE_DUMMY:
        new_id = f"group_{len(st.session_state.dummy_groups) + 1}"
        group_data["id"] = new_id
        st.session_state.dummy_groups.append(group_data)
        return True
    try:
        response = requests.post(f"{API_BASE_URL}/groups", json=group_data)
        return response.status_code == 200
    except:
        return False

def update_group(group_id: str, group_data: Dict) -> bool:
    if USE_DUMMY:
        for i, group in enumerate(st.session_state.dummy_groups):
            if group["id"] == group_id:
                group_data["id"] = group_id
                st.session_state.dummy_groups[i] = group_data
                return True
        return False
    try:
        response = requests.put(f"{API_BASE_URL}/groups/{group_id}", json=group_data)
        return response.status_code == 200
    except:
        return False

def delete_group(group_id: str) -> bool:
    if USE_DUMMY:
        st.session_state.dummy_groups = [g for g in st.session_state.dummy_groups if g["id"] != group_id]
        return True
    try:
        response = requests.delete(f"{API_BASE_URL}/groups/{group_id}")
        return response.status_code == 200
    except:
        return False

# Commented out user-related API functions
# def get_users() -> List[Dict]:
#     if USE_DUMMY:
#         return st.session_state.dummy_users
#     try:
#         response = requests.get(f"{API_BASE_URL}/users")
#         return response.json()
#     except:
#         return []

# def create_user(user_data: Dict) -> bool:
#     if USE_DUMMY:
#         new_id = f"user_{len(st.session_state.dummy_users) + 1}"
#         user_data["id"] = new_id
#         st.session_state.dummy_users.append(user_data)
#         return True
#     try:
#         response = requests.post(f"{API_BASE_URL}/users", json=user_data)
#         return response.status_code == 200
#     except:
#         return False

# def update_user(user_id: str, user_data: Dict) -> bool:
#     if USE_DUMMY:
#         for i, user in enumerate(st.session_state.dummy_users):
#             if user["id"] == user_id:
#                 user_data["id"] = user_id
#                 st.session_state.dummy_users[i] = user_data
#                 return True
#         return False
#     try:
#         response = requests.put(f"{API_BASE_URL}/users/{user_id}", json=user_data)
#         return response.status_code == 200
#     except:
#         return False

# def delete_user(user_id: str) -> bool:
#     if USE_DUMMY:
#         st.session_state.dummy_users = [u for u in st.session_state.dummy_users if u["id"] != user_id]
#         return True
#     try:
#         response = requests.delete(f"{API_BASE_URL}/users/{user_id}")
#         return response.status_code == 200
#     except:
#         return False

# Helper functions
def reset_forms():
    st.session_state.show_add_group = False
    # st.session_state.show_add_user = False
    st.session_state.edit_group_id = None
    # st.session_state.edit_user_id = None

def render_group_form(group_data: Dict = None, is_edit: bool = False):
    with st.form(key="group_form" + ("_edit" if is_edit else "_add")):
        st.subheader("✏️ Edit Group" if is_edit else "➕ Add New Group")
        
        name = st.text_input("Group Name", value=group_data.get("name", "") if group_data else "")
        
        st.write("**Security Policies:**")
        st.write("*Select policies to include in this group*")
        
        selected_policies = []
        current_policies = group_data.get("policies", []) if group_data else []
        current_policy_names = [p["name"] for p in current_policies]
        
        for template in POLICY_TEMPLATES:
            # Check if this policy is currently active in the group
            is_active = template["name"] in current_policy_names
            
            if st.checkbox(template["name"], value=is_active, key=f"policy_{template['name']}"):
                # Find existing policy or create new one
                existing_policy = next((p for p in current_policies if p["name"] == template["name"]), None)
                
                if existing_policy:
                    selected_policies.append(existing_policy)
                else:
                    new_policy = {
                        "id": f"policy_{len(selected_policies) + 1}",
                        "name": template["name"],
                        "pattern": template["pattern"],
                        "replacement": template["replacement"],
                        "active": True
                    }
                    selected_policies.append(new_policy)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save Group"):
                if name:
                    group_data_new = {
                        "name": name,
                        "policies": selected_policies
                    }
                    
                    if is_edit:
                        if update_group(st.session_state.edit_group_id, group_data_new):
                            st.success("✅ Group updated successfully!")
                            reset_forms()
                            st.rerun()
                        else:
                            st.error("❌ Failed to update group")
                    else:
                        if create_group(group_data_new):
                            st.success("✅ Group created successfully!")
                            reset_forms()
                            st.rerun()
                        else:
                            st.error("❌ Failed to create group")
                else:
                    st.error("⚠️ Please fill in all required fields")
        
        with col2:
            if st.form_submit_button("❌ Cancel"):
                reset_forms()
                st.rerun()

# Commented out user form function
# def render_user_form(user_data: Dict = None, is_edit: bool = False):
#     groups = get_groups()
#     group_names = [group["name"] for group in groups]
    
#     with st.form(key="user_form" + ("_edit" if is_edit else "_add")):
#         st.subheader("✏️ Edit User" if is_edit else "➕ Add New User")
        
#         username = st.text_input("Username", value=user_data.get("username", "") if user_data else "")
#         description = st.text_area("Description", value=user_data.get("description", "") if user_data else "")
        
#         current_group = user_data.get("group", "") if user_data else ""
#         current_group_index = group_names.index(current_group) if current_group in group_names else 0
#         group = st.selectbox("Assign Group", group_names, index=current_group_index)
        
#         col1, col2 = st.columns(2)
#         with col1:
#             if st.form_submit_button("💾 Save User"):
#                 if username and description and group:
#                     user_data_new = {
#                         "username": username,
#                         "description": description,
#                         "group": group
#                     }
                    
#                     if is_edit:
#                         if update_user(st.session_state.edit_user_id, user_data_new):
#                             st.success("✅ User updated successfully!")
#                             reset_forms()
#                             st.rerun()
#                         else:
#                             st.error("❌ Failed to update user")
#                     else:
#                         if create_user(user_data_new):
#                             st.success("✅ User created successfully!")
#                             reset_forms()
#                             st.rerun()
#                         else:
#                             st.error("❌ Failed to create user")
#                 else:
#                     st.error("⚠️ Please fill in all required fields")
        
#         with col2:
#             if st.form_submit_button("❌ Cancel"):
#                 reset_forms()
#                 st.rerun()

# Main UI
st.title("🛡️ Policy Management")
st.markdown("---")

# Summary (updated to only show groups)
groups = get_groups()
# users = get_users()
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Groups", len(groups))
# with col2:
#     st.metric("Total Users", len(users))

st.markdown("---")

# Add buttons (only group button now)
if st.button("➕ Add Group"):
    st.session_state.show_add_group = True
    # st.session_state.show_add_user = False
    st.session_state.edit_group_id = None
    # st.session_state.edit_user_id = None
    st.rerun()

# Commented out user add button
# col1, col2 = st.columns(2)
# with col1:
#     if st.button("➕ Add Group"):
#         st.session_state.show_add_group = True
#         st.session_state.show_add_user = False
#         st.session_state.edit_group_id = None
#         st.session_state.edit_user_id = None
#         st.rerun()

# with col2:
#     if st.button("➕ Add User"):
#         st.session_state.show_add_user = True
#         st.session_state.show_add_group = False
#         st.session_state.edit_group_id = None
#         st.session_state.edit_user_id = None
#         st.rerun()

# Show forms (only group form now)
if st.session_state.show_add_group:
    render_group_form()

# if st.session_state.show_add_user:
#     render_user_form()

if st.session_state.edit_group_id:
    group_to_edit = next((g for g in groups if g["id"] == st.session_state.edit_group_id), None)
    if group_to_edit:
        render_group_form(group_to_edit, is_edit=True)

# if st.session_state.edit_user_id:
#     user_to_edit = next((u for u in users if u["id"] == st.session_state.edit_user_id), None)
#     if user_to_edit:
#         render_user_form(user_to_edit, is_edit=True)

st.markdown("---")

# Groups Section
st.subheader("🏢 Groups")
for group in groups:
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.write(f"**{group['name']}**")
            if group['policies']:
                active_policies = [p["name"] for p in group['policies'] if p.get("active", True)]
                policies_display = ", ".join(active_policies)
                st.write(f"🔒 **Active Policies**: {policies_display}")
                
                # Show policy details in expander
                with st.expander(f"View {len(group['policies'])} policies"):
                    for policy in group['policies']:
                        status = "🟢 Active" if policy.get("active", True) else "🔴 Inactive"
                        st.write(f"**{policy['name']}** - {status}")
                        st.code(f"Pattern: {policy['pattern']}")
                        st.write(f"Replacement: `{policy['replacement']}`")
                        st.write("---")
            else:
                st.write("🔒 **Policies**: None")
        
        with col2:
            if st.button("✏️", key=f"edit_group_btn_{group['id']}"):
                st.session_state.edit_group_id = group['id']
                st.session_state.show_add_group = False
                # st.session_state.show_add_user = False
                # st.session_state.edit_user_id = None
                st.rerun()
        
        st.markdown("---")

# Commented out Users Section
# st.subheader("👥 Users")
# for user in users:
#     with st.container():
#         col1, col2 = st.columns([4, 1])
        
#         with col1:
#             st.write(f"**{user['username']}**")
#             st.write(f"*{user['description']}*")
#             st.write(f"🏢 **Group**: {user['group']}")
        
#         with col2:
#             subcol1, subcol2 = st.columns(2)
#             with subcol1:
#                 if st.button("✏️", key=f"edit_user_btn_{user['id']}"):
#                     st.session_state.edit_user_id = user['id']
#                     st.session_state.show_add_group = False
#                     st.session_state.show_add_user = False
#                     st.session_state.edit_group_id = None
#                     st.rerun()
            
#             with subcol2:
#                 if st.button("🗑️", key=f"delete_user_btn_{user['id']}"):
#                     if delete_user(user['id']):
#                         st.success(f"✅ User {user['username']} deleted!")
#                         st.rerun()
#                     else:
#                         st.error("❌ Failed to delete user")
        
#         st.markdown("---")