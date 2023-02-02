import praw
import requests
import pika
import logging
import sys
import json
import redis



import configparser
cfg = configparser.ConfigParser()
try:
    cfg.read("./config_file.ini")
except:
cfg.read("/host_volume/config_file.ini")


clid = cfg.get("reddit", "clid")
clsec = cfg.get("reddit", "clsec")
useragent = cfg.get("reddit", "useragent")


CLASSIFIER_HOST = cfg.get("hosts", "classifier", fallback="http://172.17.0.5:80/predict")
RABBITMQ_HOST = cfg.get("hosts", "rabbitmq", fallback="172.17.0.2")
REDIS_HOST = cfg.get("hosts", "redis", fallback="172.17.0.3")

LOG_PATH = "./logs"
FILE_NAME = "analyzer"

redis_client = redis.Redis(host=REDIS_HOST)

def setup_logger():
    log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    logging.basicConfig(level=logging.INFO)
    root_logger = logging.getLogger()

    file_handler = logging.FileHandler("{0}/{1}.log".format(LOG_PATH, FILE_NAME))
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    return root_logger


_LOGGER_ = setup_logger()


def classify_comments(comments):
    response = requests.post(CLASSIFIER_HOST, json={"data": comments})
    if not response.status_code == 200:
        _LOGGER_.error("Classification server has encountered an error.")
    json_response = response.json()
    if json_response['success'] == "false":
        _LOGGER_.error("Classification server has encountered an error.")
    return json_response['predictions']


def parse_message_input(message):
    decoded_data = message.decode('utf-8')
    input_json = json.loads(decoded_data)
    return input_json['request_identifier'], input_json['subreddits'], input_json['target']



def compute_search_ratio(request_identifier, subreddit_object, subreddits, target_term):
    _LOGGER_.info("[req: {}] Getting top posts for last month".format(request_identifier))
    posts = subreddit_object.top(time_filter="day")

    _LOGGER_.info("[req: {}] Got top posts for last month".format(request_identifier))
    target_mentioned_comments = []

    for post in posts:
        _LOGGER_.info("[req: {}] Processing post:{}".format(request_identifier, post.id))
        comments_forest = post.comments
        all_comments = comments_forest.list()

        for comment in all_comments:
            #_LOGGER_.info("[req: {}] Processing comment: {}".format(request_identifier, comment.id))

            if isinstance(comment, praw.models.reddit.more.MoreComments):
                continue
            comment_body = comment.body

            if target_term not in comment_body:
                continue

            target_mentioned_comments.append(comment_body[:500])

    sent_comments = len(target_mentioned_comments)
    _LOGGER_.info(
        "[req: {}] Got comments for last month. Number:{}".format(request_identifier, sent_comments))

    if sent_comments == 0:
        return create_search_result(request_identifier, subreddits, target_term)

    classified_comments = classify_comments(target_mentioned_comments)
    _LOGGER_.info("[req: {}] Got classified comments for last month".format(request_identifier))

    positive_comments = 0
    for sentiment in classified_comments:
        if sentiment == "positive":
            positive_comments += 1
    _LOGGER_.info("[req: {}] Counted positive comments in last month. Positives: {}".format(request_identifier, positive_comments))

    ratio = compute_ratio(sent_comments, positive_comments)
    return create_search_result(request_identifier, subreddits, target_term, sent_comments, positive_comments, ratio)


def create_search_result(request_identifier, subreddits, target, total=0, total_positives=0, ratio=0):
    response = {
        "identifier": request_identifier,
        "total_number": total,
        "total_positives": total_positives,
        "positive_ratio": ratio,
        "subreddits": subreddits,
        "target": target
    }
    return response


def recompute_using_cache(request_identifier, subreddit_object, subreddits, target_term):
    # recompute only using the delta between last query and current time
    # not really possible because of the Reddit API
    pass


def get_cache_identifier(subreddits, target):
    subreddits = subreddits.split("+")
    subreddits = sorted(subreddits)
    subreddits = "+".join(subreddits)
    return "{};{}".format(target,subreddits)


def is_search_in_cache(subreddits, target):
    identifier = get_cache_identifier(subreddits, target)
    cache_result = redis_client.get(identifier)

    return False, None


def compute_ratio(total, positives):
    if total == 0:
        return 0
    positive_ratio = (positives / total) * 100
    return positive_ratio


def send_message_in_queue(queue, body, host=RABBITMQ_HOST):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
    channel = connection.channel()
    channel.queue_declare(queue='flow_persist')
    channel.basic_publish(exchange='',
                          routing_key='flow_persist',
                          body=json.dumps(body),
                          properties=pika.BasicProperties(delivery_mode=2))
    connection.close()


def callback_scrape(channel, method, properties, body):
    try:
        request_identifier, subreddits, target_term = parse_message_input(body)
        _LOGGER_.info("[req: {}] Got input data:{} - {}".format(request_identifier, subreddits, target_term))

        reddit_read_only = praw.Reddit(client_id=clid,
                                       client_secret=clsec,
                                       user_agent=useragent)

        subreddit_object = reddit_read_only.subreddit(subreddits)
        _LOGGER_.info("[req: {}] Got subreddits: {}.".format(request_identifier, subreddits))

        is_cached, cache_object = is_search_in_cache(subreddits, target_term)

        if is_cached:
            search_result = recompute_using_cache(request_identifier, subreddit_object, subreddits, target_term)
        else:
            search_result = compute_search_ratio(request_identifier, subreddit_object, subreddits, target_term)

        send_message_in_queue("flow_persist", search_result)
        _LOGGER_.info("[req: {}] Sent search to persistance queue. {}".format(request_identifier, search_result))
    except Exception as exc:
        _LOGGER_.exception("An unknown error has occurred.")


connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST, heartbeat=0))
channel = connection.channel()
channel.queue_declare(queue="flow_request")
channel.basic_consume(queue="flow_request",
                      auto_ack=True,
                      on_message_callback=callback_scrape)
channel.start_consuming()
