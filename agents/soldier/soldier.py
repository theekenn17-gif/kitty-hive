from core.telemetry import telemetry
import asyncio

def soldier_execute(task: str):

    cpu = asyncio.run(telemetry.get_radiograph_cpu())
    gpu = asyncio.run(telemetry.get_radiograph_gpu())

    alerts = []

    if "temperature" in str(cpu).lower():
        alerts.append("CPU sensor active")

    if "temperature" in str(gpu).lower():
        alerts.append("GPU sensor active")

    return f"""
🐝 SOLDIER REPORT

CPU:
{cpu}

GPU:
{gpu}

ALERTS:
{alerts if alerts else "None"}

STATUS:
Monitoring active
"""
