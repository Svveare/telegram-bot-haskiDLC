import time

class ThrottlingMiddleware:
    def __init__(self, delay=0.5):
        self.delay = delay
        self.users = {}

    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        now = time.time()

        last_time = self.users.get(user_id, 0)

        if now - last_time < self.delay:
            return

        self.users[user_id] = now
        return await handler(event, data)