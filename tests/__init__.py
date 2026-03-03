import os

# set config.env to "test" for pytest to prevent logging to file in utils.setup_logging()
os.environ["MEMORYHUB_ENV"] = "test"
os.environ.setdefault("BASIC_MEMORY_ENV", "test")
