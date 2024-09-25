import uuid
from datetime import datetime

from sqlalchemy.orm import Session
from textual import events
from textual.app import ComposeResult
from textual.app import Widget
from textual.containers import Container
from textual.message import Message
from textual.widgets import (
    Button,
    Label,
    Select,
    Input,
    DataTable,
)

from filament_manager.models import Filament


class SQLWidget(Widget):
    def __init__(self, db_session: Session, config: None, data=None):
        super().__init__()
        self.db_session = db_session
        if data is None:
            self.data = {}
        if config is None:
            self.remove()
        self.config = config

    async def _on_key(self, event: events.Key) -> None:
        if event.key.lower() == "escape":
            await self.remove()


class FilamentAdditionSubmit(Message):
    """Message sent when the form is submitted."""

    def __init__(self, data):
        self.data = data
        super().__init__()


class FilamentUpdateSubmit(Message):
    """Message sent when the form is updated."""

    def __init__(self, data):
        self.data = data
        super().__init__()


class FilamentUpdate(SQLWidget):
    CSS_PATH = "styles/style.css"
    confirm_exit = False

    def compose(self) -> ComposeResult:
        filaments = self.db_session.query(Filament).all()
        self.filament_id = None  # Initialize filament_id

        self.banner = Label()
        self.title = "Filament Update"
        self.form = Container(
            Select(
                options=[
                    (str(fil.id), str(fil.id)) for fil in filaments
                ],  # Make sure IDs are strings
                prompt="Select ID",
                id="id",
            ),
            Select(
                prompt="Select Brand",
                options=[(brand, brand) for brand in self.config["brands"]],
                value=Select.BLANK,
                id="brand",
            ),
            Select(
                prompt="Select Material",
                options=[(material, material)
                         for material in self.config["materials"]],
                value=Select.BLANK,
                id="material",
            ),
            Input(placeholder="Color", id="color"),
            Input(placeholder="Weight (grams)", type="number", id="weight"),
            Select(
                options=[("Empty", "Empty"), ("Open", "Open")],
                prompt="Is the filament empty or open?",
                id="empty_open",
            ),
            Input(placeholder="Date opened in YYYY-MM-DD", id="date"),
            Button("Submit", id="submit"),
            id="update_form",
        )
        yield self.form

    async def on_select_changed(self, event: Select.Changed) -> None:
        """Handle when the filament ID is changed."""
        if event.select.id == "id":
            filament_id = self.query_one("#id", Select).value
            if filament_id:  # Only proceed if a valid filament_id is selected
                self.update_form_fields(filament_id)

    def update_form_fields(self, filament_id):
        """Update form fields based on the selected filament ID."""
        filament = self.db_session.get(Filament, {"id": filament_id})

        if filament:
            # Update the brand and material fields based on the selected filament
            self.app.notify(
                message="Found existing record!", title="Info", severity="information"
            )

            self.query_one("#brand", Select).value = filament.brand
            self.query_one("#material", Select).value = filament.material
            self.query_one("#color", Input).value = filament.color
            self.query_one("#weight", Input).value = str(filament.weight)
            # Optionally handle empty_open field based on filament properties
            self.query_one("#date", Input).value = str(filament.date_opened)
            self.query_one("#empty_open", Select).value = (
                "Empty" if filament.empty else "Open"
            )
        else:
            # Reset fields if no filament is found
            self.app.notify(
                message="Invalid Record? What did you do lol",
                title="Error!",
                severity="error",
            )

    async def on_button_pressed(self, event):
        if event.button.id == "submit":
            brand = self.query_one("#brand", Select).value
            material = self.query_one("#material", Select).value
            color = self.query_one("#color", Input).value
            weight_str = self.query_one("#weight", Input).value
            is_empty_or_open = self.query_one("#empty_open", Select).value
            id = self.query_one("#id", Select).value

            if (
                    brand == Select.BLANK
                    or material == Select.BLANK
                    or color == ""
                    or weight_str == ""
            ):
                if self.confirm_exit:
                    await self.remove()
                self.app.notify(
                    message="Missing field! Press again to exit",
                    title="Error!",
                    severity="error",
                )
                self.confirm_exit = True
                return

            try:
                date_str = self.query_one("#date", Input).value
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                if self.confirm_exit:
                    await self.remove()
                self.app.notify(
                    message="Invalid Date Format! Press again to exit",
                    title="Error!",
                    severity="error",
                )
                self.confirm_exit = True
                return

            empty = is_empty_or_open == "Empty"
            open = is_empty_or_open == "Open"

            data = {
                "brand": str(brand),
                "material": str(material),
                "color": str(color),
                "weight": weight_str,
                "empty": empty,
                "open": open,
                "date_opened": date,
                "id": str(id),
            }

            # Post the message
            self.post_message(FilamentUpdateSubmit(data))
            await self.remove()


class FilamentDatabaseView(SQLWidget):
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
        self.title = "Filament Manager"
        self.sub_title = self.config.get("version", self.config["version"])
        table = self.query_one(DataTable)
        ROWS = await self.GatherEntries()
        table.add_columns(*ROWS[0])
        table.add_rows(ROWS[1:])

    async def GatherEntries(self) -> list:
        filaments = self.db_session.query(Filament).all()
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


class FilamentAddition(SQLWidget):
    CSS_PATH = "styles/style.css"
    confirm_exit = False

    def compose(self) -> ComposeResult:
        self.banner = Label()
        self.title = "Filament Addition"
        self.form = Container(
            Select(
                options=[(brand, brand) for brand in self.config["brands"]],
                prompt="Select Brand",
                id="brand",
            ),
            Select(
                options=[(material, material)
                         for material in self.config["materials"]],
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
            Input(placeholder="Date in YYYY-MM-DD, blank for today", id="date"),
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
            date_str = self.query_one("#date", Input).value.strip()
            id = str(uuid.uuid4())[:8]
            while self.db_session.get(Filament, {"id": id}):
                id = str(uuid.uuid4())[:8]
            if (
                    brand == Select.BLANK
                    or material == Select.BLANK
                    or color == ""
                    or weight_str == ""
            ):
                if self.confirm_exit:
                    await self.remove()
                self.app.notify(
                    message="Missing field! Press again to exit",
                    title="Error!",
                    severity="error",
                )
                self.confirm_exit = True
                return
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                if self.confirm_exit:
                    await self.remove()
                self.app.notify(
                    message="Invalid Date Format! Press again to exit",
                    title="Error!",
                    severity="error",
                )
                self.confirm_exit = True
                return

            empty = is_empty_or_open == "Empty"
            open = is_empty_or_open == "Open"

            data = {
                "brand": str(brand),
                "material": str(material),
                "color": str(color),
                "weight": weight_str,
                "empty": empty,
                "open": open,
                "date_opened": date,
                "id": str(id),
            }

            # Post the message
            self.post_message(FilamentAdditionSubmit(data))
            await self.remove()
