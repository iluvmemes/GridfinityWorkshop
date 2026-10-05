"""Retired prototype registration; install the repository root add-in."""
import adsk.core

def run(context):
    adsk.core.Application.get().log('Gridfinity Workshop has moved. Disable GridfinityUIPreview in Scripts and Add-Ins, then add the GridfinityWorkshop repository folder and run it.')

def stop(context):
    pass
