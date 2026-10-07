# Fix Root Causes

Do not add guards. Adding a nil check to silence a crash is a symptom fix.

**Restart bugs: suspect state before code**

When something "fails after restart," suspect stale persistent state first: config files, caches, lock files, serialized state. If clearing a state file restores behavior, prioritize state validation as the fix.
