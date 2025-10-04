"""
Seed script to create initial groups and policies for testing
"""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from policy_controller import (
    create_group, create_policy, add_policy_to_group,
    GroupIn, PolicyIn
)

async def seed_data():
    """Create sample groups and policies for testing"""
    
    print("🌱 Seeding initial data...")
    
    # Create policies
    policies = [
        PolicyIn(
            name="PII Email Redaction",
            pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            replacement='[REDACTED_EMAIL]',
            active=True
        ),
        PolicyIn(
            name="SSN Redaction", 
            pattern=r'\b\d{3}-\d{2}-\d{4}\b',
            replacement='[REDACTED_SSN]',
            active=True
        ),
        PolicyIn(
            name="Prompt Injection Block",
            pattern=r'\b(ignore\s+previous\s+instructions|system\s+prompt|jailbreak)\b',
            replacement='[BLOCKED]',
            active=True
        ),
        PolicyIn(
            name="API Key Redaction",
            pattern=r'\b(sk-|AKIA)[A-Za-z0-9+/=]{16,}\b',
            replacement='[REDACTED_API_KEY]',
            active=True
        ),
        PolicyIn(
            name="Credit Card Redaction",
            pattern=r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            replacement='[REDACTED_CC]',
            active=True
        )
    ]
    
    created_policies = []
    for policy in policies:
        try:
            created = await create_policy(policy)
            created_policies.append(created)
            print(f"✅ Created policy: {policy.name}")
        except Exception as e:
            print(f"❌ Failed to create policy {policy.name}: {e}")
    
    # Create groups
    groups = [
        GroupIn(name="Admin Group"),
        GroupIn(name="Developer Group"), 
        GroupIn(name="Basic User Group"),
        GroupIn(name="Marketing Team"),
        GroupIn(name="Customer Support")
    ]
    
    created_groups = []
    for group in groups:
        try:
            created = await create_group(group)
            created_groups.append(created)
            print(f"✅ Created group: {group.name}")
        except Exception as e:
            print(f"❌ Failed to create group {group.name}: {e}")
    
    # Assign policies to groups
    if created_groups and created_policies:
        try:
            # Admin Group - all policies
            admin_group = created_groups[0]
            for policy in created_policies:
                await add_policy_to_group(admin_group.id, policy.id)
            print(f"✅ Assigned all policies to {admin_group.name}")
            
            # Developer Group - PII and API key protection
            dev_group = created_groups[1]
            for policy in created_policies[:2] + created_policies[3:4]:  # Email, SSN, API Key
                await add_policy_to_group(dev_group.id, policy.id)
            print(f"✅ Assigned PII policies to {dev_group.name}")
            
            # Basic User Group - basic PII protection
            basic_group = created_groups[2]
            for policy in created_policies[:2]:  # Email, SSN only
                await add_policy_to_group(basic_group.id, policy.id)
            print(f"✅ Assigned basic policies to {basic_group.name}")
            
        except Exception as e:
            print(f"❌ Failed to assign policies: {e}")
    
    print("🎉 Data seeding completed!")
    print("\nCreated Groups:")
    for group in created_groups:
        print(f"  - {group.name} (ID: {group.id})")
    
    print("\nCreated Policies:")
    for policy in created_policies:
        print(f"  - {policy.name} (ID: {policy.id})")

if __name__ == "__main__":
    asyncio.run(seed_data())