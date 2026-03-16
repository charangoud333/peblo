
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')

prompt = '''Return ONLY a valid JSON array. No markdown. No explanation.
[
  {\"question\": \"test\", \"type\": \"MCQ\", \"options\": [\"a\",\"b\",\"c\",\"d\"], \"answer\": \"a\", \"difficulty\": \"easy\"}
]
Now generate 3 questions about plants from this text:
Plants make food using sunlight, water and carbon dioxide in a process called photosynthesis.
'''

r = model.generate_content(prompt)
print(repr(r.text))
