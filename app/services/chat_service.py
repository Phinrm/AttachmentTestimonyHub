class ChatService:
    def get_response(self, message):
        message = message.lower()
        if "help" in message:
            return "How can I assist you today?"
        elif "testimony" in message:
            return "To add a testimony, go to the Testimonies page and fill out the form."
        else:
            return "I'm here to help! Please ask about testimonies or the app."