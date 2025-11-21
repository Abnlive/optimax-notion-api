from dotenv import load_dotenv
import os

load_dotenv()

print("MAIN_PAGE_ID =", os.getenv("MAIN_PAGE_ID"))
