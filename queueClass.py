import functions


class Queue:
    def __init__(self, queue_length=0):
        self.queue_length = queue_length

    def add_to_queue(self, name):
        self.queue_length += 1
        log(f"{name} added to queue.'")

    def remove_from_queue(self):
        self.queue_length -= 1
        log("Queue decreased")

    def display_queue_length(self):
        return self.queue_length
