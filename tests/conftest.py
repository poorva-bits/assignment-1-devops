import os
import tempfile

# throwaway test database for testing purposes
os.environ["ACEEST_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")