total = 0.0
for i in range(3):
    print(f"Iteration {i}")
    print((-1) ** i)
    print((2 * i + 1))

    term = (-1) ** i / (2 * i + 1)
    print(f"Term : {term}")
    print("###")
    total += term
# final_result = total * 4
# print(final_result)