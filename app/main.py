# mosquitto_pub -h localhost -t "hermes/intent" -m '{"intent": {"name": "SetTimer"}, "slots": {"minutes": 1, "seconds": 3}, "siteId": 5}'
import json
import paho.mqtt.client as mqtt
import time
import config
from models import Event
from base import init_db, session
import threading
from datetime import datetime, timedelta
import base_event
from base_event import SetNotificationEvent, SetTimerEvent
from sqlalchemy import select


stop_event_checker = threading.Event()

events = []

# Read the WAV file
wav_file = "./audio_samples/timeout.wav"
with open(wav_file, "rb") as f:
    wav_bytes = f.read()


def on_connect(client, userdata, flags, rc):

    client.subscribe(config.RECOGNIZED_INTENT_PATH)
    client.subscribe(config.UNRECOGNIZED_INTENT_PATH)


def on_disconnect(client, userdata, flags, rc):

    client.reconnect()


def get_unfinished_events():

    stmt = select(Event).where(Event.status == 0)
    unfinished_events = session.execute(stmt).scalars().all()

    for event in unfinished_events:

        if datetime.now() < event.timestamp:

            new_event = getattr(base_event, event.intent)(
                **event.to_dict(),
                session=session,
            )

            events.append(new_event)

        else:
            event.status = 1
            session.commit()


def set_time_handler(nlu_payload, client):

    slots = nlu_payload.get("slots", [])

    hours = 0
    minutes = 0
    seconds = 0

    for slot in slots:
        value = int(slot["value"]["value"])
        if slot["slotName"] == "hour":
            hours = value
        elif slot["slotName"] == "minute":
            minutes = value
        elif slot["slotName"] == "second":
            seconds = value

    event_timestamp = datetime.now() + timedelta(
        hours=hours, minutes=minutes, seconds=seconds
    )

    timer = SetTimerEvent(timestamp=event_timestamp, session=session)
    events.append(timer)
    client.publish("hermes/tts/say", json.dumps({"text": "Поставила таймер"}))


def get_time_handler(client):

    datetime_now = datetime.now()

    hours = datetime_now.hour
    minutes = datetime_now.minute

    print(f"Текущее время {hours} часов, {minutes} минут")
    client.publish(
        "hermes/tts/say",
        json.dumps({"text": f"Текущее время {hours} часов, {minutes} минут"}),
    )


def set_notification_handler(nlu_payload, client):

    text = nlu_payload["rawInput"]
    notification_text = text.split("о том")[1]

    slots = nlu_payload.get("slots", [])

    hours = 0
    minutes = 0
    seconds = 0

    for slot in slots:
        value = (
            int(slot["value"]["value"])
            if slot["slotName"] in ["hour", "minute", "second"]
            else None
        )
        if slot["slotName"] == "hour":
            hours = value
        elif slot["slotName"] == "minute":
            minutes = value
        elif slot["slotName"] == "second":
            seconds = value

    event_timestamp = datetime.now() + timedelta(
        hours=hours, minutes=minutes, seconds=seconds
    )

    notifier = SetNotificationEvent(
        timestamp=event_timestamp,
        notification_text=notification_text,
        session=session,
    )

    events.append(notifier)

    client.publish("hermes/tts/say", json.dumps({"text": "Поставила напоминание"}))


def on_message(client, userdata, msg):

    nlu_payload = json.loads(msg.payload)
    # print(json.dumps(nlu_payload, indent=4, ensure_ascii=False))

    if msg.topic == config.UNRECOGNIZED_INTENT_PATH:

        sentence = "Не поняла"
        print("Recognition failure")
        client.publish("hermes/tts/say", json.dumps({"text": sentence}))

    else:

        intent_name = nlu_payload["intent"]["intentName"]

        if intent_name == "SetTimer":
            set_time_handler(nlu_payload, client)
        elif intent_name == "GetTime":
            get_time_handler(client)
        elif intent_name == "SetNotification":
            set_notification_handler(nlu_payload, client)


def event_checker(client):
    while not stop_event_checker.is_set():
        now = datetime.now()
        for event in events:
            if now >= event.timestamp:

                topic = f"hermes/audioServer/default/playBytes/12345"
                client.publish(topic, wav_bytes)
                events.remove(event)

                response = event.finish_event(session=session)
                client.publish("hermes/tts/say", json.dumps({"text": response}))

                print(f"Event triggered: {response}")
        time.sleep(0.2)


if __name__ == "__main__":

    init_db()
    get_unfinished_events()
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    client.connect("localhost", 1883)

    event_checker_thread = threading.Thread(target=event_checker, args=(client,))
    event_checker_thread.daemon = True
    event_checker_thread.start()

    client.loop_forever()
