import time


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(
            f"Function '{func.__name__}' took {execution_time:.6f} seconds to execute."
        )
        return result

    return wrapper
