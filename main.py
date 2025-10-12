import json

def get_email():
    """Reads and returns the email from email.json.txt."""
    with open("email.json.txt", "r") as f:
        data = json.load(f)
    return data.get("email")

if __name__ == "__main__":
    email = get_email()
    if email:
        print(f"The email is: {email}")
    else:
        print("Email not found.")