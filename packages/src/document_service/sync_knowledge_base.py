import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0)

# Push task
r.lpush("task_queue", json.dumps({"task": "process_doc", "id": 1}))

# Worker
task = r.rpop("task_queue")

def push_to_queue(task_data):
    r.lpush("task_queue", json.dumps(task_data))
    
def update_knowledge_base(task_data):
    while 