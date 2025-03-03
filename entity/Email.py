class Email:
    def __init__(self, sender: str, date: str, subject: str, body: str, email_address: str, unique_id: str):
        self.sender_name = sender
        self.date = date
        self.subject = subject
        self.body = body
        self.sender_email = email_address
        self.unique_id = unique_id

    def __repr__(self):
        return f"Email(sender_name={self.sender_name}, date={self.date}, subject={self.subject}, sender_email={self.sender_email}, unique_id={self.unique_id})"
