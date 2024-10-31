def handle(event, context):
    if event.method == "POST":
        return handle_post(event, context)
    else:
        return handle_get(event, context)

def handle_post(event, context):
    return {
        "statusCode": 200,
        "body": "post handler"
    }


def handle_get(event, context):
    return {
        "statusCode": 200,
        "body": "get handler"
    }