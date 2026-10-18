"""Lectura, validación y almacenamiento de recetas INI."""

from configparser import ConfigParser, Error as ConfigParserError
from dataclasses import dataclass, replace
import math
import re
import unicodedata
from pathlib import Path
from typing import Optional

import config_gui.strings as text


class RecipeError(ValueError):
    """Error comprensible de formato, validación o almacenamiento de receta."""


@dataclass
class Recipe:
    name: str
    description: str
    o2_flow: float
    n2_flow: float
    base_pressure: float
    process_pressure: float
    process_temperature: float
    source_path: Optional[Path] = None


class RecipeService:
    """Opera sobre los archivos de receta junto al paquete de la aplicación."""

    TEMPLATE_FILENAME = "recipe_stardar.txt"
    PARAMETERS = (
        "o2_flow",
        "n2_flow",
        "base_pressure",
        "process_pressure",
        "process_temperature",
    )
    FLOW_LIMITS = {"o2_flow": 10.0, "n2_flow": 1.0}

    def __init__(self, recipes_directory=None):
        package_root = Path(__file__).resolve().parents[1]
        self.directory = Path(recipes_directory or package_root / "recipies").resolve()
        self.template_path = (self.directory / self.TEMPLATE_FILENAME).resolve()

    def load_template(self):
        recipe = self.load_file(self.template_path)
        return replace(recipe, name="", source_path=self.template_path)

    def load_file(self, path):
        path = Path(path).resolve()
        if path.parent != self.directory:
            raise RecipeError(text.RECIPE_ERROR_INVALID_LOCATION)
        if path.suffix.lower() != ".txt" or not path.is_file():
            raise RecipeError(text.RECIPE_ERROR_FILE_NOT_FOUND)

        parser = ConfigParser(interpolation=None)
        try:
            with path.open("r", encoding="utf-8-sig") as recipe_file:
                parser.read_file(recipe_file)
        except (OSError, UnicodeError, ConfigParserError) as error:
            raise RecipeError(text.RECIPE_ERROR_READ)

        if not parser.has_section("RECIPE") or not parser.has_section("PARAMETERS"):
            raise RecipeError(text.RECIPE_ERROR_SECTIONS)
        if not parser.has_option("RECIPE", "name") or not parser.has_option("RECIPE", "description"):
            raise RecipeError(text.RECIPE_ERROR_METADATA)

        try:
            values = {
                key: parser.getfloat("PARAMETERS", key)
                for key in self.PARAMETERS
            }
        except (ConfigParserError, ValueError) as error:
            raise RecipeError(text.RECIPE_ERROR_PARAMETERS)

        recipe = Recipe(
            name=parser.get("RECIPE", "name").strip(),
            description=parser.get("RECIPE", "description").strip(),
            source_path=path,
            **values,
        )
        self.validate(recipe, require_name=True)
        return recipe

    def validate(self, recipe, require_name=True):
        if require_name and not str(recipe.name).strip():
            raise RecipeError(text.RECIPE_ERROR_NAME_REQUIRED)
        if not isinstance(recipe.description, str) or not recipe.description.strip():
            raise RecipeError(text.RECIPE_ERROR_METADATA)

        for key in self.PARAMETERS:
            try:
                value = float(getattr(recipe, key))
            except (TypeError, ValueError) as error:
                raise RecipeError(text.RECIPE_ERROR_INVALID_VALUES) from error
            if not math.isfinite(value) or value < 0:
                raise RecipeError(text.RECIPE_ERROR_NONNEGATIVE)
            maximum = self.FLOW_LIMITS.get(key)
            if maximum is not None and value > maximum:
                raise RecipeError(
                    text.RECIPE_ERROR_O2_RANGE if key == "o2_flow"
                    else text.RECIPE_ERROR_N2_RANGE
                )

    def path_for_name(self, name):
        normalized = unicodedata.normalize("NFKD", str(name).strip())
        ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
        slug = re.sub(r"[^A-Za-z0-9_-]+", "_", ascii_name).strip("_-")
        if not slug:
            raise RecipeError(text.RECIPE_ERROR_FILENAME)
        return self.directory / f"{slug}.txt"

    def save(self, recipe, overwrite=False):
        self.validate(recipe, require_name=True)
        path = self.path_for_name(recipe.name).resolve()
        if path.parent != self.directory:
            raise RecipeError(text.RECIPE_ERROR_INVALID_LOCATION)
        if path == self.template_path:
            raise RecipeError(text.RECIPE_ERROR_TEMPLATE_PROTECTED)
        if path.exists() and not overwrite:
            raise FileExistsError(path)

        parser = ConfigParser(interpolation=None)
        parser["RECIPE"] = {
            "name": recipe.name.strip(),
            "description": recipe.description.strip(),
        }
        parser["PARAMETERS"] = {
            key: self._format_value(float(getattr(recipe, key)))
            for key in self.PARAMETERS
        }
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8", newline="\n") as recipe_file:
                parser.write(recipe_file)
        except OSError as error:
            raise RecipeError(text.RECIPE_ERROR_WRITE) from error
        return replace(recipe, source_path=path)

    @staticmethod
    def _format_value(value):
        return format(value, ".15g")
