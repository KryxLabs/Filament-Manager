import os
import uuid
from datetime import datetime

import yaml
from sqlalchemy import create_engine, Column, String, Float, Boolean, Date
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, declarative_base
from textual.app import App, Widget
from textual.app import ComposeResult
from textual.containers import Container
from textual.message import Message
from textual.widgets import (
    Header,
    Footer,
    Button,
    Label,
    Select,
    Input,
    Pretty,
    DataTable,
)

from filament_manager.models import Filament
from filament_manager.widgets import (
    FilamentAddition,
    FilamentAdditionSubmit,
    FilamentUpdateSubmit,
    FilamentDatabaseView,
    FilamentUpdate,
)

# Load configuration from config.yaml
with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

DATABASE_URL = config["database"]["url"]

# Ensure the data directory exists
data_dir = os.path.dirname(DATABASE_URL.replace("sqlite:///", "", 1))
os.makedirs(data_dir, exist_ok=True)

# Set up the database engine and session
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

# Define your data model


# Create the database tables


# Import Textual and other required modules


class FilamentManagerApp(App):
    CSS_PATH = "styles/style.css"

    def compose(self):
        yield Header()
        yield Footer()
        self.statistics = Pretty("", id="statistics")
        # Main container to hold the placeholder box and button container
        self.main_container = Container(
            self.statistics,
            Container(
                Button("Add Filament", id="add_filament"),
                Button("Update Inventory", id="update_inventory"),
                Button("View Inventory", id="view_inventory"),
                Button("Exit", id="exit"),
                id="button_container",
            ),
            id="main_container",
        )
        yield self.main_container

    async def on_mount(self):
        self.db = SessionLocal()
        self.title = "Filament Manager"
        self.sub_title = config.get("version", config["version"])

    async def on_button_pressed(self, event):
        if event.button.id == "add_filament":
            await self.add_filament()
        elif event.button.id == "view_inventory":
            await self.view_inventory()
        elif event.button.id == "update_inventory":
            await self.update_inventory()
        elif event.button.id == "exit":
            self.exit()

    async def add_filament(self):
        self.filament_form = FilamentAddition(
            config=config, db_session=self.db)
        await self.mount(self.filament_form)

    async def on_filament_addition_submit(self, message: FilamentAdditionSubmit):
        data = message.data

        # Save the data to the database
        try:
            filament = Filament(**data)
            self.db.add(filament)
            self.db.commit()
            await self.show_confirmation_message(data)
        except SQLAlchemyError as e:
            self.db.rollback()
            import sys

            sys.exit(e)

    async def on_filament_update_submit(self, message: FilamentUpdateSubmit):
        data = message.data

        try:
            # Create the insert statement
            stmt = insert(Filament).values(**data)

            # On conflict (for example, conflict on 'id'), update the existing record
            stmt = stmt.on_conflict_do_update(
                # Assuming 'id' is the unique constraint
                index_elements=["id"],
                # Fields to update
                set_={key: stmt.excluded[key]
                      for key in data.keys() if key != "id"},
            )

            # Execute the upsert operation
            self.db.execute(stmt)
            self.db.commit()

            await self.show_confirmation_message(data)

        except SQLAlchemyError as e:
            self.db.rollback()
            import sys

            sys.exit(e)

    async def show_confirmation_message(self, message: dict):
        self.statistics.update(message)

    async def view_inventory(self):
        self.database_view = FilamentDatabaseView(
            config=config, db_session=self.db)
        await self.mount(self.database_view)

    async def update_inventory(self):
        self.update_view = FilamentUpdate(config=config, db_session=self.db)
        await self.mount(self.update_view)

    async def post_notif(self, notif):
        self.statistics.update(notif)


if __name__ == "__main__":
    FilamentManagerApp().run()
