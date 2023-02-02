import pika
import logging
import sys
import json
import redis
import sqlite3

import configparser


cfg = configparser.ConfigParser()

cfg.read("./config_file.ini")

RABBITMQ_HOST = cfg.get("hosts", "rabbitmq", fallback="172.17.0.3")
REDIS_HOST = cfg.get("hosts", "redis", fallback="172.17.0.4")
SQLITE_PATH = cfg.get("hosts", "db")

LOG_PATH = "./logs"
FILE_NAME = "persistance"

redis_client = redis.Redis(host=REDIS_HOST)

database = sqlite3.connect(SQLITE_PATH)

def setup_logger():
    log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    root_logger = logging.getLogger()

    file_handler = logging.FileHandler("{0}/{1}.log".format(LOG_PATH, FILE_NAME))
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    return root_logger


_LOGGER_ = setup_logger()


def parse_message_input(message):
    decoded_data = message.decode('utf-8')
    input_json = json.loads(decoded_data)
    return input_json['identifier'], \
           input_json['total_number'], \
           input_json['total_positives'], \
           input_json['positive_ratio'], \
           input_json['target'], \
           input_json['subreddits']


def get_cache_identifier(target, subreddits):
    identifier = "{};{}".format(target, subreddits)
    return identifier


def callback_persist(channel, method, properties, body):
    try:
        request_identifier, total_number, total_positives, positive_ratio, target, subreddits = parse_message_input(body)
        _LOGGER_.info("Got request with id: {}".format(request_identifier))
        _LOGGER_.info("[req: {}] Data: total_number={} total_positives={} ratio={} target={} subreddits{}".format(request_identifier, total_number, total_positives, positive_ratio, target, subreddits))

        _LOGGER_.info("[req: {}] Setting data in cache".format(request_identifier))
        cache_identifier = get_cache_identifier(target, subreddits)
        redis_client.set(cache_identifier, positive_ratio, 60 * 10)
        _LOGGER_.info("[req: {}] Successfully set data in cache".format(request_identifier))

        _LOGGER_.info("[req: {}] Updating data in database".format(request_identifier))
        cursor_object = database.cursor()
        query = "UPDATE trust_search SET processed = ?, trust_percentage = ? WHERE trust_search.search_id = ?"
        positive_ratio = float(positive_ratio)
        values = (True, positive_ratio, request_identifier)

        cursor_object.execute(query, values)
        database.commit()
        _LOGGER_.info("[req: {}] Successfully updated data in database".format(request_identifier))
    except Exception as exc:
        _LOGGER_.exception("An unknown error has occurred.")


connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
channel = connection.channel()
channel.queue_declare(queue="flow_persist")
channel.basic_consume(queue="flow_persist",
                      auto_ack=True,
                      on_message_callback=callback_persist)
channel.start_consuming()
