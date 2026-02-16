from google import genai
client = genai.Client(api_key="AIzaSyAmvLHhjYwbcAtGZshMEUaJsBAMgowQopM")
for m in client.models.list():
    print(m.name)