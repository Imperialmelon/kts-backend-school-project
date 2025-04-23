from aiohttp.web_app import Application

__all__ = ("setup_routes",)


def setup_routes(application: Application):
    from app.admin.routes import setup_routes as admin_setup_routes

    admin_setup_routes(application)
