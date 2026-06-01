from email_utils import send_reset_email

success = send_reset_email(
    "ummanenibalaji@gmail.com",
    "TEST_TOKEN_123"
)

print(success)