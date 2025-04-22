from app.web.app import View
from app.web.utils import json_response


class TestView(View):
    async def get(self):
        return json_response(data={"message": "Hello, world!"})
