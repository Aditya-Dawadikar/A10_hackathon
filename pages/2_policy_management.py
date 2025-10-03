import streamlit as st
import requests
import json
from typing import Dict, List, Optional
from pydantic import BaseModel

class PolicyIn(BaseModel):
    name: str
    pattern: str
    replacement: str
    active: bool = True

class GroupIn(BaseModel):
    name: str
    policies: List[str] = []  # List of policy IDs

st.set_page_config(page_title="Policy Management", page_icon="🛡️", layout="wide")

# Configuration
API_BASE_URL = "http://localhost:8000"

# API Functions
def get_all_groups():
    try:
        # Get list of all groups using group endpoint
        response = requests.get(f"{API_BASE_URL}/groups")

        print(response.json())  # Debugging line to print the response

        if response.status_code == 200:
            result = response.json()
            # If a single group is returned, wrap it in a list
            if isinstance(result, dict):
                return [result]
            return result
        elif response.status_code == 404:
            return []
        else:
            st.error(f"Error fetching groups: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return []

def create_new_group(group_data):
    try:
        response = requests.post(f"{API_BASE_URL}/group", json=group_data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error creating group: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

def get_group_details(group_id=None, name=None):
    try:
        params = {}
        if group_id:
            params['groupId'] = group_id
        if name:
            params['name'] = name
        response = requests.get(f"{API_BASE_URL}/group", params=params)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            st.error(f"Error fetching group details: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

def add_policy_to_group(group_id, policy_id):
    try:
        response = requests.post(f"{API_BASE_URL}/group/{group_id}/add/{policy_id}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error adding policy to group: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

def remove_policy_from_group(group_id, policy_id):
    try:
        response = requests.delete(f"{API_BASE_URL}/group/{group_id}/remove/{policy_id}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error removing policy from group: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

def create_new_policy(policy_data):
    try:
        response = requests.post(f"{API_BASE_URL}/policy", json=policy_data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error creating policy: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

# Initialize session state
if "groups" not in st.session_state:
    st.session_state.groups = get_all_groups()

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

# Policies will be fetched from the API

# Get the current groups from session state or API
def get_groups() -> List[Dict]:
    try:
        # Refresh groups from API
        groups = get_all_groups()
        print("+++++++++++here+++++++++++++++++")
        print(groups)
        st.session_state.groups = groups
        return groups
    except Exception as e:
        st.error(f"Error getting groups: {str(e)}")
        return st.session_state.get('groups', [])

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

def get_available_policies():
    try:
        response = requests.get(f"{API_BASE_URL}/policies")
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return []
        else:
            st.error(f"Error fetching policies: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return []

def delete_group(group_id: str) -> bool:
    try:
        response = requests.delete(f"{API_BASE_URL}/group/{group_id}")
        if response.status_code == 200:
            return True
        else:
            st.error(f"Error deleting group: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return False

def render_group_form(group_data: Dict = None, is_edit: bool = False):
    with st.form(key="group_form" + ("_edit" if is_edit else "_add")):
        st.subheader("✏️ Edit Group" if is_edit else "➕ Add New Group")
        
        name = st.text_input("Group Name", value=group_data.get("name", "") if group_data else "")
        
        st.write("**Security Policies:**")
        st.write("*Select policies to include in this group*")
        
        selected_policies = []
        current_policies = group_data.get("policies", []) if group_data else []
        current_policy_names = [p["name"] for p in current_policies]
        
        # Fetch available policies from API
        available_policies = get_available_policies()
        
        for policy in available_policies:
            # Check if this policy is currently active in the group
            is_active = policy["name"] in current_policy_names
            
            if st.checkbox(policy["name"], value=is_active, key=f"policy_{policy['name']}"):
                # Find existing policy or create new one
                existing_policy = next((p for p in current_policies if p["name"] == policy["name"]), None)
                
                if existing_policy:
                    selected_policies.append(existing_policy)
                else:
                    selected_policies.append(policy)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save Group"):
                if name:
                    group_data_new = GroupIn(
                        name=name,
                        policies=[p["id"] for p in selected_policies]
                    )
                    
                    if is_edit:
                        try:
                            # Update policies in a single API call
                            response = requests.put(
                                f"{API_BASE_URL}/{st.session_state.edit_group_id}/policies",
                                json={"policy_ids": group_data_new.policies}
                            )
                            if response.status_code == 200:
                                st.success("✅ Group updated successfully!")
                                reset_forms()
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to update group: {response.status_code}")
                        except Exception as e:
                            st.error(f"❌ Failed to update group: {str(e)}")
                    else:
                        try:
                            # First create the group
                            group = create_new_group({"name": name})
                            if group:
                                # Then update its policies
                                response = requests.put(
                                    f"{API_BASE_URL}/{group['id']}/policies",
                                    json={"policy_ids": group_data_new.policies}
                                )
                                if response.status_code == 200:
                                    st.success("✅ Group created successfully!")
                                    reset_forms()
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to attach policies: {response.status_code}")
                            else:
                                st.error("❌ Failed to create group")
                        except Exception as e:
                            st.error(f"❌ Failed to create group: {str(e)}")
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
print("++++++++++++++++++++++++++++")
print(groups)
for group in groups:
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.write(f"**{group['name']}**")
            group_policies = group.get('policies', [])
            
            if group_policies:
                active_policies = [p["name"] for p in group_policies if p.get("active", True)]
                policies_display = ", ".join(active_policies) if active_policies else "None"
                st.write(f"🔒 **Active Policies**: {policies_display}")
                
                # Show policy details in expander
                with st.expander(f"View {len(group_policies)} policies"):
                    for policy in group_policies:
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
                st.rerun()
            
            # Add a delete button
            if st.button("🗑️", key=f"delete_group_btn_{group['id']}"):
                if delete_group(group['id']):
                    st.success("✅ Group deleted successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to delete group")
        
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