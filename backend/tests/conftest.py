import os


# Unit/integration tests verify fallback behavior without loading a large local model.
# Semantic mode is covered by runtime status and manual acceptance steps.
os.environ.setdefault("EMBEDDING_PROVIDER", "hashing")
os.environ.setdefault("LLM_PROVIDER", "mock")
