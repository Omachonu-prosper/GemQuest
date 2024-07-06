from datetime import datetime, timedelta

def close_expired_waitrooms():
    from app.routes.rooms import rooms
    for room, info in rooms.items():
        current_time = datetime.now()
        elapsed_time = current_time - info['create_time']
        elapsed_time_in_mins = elapsed_time.seconds / 60
        if elapsed_time_in_mins > 2:
            print(room, 'expired')
        else:
            print(room, 'not expired')