import redis

def check_redis(host="127.0.0.1", port=6379):
    try:
        r = redis.Redis(host=host, port=port, socket_connect_timeout=2)
        if r.ping():
            print("✅ Redis is accessible")
            return True
    except Exception as e:
        print("❌ Redis not accessible:", e)
        return False

if __name__ == "__main__":
    check_redis()