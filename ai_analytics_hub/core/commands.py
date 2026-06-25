import click
from flask import current_app

from ai_analytics_hub.core.extensions import db
from ai_analytics_hub.services.auth_service import (
    create_user,
    ensure_default_admin,
    list_users,
    reset_user_password,
    update_user_email,
    update_user_role,
)


def register_commands(app) -> None:
    @app.cli.command("init-db")
    def init_db_command() -> None:
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("seed-admin")
    def seed_admin_command() -> None:
        db.create_all()
        user = ensure_default_admin(
            current_app.config["DEFAULT_ADMIN_EMAIL"],
            current_app.config["DEFAULT_ADMIN_PASSWORD"],
        )
        click.echo(f"Admin user ready: {user.email}")

    @app.cli.command("create-user")
    @click.option("--email", prompt=True)
    @click.option("--full-name", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    @click.option(
        "--role",
        default="analyst",
        type=click.Choice(["admin", "analyst", "viewer"], case_sensitive=False),
    )
    def create_user_command(email: str, full_name: str, password: str, role: str) -> None:
        db.create_all()
        user = create_user(email=email, full_name=full_name, password=password, role=role)
        click.echo(f"Created user {user.email} with role {user.role}.")

    @app.cli.command("list-users")
    def list_users_command() -> None:
        db.create_all()
        users = list_users()
        if not users:
            click.echo("No users found.")
            return

        click.echo("ID | Email | Full Name | Role | Active | Password")
        for user in users:
            click.echo(
                f"{user.id} | {user.email} | {user.full_name} | "
                f"{user.role} | {user.is_active} | stored as secure hash"
            )

    @app.cli.command("update-user-email")
    @click.option("--current-email", prompt=True)
    @click.option("--new-email", prompt=True)
    def update_user_email_command(current_email: str, new_email: str) -> None:
        db.create_all()
        user = update_user_email(current_email=current_email, new_email=new_email)
        click.echo(f"Updated email. User is now {user.email}.")

    @app.cli.command("update-user-role")
    @click.option("--email", prompt=True)
    @click.option(
        "--role",
        prompt=True,
        type=click.Choice(["admin", "analyst", "viewer"], case_sensitive=False),
    )
    def update_user_role_command(email: str, role: str) -> None:
        db.create_all()
        user = update_user_role(email=email, role=role)
        click.echo(f"Updated role. {user.email} is now {user.role}.")

    @app.cli.command("reset-user-password")
    @click.option("--email", prompt=True)
    @click.option("--new-password", prompt=True, hide_input=True, confirmation_prompt=True)
    def reset_user_password_command(email: str, new_password: str) -> None:
        db.create_all()
        user = reset_user_password(email=email, new_password=new_password)
        click.echo(f"Password reset for {user.email}.")
