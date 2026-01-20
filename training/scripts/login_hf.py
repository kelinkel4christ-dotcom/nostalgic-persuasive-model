from huggingface_hub import login

print("Logging in to Hugging Face...")
print("Please retrieve your token from: https://huggingface.co/settings/tokens")
print("(Make sure it's a 'Write' token)")
print("-" * 50)

login()

print("-" * 50)
print("Login successful! Now you can run the upload script.")
