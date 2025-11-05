with open("index_value.mem", "w") as f:
    for i in range(0x10000):
        f.write(f"{i % 256:08b}\n")  # 8-bit binary string per line

