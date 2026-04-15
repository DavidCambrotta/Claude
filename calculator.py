def add(a: int, b: int = 0) -> int:
    return a + b


if __name__ == "__main__":
    raw = input("Enter up to 2 integers separated by space: ").split()
    if len(raw) > 2:
        print("Error: maximum 2 inputs allowed.")
    else:
        nums = [int(x) for x in raw]
        result = add(*nums)
        print(f"Result: {result}")
