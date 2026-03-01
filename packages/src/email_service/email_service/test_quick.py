from email_classifier import email_classifier

print("Testing email_classifier...")
try:
    result = email_classifier(
        email_content="Quick test email about a meeting",
        sender_info="test@example.com"
    )
    print("Success:", result)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
