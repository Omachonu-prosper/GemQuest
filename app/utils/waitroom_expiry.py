from datetime import datetime

def close_expired_waitrooms():
    from app.routes.rooms import waitingroom_manager
    for room, info in waitingroom_manager.rooms.items():
        current_time = datetime.now()
        elapsed_time = current_time - info['create_time']
        elapsed_time_in_mins = elapsed_time.seconds / 60
        if elapsed_time_in_mins > 5:
            print(room, 'expired')
        else:
            print(room, 'not expired')