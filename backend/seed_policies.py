import asyncio
from policy_controller import (
    create_policy, create_group, add_policy_to_group,
    PolicyIn, GroupIn
)

async def seed():
    # 1. Create Group
    group = await create_group(GroupIn(name="Role 0"))
    print("✅ Created Group:", group)

    # 2. Create Policies
    p1 = await create_policy(PolicyIn(
        name="Redact PII",
        pattern=r"(\b\d{3}-\d{2}-\d{4}\b|\b\d{3}-\d{3}-\d{4}\b|[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
        replacement="[REDACTED_PII]",
        active=True,
        type="redact"
    ))

    p2 = await create_policy(PolicyIn(
        name="Block Prompt Injection",
        pattern=r"(ignore\s+previous\s+instructions|system\s+prompt|jailbreak|do\s+anything\s+now)",
        replacement="[REDACTED_INJECTION]",
        active=True,
        type="block"
    ))

    p3 = await create_policy(PolicyIn(
        name="Redact Secrets",
        pattern=r"([A-Za-z0-9+/=]{32,})",
        replacement="[REDACTED_SECRET]",
        active=True,
        type="redact"
    ))

    print("✅ Policies created:", p1, p2, p3)

    # 3. Attach Policies to Group
    await add_policy_to_group(group.id, p1.id)
    await add_policy_to_group(group.id, p2.id)
    await add_policy_to_group(group.id, p3.id)

    print(f"🎉 Group '{group.name}' now has 3 policies attached.")

if __name__ == "__main__":
    asyncio.run(seed())
