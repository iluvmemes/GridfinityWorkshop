"""Fusion entry point for the Gridfinity Workshop palettes."""
import adsk.core
import traceback
from .workshop import app

def run(context):
    try:
        app.start()
    except Exception:
        adsk.core.Application.get().log(traceback.format_exc())
        app.stop(context)
        raise

def stop(context):
    app.stop(context)
