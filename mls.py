import numpy as np

def mls(n, flag=0):
    # Define the taps based on the value of n
    taps_dict = {
        2: [1, 2],
        3: [1, 3],
        4: [1, 4],
        5: [2, 5],
        6: [1, 6],
        7: [1, 7],
        8: [2, 3, 4, 8],
        9: [4, 9],
        10: [3, 10],
        11: [2, 11],
        12: [1, 4, 6, 12],
        13: [1, 3, 4, 13],
        14: [1, 3, 5, 14],
        15: [1, 15],
        16: [2, 3, 5, 16],
        17: [3, 17],
        18: [7, 18],
        19: [1, 2, 5, 19],
        20: [3, 20],
        21: [2, 21],
        22: [1, 22],
        23: [5, 23],
        24: [1, 3, 4, 24],
    }

    if n not in taps_dict:
        print('Input bits must be between 2 and 24')
        return

    taps = taps_dict[n]
    num_taps = len(taps)

    if flag == 1:
        abuff = np.ones(n, dtype=int)
    else:
        np.random.seed(int(sum(np.random.rand(100) * 100)))  # Seed for reproducibility
        while True:
            abuff = np.random.randint(0, 2, n)  # Random bits
            if np.any(abuff == 1):
                break

    # Length of the output sequence
    y_length = (2**n) - 1
    y = np.zeros(y_length)

    for i in range(y_length - 1, -1, -1):
        xorbit = abuff[taps[0] - 1] ^ abuff[taps[1] - 1]  # Feedback bit

        if num_taps == 4:
            xorbit2 = abuff[taps[2] - 1] ^ abuff[taps[3] - 1]  # Second level
            xorbit = xorbit ^ xorbit2

        abuff = np.concatenate(([xorbit], abuff[:-1]))
        y[i] = (-2 * xorbit) + 1  # Converts to -1 and 1

    return y
