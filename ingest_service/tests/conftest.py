import os

# Provide a dummy DATABASE_URL so pydantic Settings can initialize during imports.
os.environ.setdefault("DATABASE_URL", "postgresql://iot:iotpass@localhost:5432/iot")


