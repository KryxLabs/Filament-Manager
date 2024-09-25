import os
import asyncio

import yaml
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

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
Base = declarative_base()


# Define your data model
class Filament(Base):
    __tablename__ = "filaments"
    id = Column(String, primary_key=True)
    brand = Column(String)
    material = Column(String)
    color = Column(String)
    weight = Column(Float)
    date_opened = Column(Date)
    empty = Column(Boolean)
    open = Column(Boolean)


# Create the database tables
Base.metadata.create_all(bind=engine)

from textual.app import App, Widget
from textual.widgets import (
    Header,
    Footer,
    Button,
    Label,
    Select,
    Checkbox,
    Input,
    Pretty,
    DataTable,
    SelectionList,
)
from textual.containers import Container
from textual.containers import Container
from textual.message import Message
from textual.app import ComposeResult
from datetime import date
import uuid


class FilamentAdditionSubmit(Message):
    """Message sent when the form is submitted."""

    def __init__(self, data):
        self.data = data
        super().__init__()

class FilamentUpdate(Widget):
    CSS_PATH = "styles/style.css"

   
    def compose(self) -> ComposeResult:
        self.db = SessionLocal()
        filaments = self.db.query(Filament).all()
        filament_id = ""

        self.banner = Label()
        self.title = "Filament Update"
        self.form = Container(
            Select(
                options=[(fil.id, fil.id) for fil in filaments],
                prompt="Select ID",
                id="id",
            ),
            Select(
                options=[(brand, brand) for brand in config["brands"]],
                value=self.db.get(Filament, {"id": filament_id}).brand if filament_id is not None else "Select Brand",
                id="brand",
            ),

            Select(
                options=[(material, material) for material in config["materials"]],
                value=self.db.get(Filament, {"id": filament_id}).material if filament_id is not None else "Select Material",
                id="material",
            ),

            Input(value=self.db.get(filament_id.material) if filament_id is not None else "Color", id="color"),
            Input(value=self.db.get(filament_id.material) if filament_id is not None else "Weight (grams)", type="number", id="weight"),
            Select(
                [("Empty", "Empty"), ("Open", "Open")],
                prompt="Is the filament empty or open?",
                id="empty_open",
            ),
            Button("Submit", id="submit"),
            id="addition_form",
        )
        yield self.form

        


    async def on_button_pressed(self, event):
        if event.button.id == "submit":
            brand = self.query_one("#brand", Select).value
            material = self.query_one("#material", Select).value
            color = self.query_one("#color", Input).value
            weight_str = self.query_one("#weight", Input).value
            is_empty_or_open = self.query_one("#empty_open", Select).value
            id = str(uuid.uuid4())[:8]

            if (
                brand == Select.BLANK
                or material == Select.BLANK
                or color == ""
                or weight_str == ""
            ):
                return

            if is_empty_or_open == "empty":
                empty = True
                open = True
            elif is_empty_or_open == "open":
                empty = False
                open = True
            else:
                empty = False
                open = False

            data = {
                "brand": str(brand),
                "material": str(material),
                "color": str(color),
                "weight": weight,
                "empty": empty,
                "open": open,
                "id": str(id),
            }

            # Post the message
            self.post_message(FilamentAdditionSubmit(data))
            await self.remove()


class FilamentDatabaseView(Widget):
    CSS_PATH = "styles/style.css"

    def compose(self) -> ComposeResult:
        self.database_view = Container(
            DataTable(), Button("Back to Menu", id="menu"), id="database_view"
        )

        yield self.database_view

    async def on_button_pressed(self, event):
        if event.button.id == "menu":
            await self.remove()

    async def on_mount(self):
        self.db = SessionLocal()
        self.title = "Filament Manager"
        self.sub_title = config.get("version", config["version"])
        table = self.query_one(DataTable)
        ROWS = await self.GatherEntries()
        table.add_columns(*ROWS[0])
        table.add_rows(ROWS[1:])

    async def GatherEntries(self) -> list:
        filaments = self.db.query(Filament).all()
        if not filaments:
            return [("no", "filaments", "in", "the", "current", "database", "", ""), ()]
        ROWS = [
            (
                "ID",
                "Brand",
                "Material",
                "Color",
                "Weight",
                "Date Opened",
                "Open",
                "Empty",
            )
        ]
        for i, fil in enumerate(filaments):
            ROWS.append(
                (
                    fil.id,
                    fil.brand,
                    fil.material,
                    fil.color,
                    fil.weight,
                    fil.date_opened,
                    f"{'Yes' if fil.open == True else 'No'}",
                    f"{'Yes' if fil.empty == True else 'No'}",
                )
            )
        return ROWS


class FilamentAddition(Widget):
    CSS_PATH = "styles/style.css"

    def compose(self) -> ComposeResult:
        self.banner = Label()
        self.title = "Filament Addition"
        self.form = Container(
            Select(
                options=[(brand, brand) for brand in config["brands"]],
                prompt="Select Brand",
                id="brand",
            ),
            Select(
                options=[(material, material) for material in config["materials"]],
                prompt="Select Material",
                id="material",
            ),
            Input(placeholder="Color", id="color"),
            Input(placeholder="Weight (grams)", type="number", id="weight"),
            Select(
                [("Empty", "Empty"), ("Open", "Open")],
                prompt="Is the filament empty or open?",
                id="empty_open",
            ),
            Button("Submit", id="submit"),
            id="addition_form",
        )
        yield self.form

    async def on_button_pressed(self, event):
        if event.button.id == "submit":
            brand = self.query_one("#brand", Select).value
            material = self.query_one("#material", Select).value
            color = self.query_one("#color", Input).value
            weight_str = self.query_one("#weight", Input).value
            is_empty_or_open = self.query_one("#empty_open", Select).value
            id = str(uuid.uuid4())[:8]

            if (
                brand == Select.BLANK
                or material == Select.BLANK
                or color == ""
                or weight_str == ""
            ):
                return

            if is_empty_or_open == "empty":
                empty = True
                open = True
            elif is_empty_or_open == "open":
                empty = False
                open = True
            else:
                empty = False
                open = False

            data = {
                "brand": str(brand),
                "material": str(material),
                "color": str(color),
                "weight": weight_str,
                "empty": empty,
                "open": open,
                "id": str(id),
            }

            # Post the message
            self.post_message(FilamentAdditionSubmit(data))
            await self.remove()


import asyncio

# Import Textual and other required modules
from textual.app import App, Widget
from textual.widgets import Header, Footer, Button, Label, Select, Checkbox, Input
from textual.containers import Container
from textual.containers import Container
from textual.message import Message
from textual.app import ComposeResult
from datetime import date
import uuid


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
        self.filament_form = FilamentAddition()
        await self.mount(self.filament_form)

    async def on_filament_addition_submit(self, message: FilamentAdditionSubmit):
        data = message.data

        # Save the data to the database
        try:
            data["date_opened"] = date.today()
            filament = Filament(**data)
            self.db.add(filament)
            self.db.commit()
            await self.show_confirmation_message(data)
        except SQLAlchemyError as e:
            self.db.rollback()
            import sys

            sys.exit(e)

    async def show_confirmation_message(self, message: dict):
        self.statistics.update(message)

    async def view_inventory(self):
        self.database_view = FilamentDatabaseView()
        await self.mount(self.database_view)

    async def update_inventory(self):
        self.update_view = FilamentUpdate()
        await self.mount(self.update_view)

    async def post_notif(self, notif):
        self.statistics.update(notif)


if __name__ == "__main__":
    FilamentManagerApp().run()
