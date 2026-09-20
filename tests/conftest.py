import os
import pytest

# Ensure tests use isolated local SQLite database to prevent wiping live Supabase data
os.environ["DATABASE_URL"] = "sqlite:///./test_echoreach.db"
