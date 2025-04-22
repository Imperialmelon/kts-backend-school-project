from app.web.app import View
from app.web.utils import json_response, check_admin_credentials
from app.admin.schemes import AdminLoginSchema, AdminResponseSchema, AdminSchema, OkResponseSchema
from aiohttp_apispec import docs, request_schema, response_schema
from aiohttp_session import new_session, get_session
from aiohttp.web_exceptions import HTTPForbidden, HTTPUnauthorized
from app.web.decorators import login_required


class AdminLoginView(View):
    @docs(tags=['admin'], summary = 'Admin login')
    @request_schema(AdminLoginSchema)
    @response_schema(AdminResponseSchema,200)
    async def post(self):
        email = self.data['email']
        admin = await self.store.admin_accessor.get_by_email(email=email)
        if not check_admin_credentials(admin=admin, password=self.data["password"]):
            raise HTTPForbidden(reason="Invalid credentials")
        session = await new_session(self.request)
        session['admin_email'] = email
        return json_response(data=AdminSchema().dump(admin))
    

    @docs(tags=['admin'], summary = 'Admin logout')
    @response_schema(OkResponseSchema, 200)
    async def delete(self):
        session = await get_session(self.request)
        if 'admin_email' in session:
            del session['admin_email']
        return json_response(data={})
    



