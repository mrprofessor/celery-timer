from flask import Flask
from celery import Celery
from celery.utils.log import get_task_logger
import redis

logger = get_task_logger(__name__)
app = Flask(__name__)

# Add Redis configs
app.config["CELERY_BROKER_URL"] = "redis://redis:6379/0"
app.config["CELERY_RESULT_BACKEND"] = "redis://redis:6379/0"

# Connect Redis db
redis_db = redis.Redis(
    host="redis", port="6379", db=1, charset="utf-8", decode_responses=True
)

# Initialize timer in redis
redis_db.mset({"minute": 0, "second": 0})

# Add periodic tasks
celery_beat_schedule = {
    "time_scheduler": {
        "task": "app.timer",
        # Run every second
        "schedule": 1.0,
    }
}

# Initialize Celery and update its config
celery = Celery(app.name)
celery.conf.update(
    result_backend=app.config["CELERY_RESULT_BACKEND"],
    broker_url=app.config["CELERY_BROKER_URL"],
    timezone="UTC",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    beat_schedule=celery_beat_schedule,
)


@app.route("/")
def index_view():
    return "Flask-celery task scheduler!"


@app.route("/timer")
def timer_view():
    time_counter = redis_db.mget(["minute", "second"])
    return f"Minute: {time_counter[0]}, Second: {time_counter[1]}"


@celery.task
def timer():
    second_counter = int(redis_db.get("second")) + 1
    if second_counter >= 59:
        # Reset the counter
        redis_db.set("second", 0)
        # Increment the minute
        redis_db.set("minute", int(redis_db.get("minute")) + 1)
    else:
        # Increment the second
        redis_db.set("second", second_counter)

    logger.critical("second")
    logger.critical(redis_db.get("second"))


if __name__ == "__main__":
    app.run()
